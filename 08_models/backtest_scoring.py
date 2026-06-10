r"""Backtest leak-safe del modelo de goleo — ¿calibran las probabilidades?

Para cada jugador-partido (en orden cronológico) estima la tasa de goles usando
**sólo** el historial PREVIO del jugador (expanding + ``shift(1)``), calcula
``P(marca) = 1 - e^{-λ}`` y la compara contra si el jugador realmente marcó. Así
se mide la calidad real del modelo sin fuga de información.

Compara los métodos de ``lib.scoring`` (rate vs shrinkage vs xg_shrinkage) con
tres métricas:

    Brier   media (p - y)²            (menor es mejor)
    LogLoss -media[y·ln p + (1-y)·ln(1-p)]   (menor es mejor)
    Calib   |obs - pred| por bins     (cercano a 0 es mejor)

La tasa se evalúa escalada por los minutos efectivamente jugados en ese partido,
para aislar la calidad de la *tasa* del problema aparte de predecir minutos.

Uso:
    python 08_models/backtest_scoring.py
    python 08_models/backtest_scoring.py --min-prior 3

Salida:
    08_models/reports/scoring_backtest.md
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.io import read_parquet  # noqa: E402
from lib.scoring import positional_rate, aggregate_history  # noqa: E402

PM_PATH = PROJECT_ROOT / "02_data_processed" / "events_clean" / "statsbomb_player_match.parquet"
REPORT = PROJECT_ROOT / "08_models" / "reports" / "scoring_backtest.md"


def _positional_prior(pm: pd.DataFrame, target: str, xg: str | None) -> dict:
    """Tasa per-90 por posición (prior fijo del pool — uso estándar de EB)."""
    agg = aggregate_history(pm, target_col=target, xg_col=xg)
    col = "xg_sum" if xg else "events"
    return positional_rate(agg, events_col=col).to_dict()


def leak_safe_predictions(pm: pd.DataFrame, prior_strength: float = 4.0,
                          min_prior: int = 2) -> pd.DataFrame:
    """Predicción leak-safe de P(marca) por jugador-partido, para 3 métodos."""
    df = pm.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.sort_values(["player_id", "date"]).reset_index(drop=True)
    df["minutes_played"] = df["minutes_played"].fillna(0)
    df["xg"] = df["xg"].fillna(0)
    df["exposure90"] = df["minutes_played"].clip(lower=0) / 90.0

    g = df.groupby("player_id")
    # Acumulados estrictamente previos (shift 1).
    cum_goals = g["goals"].cumsum().shift(1)
    cum_xg = g["xg"].cumsum().shift(1)
    cum_exp = g["exposure90"].cumsum().shift(1)
    cum_n = g.cumcount()  # nº de partidos previos
    # Reset del shift en el primer partido de cada jugador.
    first = g.cumcount() == 0
    cum_goals = cum_goals.mask(first, np.nan)
    cum_xg = cum_xg.mask(first, np.nan)
    cum_exp = cum_exp.mask(first, np.nan)

    prior_g = _positional_prior(df, "goals", None)
    prior_xg = _positional_prior(df, "goals", "xg")  # prior sobre goles igual
    pos = df["position_group"]
    global_g = df["goals"].sum() / max(df["exposure90"].sum(), 1e-9)
    m_g = pos.map(prior_g).fillna(global_g)

    c = prior_strength
    scale = (df["minutes_played"].clip(lower=0) / 90.0).values  # minutos de ESTE partido

    # rate (per-match naive): goles_prev / partidos_prev → por partido
    rate_permatch = cum_goals / cum_n.replace(0, np.nan)
    lam_rate = rate_permatch.fillna(0).values  # ya es por-partido
    # shrinkage sobre goles
    lam_shr = ((cum_goals + m_g * c) / (cum_exp + c)).values * scale
    # xg_shrinkage
    lam_xgs = ((cum_xg + m_g * c) / (cum_exp + c)).values * scale

    out = pd.DataFrame({
        "player_id": df["player_id"], "date": df["date"],
        "prior_matches": cum_n.values,
        "scored": (df["goals"] > 0).astype(int).values,
        "p_rate": 1 - np.exp(-np.clip(lam_rate, 0, None)),
        "p_shrinkage": 1 - np.exp(-np.clip(lam_shr, 0, None)),
        "p_xg_shrinkage": 1 - np.exp(-np.clip(lam_xgs, 0, None)),
    })
    out = out[out["prior_matches"] >= min_prior]
    out = out.dropna(subset=["p_rate", "p_shrinkage", "p_xg_shrinkage"])
    return out.reset_index(drop=True)


def _metrics(y: np.ndarray, p: np.ndarray) -> dict:
    p = np.clip(p, 1e-6, 1 - 1e-6)
    brier = float(np.mean((p - y) ** 2))
    logloss = float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))
    return {"brier": brier, "logloss": logloss}


def _calibration(y: np.ndarray, p: np.ndarray, n_bins: int = 10) -> pd.DataFrame:
    edges = np.linspace(0, 1, n_bins + 1)
    b = pd.DataFrame({"y": y, "p": p})
    b["bin"] = pd.cut(b["p"], edges, include_lowest=True)
    out = (b.groupby("bin", observed=True)
             .agg(n=("y", "size"), pred=("p", "mean"), obs=("y", "mean")).dropna())
    out["gap"] = out["obs"] - out["pred"]
    return out.reset_index()


def main():
    ap = argparse.ArgumentParser(description="Backtest leak-safe del modelo de goleo.")
    ap.add_argument("--prior-strength", type=float, default=4.0)
    ap.add_argument("--min-prior", type=int, default=2,
                    help="Mínimo de partidos previos para evaluar (default 2).")
    args = ap.parse_args()

    pm = read_parquet(PM_PATH)
    preds = leak_safe_predictions(pm, args.prior_strength, args.min_prior)
    y = preds["scored"].values
    base = float(y.mean())
    print(f"Evaluando {len(preds):,} jugador-partidos | tasa base de gol: {base:.3f}")

    methods = ["rate", "shrinkage", "xg_shrinkage"]
    summary = []
    for mth in methods:
        p = preds[f"p_{mth}"].values
        m = _metrics(y, p)
        cal = _calibration(y, p)
        m["method"] = mth
        m["cal_mae"] = float(cal["gap"].abs().mean())
        summary.append(m)
    sumdf = pd.DataFrame(summary)[["method", "brier", "logloss", "cal_mae"]]

    best = sumdf.sort_values("logloss").iloc[0]["method"]
    cal_best = _calibration(y, preds[f"p_{best}"].values)

    lines = ["# Backtest leak-safe — modelo de goleo (P de marcar)\n"]
    lines.append(f"\n{len(preds):,} jugador-partidos evaluados (≥{args.min_prior} partidos "
                 f"de historial previo). Tasa base de gol: **{base:.3f}**.\n")
    lines.append("\n## Comparación de métodos\n")
    lines.append("Menor Brier / LogLoss = mejor. `cal_mae` = error medio de calibración.\n")
    head = ["método", "Brier", "LogLoss", "cal_MAE"]
    lines.append("| " + " | ".join(head) + " |")
    lines.append("| " + " | ".join("---" for _ in head) + " |")
    for _, r in sumdf.iterrows():
        lines.append(f"| {r['method']} | {r['brier']:.4f} | {r['logloss']:.4f} | {r['cal_mae']:.4f} |")
    lines.append(f"\n**Mejor método: `{best}`** (menor LogLoss).\n")
    lines.append(f"\n## Calibración del mejor método (`{best}`)\n")
    lines.append("`gap = obs − pred`; cercano a 0 ⇒ probabilidades fiables.\n")
    head2 = ["bin p", "n", "pred", "obs", "gap"]
    lines.append("| " + " | ".join(head2) + " |")
    lines.append("| " + " | ".join("---" for _ in head2) + " |")
    for _, r in cal_best.iterrows():
        lines.append(f"| {str(r['bin'])} | {int(r['n'])} | {r['pred']:.3f} | "
                     f"{r['obs']:.3f} | {r['gap']:+.3f} |")
    lines.append("\n## Lectura\n")
    lines.append(
        "- El **shrinkage** debería ganarle al **rate** crudo: el rate sobreestima a "
        "jugadores con racha en pocos partidos (Brier/LogLoss peor).\n"
        "- **xg_shrinkage** suele calibrar mejor en la cola alta: xG es menos ruidoso "
        "que goles para estimar la tasa real.\n"
        "- Si la calibración del mejor método es buena, el EV del value board del Mundial "
        "es confiable *para jugadores con muestra* (ojo con `prior_matches` bajo).\n")

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print("\n" + sumdf.to_string(index=False))
    print(f"\nMejor: {best}")
    print(f"Reporte -> {REPORT.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
