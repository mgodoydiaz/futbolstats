r"""Pronóstico completo de un partido contra las cuotas de Betano.

Toma el JSON de Betano (extraído del navegador) y, con el historial StatsBomb,
modela y calcula EV para todos los mercados que podemos cubrir:

    1X2 · total goles O/U · ambos anotan · goles por equipo · marcador correcto
    corners O/U · tarjetas O/U · tiros al arco por jugador · goleador

Une el modelo de equipo (``lib.match_model``, Poisson) con los modelos de jugador
(``lib.scoring``, shrinkage) y el parser de cuotas (``lib.odds_betano``).

**Blend con el mercado (paso 2).** El modelo sobre-estima a equipos con poca
muestra (un minnow con 3 partidos tira a la media). Para corregirlo, en los
mercados de varios resultados des-vigamos la cuota y mezclamos:

    p_blend = w · p_model + (1 - w) · p_market_devig ,   w = n_eff / (n_eff + K)

``n_eff`` = mínimo de partidos de los equipos implicados. Pocos datos ⇒ ``w``
chico ⇒ se confía en el mercado. El EV reportado usa ``p_blend``. Los props de
jugador (mercado de un solo lado) no se des-vigan: quedan model-only.

Uso:
    python 08_models/predict_match.py --odds 01_data_raw/odds/betano_catar_suiza_2026-06-13.json
    python 08_models/predict_match.py --odds <json> --team-a Qatar --team-b Switzerland --ev-min 0.05
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
from lib.betting import (  # noqa: E402
    expected_value, implied_prob, negbin_over_under, poisson_over_under, remove_vig,
)
from lib.io import read_parquet  # noqa: E402
from lib.scoring import estimate_rate, prob_at_least_one  # noqa: E402
from lib.text import normalize_name  # noqa: E402

PM = PROJECT_ROOT / "02_data_processed" / "events_clean" / "statsbomb_player_match.parquet"
DISC = PROJECT_ROOT / "02_data_processed" / "events_clean" / "statsbomb_player_match_discipline.parquet"
SP = PROJECT_ROOT / "02_data_processed" / "events_clean" / "statsbomb_team_match_setpieces.parquet"
OUT_DIR = PROJECT_ROOT / "10_serving" / "matches"

BLEND_K = 6.0  # fuerza del prior de mercado (en "partidos equivalentes")

TEAM_ALIASES = {
    "catar": "Qatar", "qatar": "Qatar",
    "suiza": "Switzerland", "switzerland": "Switzerland",
    "corea del sur": "South Korea", "chequia": "Czech Republic",
    "brasil": "Brazil", "brazil": "Brazil",
    "marruecos": "Morocco", "morocco": "Morocco",
    "haití": "Haiti", "haiti": "Haiti",
    "escocia": "Scotland", "scotland": "Scotland",
}


def map_team(name: str) -> str:
    return TEAM_ALIASES.get(name.strip().lower(), name.strip())


def fuzzy_player_index(player_match: pd.DataFrame) -> dict:
    names = player_match["player_name"].dropna().unique()
    return {"exact": {normalize_name(n): n for n in names},
            "tokens": {n: set(normalize_name(n).split()) for n in names}}


def match_player(betano_name: str, idx: dict) -> str | None:
    nb = normalize_name(betano_name)
    if nb in idx["exact"]:
        return idx["exact"][nb]
    bt = set(nb.split())
    best, best_score = None, 0
    for full, toks in idx["tokens"].items():
        if not (bt & toks) or nb.split()[-1] not in toks:
            continue
        if len(bt & toks) > best_score:
            best, best_score = full, len(bt & toks)
    return best


def _emit(rows, market, sel, p_model, odds, p_market=None, n_eff=None):
    """Agrega una fila con p_model, p_market (devig), blend y EV."""
    if odds is None or odds <= 1.0:
        return
    if p_market is not None and n_eff is not None:
        w = n_eff / (n_eff + BLEND_K)
        p_blend = w * p_model + (1 - w) * p_market
    else:
        w, p_blend = 1.0, p_model
    rows.append({
        "mercado": market, "selección": sel,
        "p_model": round(p_model, 4),
        "p_market": round(p_market, 4) if p_market is not None else np.nan,
        "w_model": round(w, 2),
        "p_blend": round(p_blend, 4),
        "cuota": odds, "p_impl": round(implied_prob(odds), 4),
        "EV_model": round(expected_value(p_model, odds), 4),
        "EV": round(expected_value(p_blend, odds), 4),
    })


def predict(odds_path: Path, team_a_override=None, team_b_override=None):
    data = OB.load(odds_path)
    ba, bb = OB.teams_from_meta(data)
    team_a = team_a_override or map_team(ba)
    team_b = team_b_override or map_team(bb)
    M = data["mercados"]

    pm = read_parquet(PM)
    disc = read_parquet(DISC)
    sp = read_parquet(SP)
    team_set = set(pm["team_name"])

    rows: list[dict] = []
    notes: list[str] = []
    meta = {"partido": data.get("partido"), "fecha": data.get("fecha"),
            "team_a": team_a, "team_b": team_b}

    # n_eff = min de partidos de ambos equipos (para el peso del blend)
    strengths = MM.team_strengths(pm) if team_a in team_set and team_b in team_set else None
    n_eff = None
    if strengths is not None:
        s = strengths.set_index("team_name")["n"]
        n_eff = float(min(s.get(team_a, 0), s.get(team_b, 0)))

    have_both = team_a in team_set and team_b in team_set
    lam_a = lam_b = None
    if have_both:
        lam_a, lam_b = MM.expected_goals(strengths, team_a, team_b)
        mat = MM.scoreline_matrix(lam_a, lam_b)
        mk = MM.markets_from_matrix(mat)
        notes.append(f"Goles esperados: {team_a} {lam_a:.2f} — {team_b} {lam_b:.2f} "
                     f"(n_eff={n_eff:.0f}, peso modelo={n_eff/(n_eff+BLEND_K):.2f})")

        if "resultado_partido" in M:
            o = OB.one_x_two(M["resultado_partido"])
            if all(k in o for k in ("home", "draw", "away")):
                pm_h, pm_d, pm_a = remove_vig([o["home"], o["draw"], o["away"]])
                for side, pmod, pmar, odd in [("home", mk["home"], pm_h, o["home"]),
                                              ("draw", mk["draw"], pm_d, o["draw"]),
                                              ("away", mk["away"], pm_a, o["away"])]:
                    _emit(rows, "1X2", side, pmod, odd, pmar, n_eff)
        if "goles_totales_mas_menos" in M:
            for line, sides in OB.over_under(M["goles_totales_mas_menos"]).items():
                if line in mk["totals"] and "over" in sides and "under" in sides:
                    p_over_m, p_under_m = remove_vig([sides["over"], sides["under"]])
                    _emit(rows, "Total goles", f"over {line}", mk["totals"][line]["over"],
                          sides["over"], p_over_m, n_eff)
                    _emit(rows, "Total goles", f"under {line}", mk["totals"][line]["under"],
                          sides["under"], p_under_m, n_eff)
        if "ambos_equipos_anotan" in M:
            yn = OB.yes_no(M["ambos_equipos_anotan"])
            if "yes" in yn and "no" in yn:
                py, pn = remove_vig([yn["yes"], yn["no"]])
                _emit(rows, "Ambos anotan", "sí", mk["btts_yes"], yn["yes"], py, n_eff)
                _emit(rows, "Ambos anotan", "no", mk["btts_no"], yn["no"], pn, n_eff)
        for key, lam, tname in [("local_goles_mas_menos", lam_a, team_a),
                                ("visita_goles_mas_menos", lam_b, team_b),
                                ("catar_goles_mas_menos", lam_a, team_a),
                                ("suiza_goles_mas_menos", lam_b, team_b),
                                ("brasil_goles_mas_menos", lam_a, team_a),
                                ("marruecos_goles_mas_menos", lam_b, team_b)]:
            if key in M:
                for line, sides in OB.over_under(M[key]).items():
                    tt = MM.team_total_goals(lam, line)
                    if "over" in sides and "under" in sides:
                        po, pu = remove_vig([sides["over"], sides["under"]])
                        _emit(rows, f"Goles {tname}", f"over {line}", tt["over"], sides["over"], po, n_eff)
                        _emit(rows, f"Goles {tname}", f"under {line}", tt["under"], sides["under"], pu, n_eff)
        if "marcador_correcto" in M:
            # mercado de un solo lado por marcador: blendeamos contra la implícita
            # cruda (1/cuota) para amansar la sobre-estimación de equipos flojos.
            for (a, b), odds in OB.correct_scores(M["marcador_correcto"]).items():
                _emit(rows, "Marcador", f"{a}-{b}", MM.correct_score(mat, a, b),
                      odds, implied_prob(odds), n_eff)

    # corners
    if "corners_mas_menos" in M:
        _, _, tot_c = MM.expected_corners(sp, team_a, team_b)
        if tot_c == tot_c:
            notes.append(f"Corners esperados: total {tot_c:.2f}")
            for line, sides in OB.over_under(M["corners_mas_menos"]).items():
                pp = negbin_over_under(tot_c, 0.05, line)
                if "over" in sides and "under" in sides:
                    po, pu = remove_vig([sides["over"], sides["under"]])
                    _emit(rows, "Corners", f"over {line}", pp.p_over, sides["over"], po, n_eff)
                    _emit(rows, "Corners", f"under {line}", pp.p_under, sides["under"], pu, n_eff)

    # tarjetas
    if "tarjetas_totales_mas_menos" in M:
        _, _, tot_k = MM.expected_cards(pm, disc, team_a, team_b)
        if tot_k > 0:
            notes.append(f"Tarjetas (amarillas) esperadas: total {tot_k:.2f}")
            for line, sides in OB.over_under(M["tarjetas_totales_mas_menos"]).items():
                pp = poisson_over_under(tot_k, line)
                if "over" in sides and "under" in sides:
                    po, pu = remove_vig([sides["over"], sides["under"]])
                    _emit(rows, "Tarjetas", f"over {line}", pp.p_over, sides["over"], po, n_eff)
                    _emit(rows, "Tarjetas", f"under {line}", pp.p_under, sides["under"], pu, n_eff)

    # props de jugador (model-only, mercado de un solo lado)
    idx = fuzzy_player_index(pm)
    unmatched = []

    def lam_table(target, xg, method):
        r = estimate_rate(pm, target_col=target, method=method, xg_col=xg,
                          prior_strength=4.0, min_matches=1)
        em = pm.groupby("player_id")["minutes_played"].mean().clip(30, 90)
        r = r.merge(em.rename("em"), on="player_id", how="left")
        r["lam"] = r["lam_per90"] * (r["em"].fillna(90) / 90)
        return r.set_index("player_name")["lam"]

    lam_sot = lam_table("shots_on_target", None, "shrinkage")
    lam_goals = lam_table("goals", "xg", "xg_shrinkage")

    if "tiros_al_arco" in M:
        for bname, thr in OB.player_shots(M["tiros_al_arco"]).items():
            full = match_player(bname, idx)
            if full is None or full not in lam_sot.index:
                unmatched.append(bname); continue
            lam = float(lam_sot.loc[full])
            for k, odds in thr.items():
                p = float(1 - poisson_over_under(lam, k - 0.5).p_under)
                _emit(rows, "Tiros al arco", f"{bname} {k}+", p, odds)
    if "goleador" in M:
        for bname, cols in OB.player_goalscorer(M["goleador"]).items():
            full = match_player(bname, idx)
            if full is None or full not in lam_goals.index:
                if bname not in unmatched:
                    unmatched.append(bname)
                continue
            p = float(prob_at_least_one(lam_goals.loc[full]))
            _emit(rows, "Goleador", f"{bname} anytime", p, cols.get("anytime"))

    df = pd.DataFrame(rows)
    meta.update({"notes": notes, "unmatched": unmatched, "lam_a": lam_a, "lam_b": lam_b,
                 "n_eff": n_eff, "have_team_model": have_both})
    return df, meta


def main():
    ap = argparse.ArgumentParser(description="Pronóstico de partido vs cuotas de Betano.")
    ap.add_argument("--odds", required=True)
    ap.add_argument("--team-a", default=None)
    ap.add_argument("--team-b", default=None)
    ap.add_argument("--ev-min", type=float, default=None)
    args = ap.parse_args()

    df, meta = predict(Path(args.odds), args.team_a, args.team_b)
    print(f"\n=== {meta['team_a']} vs {meta['team_b']} ===")
    for n in meta["notes"]:
        print("  ·", n)
    if meta["unmatched"]:
        print(f"  · jugadores sin match: {meta['unmatched']}")
    if len(df) == 0:
        print("\nNo se pudo valuar ningún mercado.")
        return
    show = df.copy()
    if args.ev_min is not None:
        show = show[show["EV"] > args.ev_min]
    show = show.sort_values("EV", ascending=False)
    print(f"\nMercados: {len(df)} | EV>0 (blend): {int((df['EV']>0).sum())}\n")
    cols = ["mercado", "selección", "p_model", "p_market", "p_blend", "cuota", "p_impl", "EV"]
    print(show.head(25)[cols].to_string(index=False))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    slug = f"{meta['team_a']}_{meta['team_b']}".lower().replace(" ", "_")
    out = OUT_DIR / f"{slug}_pred.md"
    lines = [f"# Pronóstico {meta['team_a']} vs {meta['team_b']}\n"]
    lines += [f"- {n}" for n in meta["notes"]]
    lines.append("\n| mercado | selección | p_model | p_market | p_blend | cuota | p_impl | EV |")
    lines.append("|---|---|--:|--:|--:|--:|--:|--:|")
    for _, r in df.sort_values("EV", ascending=False).iterrows():
        pm_s = f"{r['p_market']:.3f}" if r["p_market"] == r["p_market"] else "—"
        lines.append(f"| {r['mercado']} | {r['selección']} | {r['p_model']:.3f} | {pm_s} | "
                     f"{r['p_blend']:.3f} | {r['cuota']:.2f} | {r['p_impl']:.3f} | {r['EV']:+.3f} |")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n-> {out.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
