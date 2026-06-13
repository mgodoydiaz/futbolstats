r"""Pronóstico completo de un partido contra las cuotas de Betano.

Toma el JSON de Betano (extraído del navegador) y, con el historial StatsBomb,
modela y calcula EV para todos los mercados que podemos cubrir:

    1X2 · total goles O/U · ambos anotan · goles por equipo · marcador correcto
    corners O/U · tarjetas O/U · tiros al arco por jugador · goleador

Une el modelo de equipo (``lib.match_model``, Poisson) con los modelos de jugador
(``lib.scoring``, shrinkage) y el parser de cuotas (``lib.odds_betano``).

Uso:
    python 08_models/predict_match.py --odds 01_data_raw/odds/betano_catar_suiza_2026-06-13.json
    python 08_models/predict_match.py --odds <json> --team-a Qatar --team-b Switzerland
    python 08_models/predict_match.py --odds <json> --ev-min 0.05

Salida:
    10_serving/matches/<slug>_pred.md   (tabla de EV)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib import match_model as MM  # noqa: E402
from lib import odds_betano as OB  # noqa: E402
from lib.betting import expected_value, implied_prob, negbin_over_under, poisson_over_under  # noqa: E402
from lib.betting import dispersion_from_moments  # noqa: E402
from lib.io import read_parquet  # noqa: E402
from lib.scoring import estimate_rate, prob_at_least_one  # noqa: E402
from lib.text import normalize_name  # noqa: E402

PM = PROJECT_ROOT / "02_data_processed" / "events_clean" / "statsbomb_player_match.parquet"
DISC = PROJECT_ROOT / "02_data_processed" / "events_clean" / "statsbomb_player_match_discipline.parquet"
SP = PROJECT_ROOT / "02_data_processed" / "events_clean" / "statsbomb_team_match_setpieces.parquet"
OUT_DIR = PROJECT_ROOT / "10_serving" / "matches"

# Betano (español) → nombre StatsBomb (inglés). Ampliable.
TEAM_ALIASES = {
    "catar": "Qatar", "qatar": "Qatar",
    "suiza": "Switzerland", "switzerland": "Switzerland",
    "corea del sur": "South Korea", "chequia": "Czech Republic",
}


def map_team(name: str) -> str:
    return TEAM_ALIASES.get(name.strip().lower(), name.strip())


def fuzzy_player_index(player_match: pd.DataFrame) -> dict:
    """Índice de nombres para matchear nombres cortos de Betano con los completos.

    Devuelve dict con dos vistas: exacto-normalizado y por conjunto de tokens.
    """
    names = player_match["player_name"].dropna().unique()
    exact = {normalize_name(n): n for n in names}
    tokens = {n: set(normalize_name(n).split()) for n in names}
    return {"exact": exact, "tokens": tokens}


def match_player(betano_name: str, idx: dict) -> str | None:
    """Matchea 'Breel Embolo' con 'Breel-Donald Embolo' por subconjunto de tokens."""
    nb = normalize_name(betano_name)
    if nb in idx["exact"]:
        return idx["exact"][nb]
    bt = set(nb.split())
    best, best_score = None, 0
    for full, toks in idx["tokens"].items():
        inter = bt & toks
        if not inter:
            continue
        # exige que el apellido (último token de Betano) esté presente
        if nb.split()[-1] not in toks:
            continue
        score = len(inter)
        if score > best_score:
            best, best_score = full, score
    return best


def _row(market, sel, p, odds):
    if odds is None or odds <= 1.0:
        return None
    return {"mercado": market, "selección": sel, "p_model": round(p, 4),
            "cuota": odds, "p_impl": round(implied_prob(odds), 4),
            "EV": round(expected_value(p, odds), 4)}


def predict(odds_path: Path, team_a_override=None, team_b_override=None):
    data = OB.load(odds_path)
    ba, bb = OB.teams_from_meta(data)
    team_a = team_a_override or map_team(ba)
    team_b = team_b_override or map_team(bb)
    M = data["mercados"]

    pm = read_parquet(PM)
    disc = read_parquet(DISC)
    sp = read_parquet(SP)

    for t in (team_a, team_b):
        if t not in set(pm["team_name"]):
            print(f"[warn] '{t}' no está en los datos StatsBomb — predicciones de "
                  f"equipo serán None.")

    rows: list[dict] = []
    notes: list[str] = []

    # ---- modelo de equipo: goles esperados → matriz ----
    have_both = team_a in set(pm["team_name"]) and team_b in set(pm["team_name"])
    lam_a = lam_b = None
    if have_both:
        strengths = MM.team_strengths(pm)
        lam_a, lam_b = MM.expected_goals(strengths, team_a, team_b)
        mat = MM.scoreline_matrix(lam_a, lam_b)
        mk = MM.markets_from_matrix(mat)
        notes.append(f"Goles esperados: {team_a} {lam_a:.2f} — {team_b} {lam_b:.2f}")

        # 1X2
        if "resultado_partido" in M:
            o = OB.one_x_two(M["resultado_partido"])
            for side, p in [("home", mk["home"]), ("draw", mk["draw"]), ("away", mk["away"])]:
                r = _row("1X2", side, p, o.get(side))
                if r:
                    rows.append(r)
        # total goles
        if "goles_totales_mas_menos" in M:
            ou = OB.over_under(M["goles_totales_mas_menos"])
            for line, sides in ou.items():
                if line in mk["totals"]:
                    for s in ("over", "under"):
                        r = _row("Total goles", f"{s} {line}", mk["totals"][line][s], sides.get(s))
                        if r:
                            rows.append(r)
        # BTTS
        if "ambos_equipos_anotan" in M:
            yn = OB.yes_no(M["ambos_equipos_anotan"])
            rows += [r for r in [
                _row("Ambos anotan", "sí", mk["btts_yes"], yn.get("yes")),
                _row("Ambos anotan", "no", mk["btts_no"], yn.get("no"))] if r]
        # goles por equipo
        for key, lam, tname in [("catar_goles_mas_menos", lam_a, team_a),
                                ("suiza_goles_mas_menos", lam_b, team_b)]:
            if key in M:
                ou = OB.over_under(M[key])
                for line, sides in ou.items():
                    tt = MM.team_total_goals(lam, line)
                    for s in ("over", "under"):
                        r = _row(f"Goles {tname}", f"{s} {line}", tt[s], sides.get(s))
                        if r:
                            rows.append(r)
        # marcador correcto
        if "marcador_correcto" in M:
            for (a, b), odds in OB.correct_scores(M["marcador_correcto"]).items():
                r = _row("Marcador", f"{a}-{b}", MM.correct_score(mat, a, b), odds)
                if r:
                    rows.append(r)

    # ---- corners ----
    if "corners_mas_menos" in M:
        a_c, b_c, tot_c = MM.expected_corners(sp, team_a, team_b)
        if tot_c == tot_c:  # not NaN
            notes.append(f"Corners esperados: total {tot_c:.2f}")
            alpha = 0.05
            ou = OB.over_under(M["corners_mas_menos"])
            for line, sides in ou.items():
                pp = negbin_over_under(tot_c, alpha, line)
                rows += [r for r in [
                    _row("Corners", f"over {line}", pp.p_over, sides.get("over")),
                    _row("Corners", f"under {line}", pp.p_under, sides.get("under"))] if r]
        else:
            notes.append("Corners: sin datos de set-pieces para algún equipo.")

    # ---- tarjetas ----
    if "tarjetas_totales_mas_menos" in M:
        a_k, b_k, tot_k = MM.expected_cards(pm, disc, team_a, team_b)
        if tot_k > 0:
            notes.append(f"Tarjetas esperadas: total {tot_k:.2f} (sólo amarillas en datos)")
            ou = OB.over_under(M["tarjetas_totales_mas_menos"])
            for line, sides in ou.items():
                pp = poisson_over_under(tot_k, line)
                rows += [r for r in [
                    _row("Tarjetas", f"over {line}", pp.p_over, sides.get("over")),
                    _row("Tarjetas", f"under {line}", pp.p_under, sides.get("under"))] if r]

    # ---- props de jugador ----
    idx = fuzzy_player_index(pm)
    unmatched = []

    def player_lambda(target, xg):
        rates = estimate_rate(pm, target_col=target, method="shrinkage",
                              xg_col=xg, prior_strength=4.0, min_matches=1)
        em = pm.groupby("player_id")["minutes_played"].mean().clip(30, 90)
        rates = rates.merge(em.rename("em"), on="player_id", how="left")
        rates["lam"] = rates["lam_per90"] * (rates["em"].fillna(90) / 90)
        return rates.set_index("player_name")["lam"]

    lam_sot = player_lambda("shots_on_target", None)
    lam_goals_rate = estimate_rate(pm, "goals", "xg_shrinkage", xg_col="xg",
                                   prior_strength=4.0, min_matches=1)
    em = pm.groupby("player_id")["minutes_played"].mean().clip(30, 90)
    lam_goals_rate = lam_goals_rate.merge(em.rename("em"), on="player_id", how="left")
    lam_goals_rate["lam"] = lam_goals_rate["lam_per90"] * (lam_goals_rate["em"].fillna(90) / 90)
    lam_goals = lam_goals_rate.set_index("player_name")["lam"]

    # tiros al arco
    if "tiros_al_arco" in M:
        for bname, thr in OB.player_shots(M["tiros_al_arco"]).items():
            full = match_player(bname, idx)
            if full is None or full not in lam_sot.index:
                unmatched.append(bname)
                continue
            lam = float(lam_sot.loc[full])
            for k, odds in thr.items():
                p = float(1 - poisson_over_under(lam, k - 0.5).p_under)  # P(>=k)
                r = _row("Tiros al arco", f"{bname} {k}+", p, odds)
                if r:
                    rows.append(r)
    # goleador
    if "goleador" in M:
        for bname, cols in OB.player_goalscorer(M["goleador"]).items():
            full = match_player(bname, idx)
            if full is None or full not in lam_goals.index:
                if bname not in unmatched:
                    unmatched.append(bname)
                continue
            p = float(prob_at_least_one(lam_goals.loc[full]))
            r = _row("Goleador", f"{bname} anytime", p, cols.get("anytime"))
            if r:
                rows.append(r)

    df = pd.DataFrame(rows)
    return df, notes, unmatched, (team_a, team_b), (lam_a, lam_b)


def main():
    ap = argparse.ArgumentParser(description="Pronóstico de partido vs cuotas de Betano.")
    ap.add_argument("--odds", required=True, help="Ruta al JSON de Betano.")
    ap.add_argument("--team-a", default=None, help="Nombre StatsBomb del 1er equipo (override).")
    ap.add_argument("--team-b", default=None, help="Nombre StatsBomb del 2do equipo (override).")
    ap.add_argument("--ev-min", type=float, default=None, help="Filtrar a EV>ev-min.")
    args = ap.parse_args()

    df, notes, unmatched, (ta, tb), (la, lb) = predict(
        Path(args.odds), args.team_a, args.team_b)

    print(f"\n=== {ta} vs {tb} ===")
    for n in notes:
        print("  ·", n)
    if unmatched:
        print(f"  · jugadores sin match en datos: {unmatched}")
    if len(df) == 0:
        print("\nNo se pudo valuar ningún mercado (¿equipos sin datos?).")
        return

    show = df.copy()
    if args.ev_min is not None:
        show = show[show["EV"] > args.ev_min]
    show = show.sort_values("EV", ascending=False)
    print(f"\nMercados valuados: {len(df)} | con EV>0: {int((df['EV']>0).sum())}\n")
    print(show.head(25).to_string(index=False))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = f"{ta}_{tb}".lower().replace(" ", "_")
    out = OUT_DIR / f"{slug}_pred.md"
    lines = [f"# Pronóstico {ta} vs {tb}\n"]
    lines += [f"- {n}" for n in notes]
    lines.append(f"\n_{len(df)} mercados valuados, {int((df['EV']>0).sum())} con EV>0. "
                 f"Cuotas Betano. EV = p_model×cuota − 1._\n")
    lines.append("\n| mercado | selección | p_model | cuota | p_impl | EV |")
    lines.append("|---|---|--:|--:|--:|--:|")
    for _, r in df.sort_values("EV", ascending=False).iterrows():
        lines.append(f"| {r['mercado']} | {r['selección']} | {r['p_model']:.3f} | "
                     f"{r['cuota']:.2f} | {r['p_impl']:.3f} | {r['EV']:+.3f} |")
    if unmatched:
        lines.append(f"\n**Jugadores sin historial en datos:** {', '.join(unmatched)}")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n-> {out.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
