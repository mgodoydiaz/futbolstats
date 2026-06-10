r"""Value board del Mundial 2026 — cuotas reales de Pinnacle vs modelo.

Cruza las cuotas reales scrapeadas de Pinnacle (``01_data_raw/odds/``) con
predicciones de ``lib.scoring`` y produce una tabla de valor esperado para los
dos mercados que Pinnacle cotiza en fútbol:

    anytime_goalscorer  → modelo de GOLES   → P(marca ≥ 1)
    to_be_booked        → modelo de TARJETAS → P(amonestado ≥ 1)

El método del modelo es **seleccionable** (``--goal-method`` / ``--card-method``,
ver ``lib.scoring.METHODS``): el default ``shrinkage`` encoge la tasa cruda hacia
la media de la posición para no creerle a un delantero con 2 goles en 3 partidos.

Cobertura: sólo jugadores cotizados por Pinnacle QUE además tienen historial en
nuestros datos StatsBomb (≈ 239 al cierre del WC 2026). El resto no se puede
predecir y se omite.

Nota sobre el margen: el "anytime goalscorer" de Pinnacle es un precio de un solo
lado por jugador, así que no se puede des-vigar por jugador. Comparamos contra la
implícita cruda (``1/odds``), que ya incluye el margen — por lo que un EV positivo
es una señal *conservadora* (el margen juega en contra).

Uso:
    python 08_models/worldcup_value.py
    python 08_models/worldcup_value.py --goal-method xg_shrinkage --min-matches 5
    python 08_models/worldcup_value.py --ev-min 0.0 --top 40

Salida:
    10_serving/worldcup/value_board_<fecha>.parquet
    10_serving/worldcup/value_board_<fecha>.md

Aviso: análisis estadístico, no asesoría. Apostar arriesga pérdida total.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.betting import expected_value, implied_prob, kelly_fraction  # noqa: E402
from lib.io import read_parquet  # noqa: E402
from lib.scoring import estimate_rate, prob_at_least_one  # noqa: E402

PM_PATH = PROJECT_ROOT / "02_data_processed" / "events_clean" / "statsbomb_player_match.parquet"
DISC_PATH = PROJECT_ROOT / "02_data_processed" / "events_clean" / "statsbomb_player_match_discipline.parquet"
ODDS_DIR = PROJECT_ROOT / "01_data_raw" / "odds"
OUT_DIR = PROJECT_ROOT / "10_serving" / "worldcup"


def latest_odds() -> pd.DataFrame:
    files = sorted(ODDS_DIR.glob("pinnacle_soccer_*.parquet"))
    if not files:
        raise FileNotFoundError(
            "No hay snapshot de odds. Corré: python 06_ingestion/pinnacle_scraper.py")
    return read_parquet(files[-1])


def load_goals_history() -> pd.DataFrame:
    """Historial partido-a-partido con goles, xG, minutos, posición."""
    return read_parquet(PM_PATH)


def load_cards_history(pm: pd.DataFrame) -> pd.DataFrame:
    """Agrega yellow_total al historial vía ids numéricos (discipline usa id crudo)."""
    disc = read_parquet(DISC_PATH)[["player_id", "match_id", "yellow_total"]].copy()
    disc = disc.rename(columns={"player_id": "pid_num", "match_id": "mid_num"})
    df = pm.copy()
    df["pid_num"] = df["player_id_sb"].astype("float64")
    df["mid_num"] = df["match_id"].str.replace("sb_", "", regex=False).astype("float64")
    disc["pid_num"] = disc["pid_num"].astype("float64")
    disc["mid_num"] = disc["mid_num"].astype("float64")
    df = df.merge(disc, on=["pid_num", "mid_num"], how="left")
    df["yellow_total"] = df["yellow_total"].fillna(0)
    return df


def per_player_expected_minutes(history: pd.DataFrame, cap: float = 90.0,
                                floor: float = 30.0) -> pd.Series:
    """Minutos esperados = media histórica del jugador, acotada a [floor, cap]."""
    avg = history.groupby("player_id")["minutes_played"].mean().clip(floor, cap)
    return avg


def rates_with_minutes(history: pd.DataFrame, target_col: str, method: str,
                       xg_col: str | None, prior_strength: float,
                       min_matches: int) -> pd.DataFrame:
    """estimate_rate + ajuste por minutos esperados propios de cada jugador."""
    rates = estimate_rate(history, target_col=target_col, method=method,
                          xg_col=xg_col, prior_strength=prior_strength,
                          expected_minutes=90.0, min_matches=min_matches)
    exp_min = per_player_expected_minutes(history)
    rates = rates.merge(exp_min.rename("exp_min"), on="player_id", how="left")
    rates["exp_min"] = rates["exp_min"].fillna(90.0)
    rates["lam_match"] = rates["lam_per90"] * (rates["exp_min"] / 90.0)
    return rates


def build_value_board(goal_method: str, card_method: str, prior_strength: float,
                      min_matches: int, kelly_frac: float) -> pd.DataFrame:
    odds = latest_odds()
    pm = load_goals_history()
    cards_hist = load_cards_history(pm)

    goal_rates = rates_with_minutes(pm, "goals", goal_method, "xg",
                                    prior_strength, min_matches)
    card_rates = rates_with_minutes(cards_hist, "yellow_total", card_method, None,
                                    prior_strength, min_matches)
    goal_rates["p_model"] = prob_at_least_one(goal_rates["lam_match"])
    card_rates["p_model"] = prob_at_least_one(card_rates["lam_match"])

    keep = ["player_id", "matches", "lam_match", "exp_min", "p_model"]
    market_rates = {
        "anytime_goalscorer": goal_rates[keep],
        "to_be_booked": card_rates[keep],
    }

    rows = []
    for market, rates in market_rates.items():
        sub = odds[(odds["market"] == market) & odds["player_id"].notna()].copy()
        sub = sub.merge(rates, on="player_id", how="inner")
        if len(sub) == 0:
            continue
        sub["implied_prob"] = sub["odds"].apply(implied_prob)
        sub["edge"] = sub["p_model"] - sub["implied_prob"]
        sub["ev"] = [expected_value(p, o) for p, o in zip(sub["p_model"], sub["odds"])]
        sub["kelly"] = [kelly_fraction(p, o, kelly_frac)
                        for p, o in zip(sub["p_model"], sub["odds"])]
        rows.append(sub)

    if not rows:
        return pd.DataFrame()
    board = pd.concat(rows, ignore_index=True)
    cols = ["league", "home_team", "away_team", "start_time", "player_name",
            "market", "matches", "exp_min", "lam_match", "p_model",
            "odds", "implied_prob", "edge", "ev", "kelly"]
    cols = [c for c in cols if c in board.columns]
    return board[cols].sort_values("ev", ascending=False).reset_index(drop=True)


def write_report(board: pd.DataFrame, args, out_md: Path) -> None:
    n = len(board)
    pos = int((board["ev"] > 0).sum())
    lines = [
        "# 🏆 Value Board — Mundial 2026\n",
        f"Cuotas reales de **Pinnacle** vs modelo `{args.goal_method}` (goles) / "
        f"`{args.card_method}` (tarjetas). Generado {date.today().isoformat()}.\n",
        f"\n- Mercados cotizados con historial: **{n}**  ·  con EV>0: **{pos}**\n"
        f"- `min_matches`={args.min_matches}, `prior_strength`={args.prior_strength}, "
        f"quarter-Kelly={args.kelly_frac}\n",
        "\n> ⚠️ La implícita de Pinnacle incluye margen; un EV>0 ya es conservador. "
        "Pero pocos partidos por jugador en torneos = incertidumbre alta. "
        "Análisis estadístico, **no** asesoría. Apostar arriesga pérdida total.\n",
        f"\n## Top {args.top} por EV\n",
    ]
    head = ["Jugador", "Mercado", "Partido", "PJ", "λ", "p_model", "cuota", "p_impl", "EV", "Kelly"]
    lines.append("| " + " | ".join(head) + " |")
    lines.append("| " + " | ".join("---" for _ in head) + " |")
    for _, r in board.head(args.top).iterrows():
        match = f"{r.get('home_team','')[:12]}–{r.get('away_team','')[:12]}" \
            if "home_team" in board.columns else ""
        lines.append("| " + " | ".join([
            str(r.get("player_name", ""))[:24],
            str(r["market"]).replace("anytime_goalscorer", "gol").replace("to_be_booked", "tarjeta"),
            match,
            f"{int(r['matches'])}",
            f"{r['lam_match']:.2f}",
            f"{r['p_model']:.3f}",
            f"{r['odds']:.2f}",
            f"{r['implied_prob']:.3f}",
            f"{r['ev']:+.3f}",
            f"{r['kelly']:.3f}",
        ]) + " |")
    lines.append("\n\n## Cómo leer esto\n")
    lines.append(
        "- **λ**: goles (o tarjetas) esperados del jugador en el partido, ajustado por "
        "minutos y encogido hacia su posición.\n"
        "- **p_model**: P(marca ≥1) = 1−e^(−λ). **p_impl**: 1/cuota (con margen).\n"
        "- **EV**: `p_model × cuota − 1`. Positivo ⇒ el modelo ve más probable el evento "
        "que la cuota.\n"
        "- **Kelly**: fracción del bankroll sugerida (quarter-Kelly). 0 = no apostar.\n"
        "- EV altísimos (>0.5) suelen ser jugadores con poquísimos partidos: desconfiá, "
        "subí `--min-matches`.\n")
    out_md.write_text("".join(l if l.endswith("\n") else l + "\n" for l in lines),
                      encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description="Value board del Mundial 2026 (Pinnacle vs modelo).")
    p.add_argument("--goal-method", default="shrinkage",
                   help="Método para goles (rate|per90|shrinkage|xg_shrinkage).")
    p.add_argument("--card-method", default="shrinkage",
                   help="Método para tarjetas (rate|per90|shrinkage).")
    p.add_argument("--prior-strength", type=float, default=4.0,
                   help="Fuerza del encogimiento (métodos shrinkage).")
    p.add_argument("--min-matches", type=int, default=4,
                   help="Mínimo de partidos de historial para predecir (default 4).")
    p.add_argument("--kelly-frac", type=float, default=0.25, help="Fracción de Kelly.")
    p.add_argument("--ev-min", type=float, default=None,
                   help="Si se pasa, filtra el board a EV>ev-min.")
    p.add_argument("--top", type=int, default=30, help="Filas en el reporte markdown.")
    args = p.parse_args()

    board = build_value_board(args.goal_method, args.card_method,
                              args.prior_strength, args.min_matches, args.kelly_frac)
    if len(board) == 0:
        print("[wc] no hubo cruce entre odds y modelo. ¿Scrapeaste Pinnacle hoy?")
        return
    if args.ev_min is not None:
        board = board[board["ev"] > args.ev_min].reset_index(drop=True)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = date.today().isoformat()
    out_pq = OUT_DIR / f"value_board_{stamp}.parquet"
    out_md = OUT_DIR / f"value_board_{stamp}.md"
    board.to_parquet(out_pq, index=False)
    write_report(board, args, out_md)

    pos = int((board["ev"] > 0).sum())
    print(f"[wc] {len(board)} mercados cruzados ({pos} con EV>0)")
    print(f"[wc] goles={args.goal_method} tarjetas={args.card_method} "
          f"min_matches={args.min_matches}")
    print("\nTop 8 por EV:")
    show = board.head(8)[["player_name", "market", "matches", "p_model", "odds", "ev"]].copy()
    print(show.to_string(index=False))
    print(f"\n-> {out_md.relative_to(PROJECT_ROOT)}")
    print(f"-> {out_pq.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
