r"""Dashboard HTML de pronósticos de partidos (consumo propio).

Lee cada JSON de Betano en ``01_data_raw/odds/betano_*.json``, corre el predictor
(``08_models/predict_match.predict``) y arma una página HTML con una tabla por
partido. Columnas: mercado, selección, cuota, **% casa** (1/cuota), **p_model**,
**p_blend** (modelo mezclado con el mercado) y **EV**.

Uso:
    python 10_serving/build_match_dashboard.py
    python 10_serving/build_match_dashboard.py --ev-min 0.05

Salida:
    10_serving/matches/dashboard.html
"""
from __future__ import annotations

import argparse
import html
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

ODDS_DIR = PROJECT_ROOT / "01_data_raw" / "odds"
OUT = PROJECT_ROOT / "10_serving" / "matches" / "dashboard.html"

sys.path.insert(0, str(PROJECT_ROOT / "08_models"))
from predict_match import predict  # noqa: E402


def _ev_color(ev):
    if ev >= 0.20:
        return "#0F6E56"
    if ev >= 0.05:
        return "#1D9E75"
    if ev > 0:
        return "#639922"
    return "#888780"


def _table(df, ev_min):
    if len(df) == 0:
        return "<p style='color:var(--muted)'>Sin mercados valuados (¿equipos sin datos en StatsBomb?).</p>"
    d = df.sort_values("EV", ascending=False)
    rows = []
    for _, r in d.iterrows():
        ev = float(r["EV"])
        if ev_min is not None and ev <= ev_min:
            continue
        pm = f"{r['p_market']:.1%}" if r["p_market"] == r["p_market"] else "—"
        pb = f"{r['p_blend']:.1%}"
        hl = "background:#1a2a22;" if ev >= 0.05 else ""
        rows.append(f"""<tr style="{hl}">
          <td>{html.escape(str(r['mercado']))}</td>
          <td>{html.escape(str(r['selección']))}</td>
          <td class="num">{float(r['cuota']):.2f}</td>
          <td class="num muted">{float(r['p_impl']):.1%}</td>
          <td class="num">{float(r['p_model']):.1%}</td>
          <td class="num">{pb}</td>
          <td class="num" style="color:{_ev_color(ev)};font-weight:600">{ev:+.1%}</td>
        </tr>""")
    body = "".join(rows) or "<tr><td colspan='7' class='muted'>nada supera el filtro de EV</td></tr>"
    return f"""<table>
      <thead><tr>
        <th>Mercado</th><th>Selección</th><th class="num">Cuota</th>
        <th class="num">% casa</th><th class="num">p_model</th>
        <th class="num">p_blend</th><th class="num">EV</th>
      </tr></thead><tbody>{body}</tbody></table>"""


def _section(df, meta, ev_min):
    notes = "<br>".join(html.escape(n) for n in meta["notes"]) or "—"
    warn = ""
    if not meta["have_team_model"]:
        warn = ("<div class='warn'>⚠ Falta uno de los equipos en los datos StatsBomb: "
                "sólo se valúan props de jugador / mercados disponibles.</div>")
    unmatched = ""
    if meta["unmatched"]:
        unmatched = (f"<div class='muted' style='font-size:12px;margin-top:6px'>"
                     f"jugadores sin historial: {html.escape(', '.join(meta['unmatched']))}</div>")
    npos = int((df["EV"] > 0).sum()) if len(df) else 0
    return f"""<section>
      <h2>{html.escape(meta['team_a'])} <span class="vs">vs</span> {html.escape(meta['team_b'])}</h2>
      <div class="meta">{html.escape(str(meta.get('partido','')))} · {html.escape(str(meta.get('fecha','')))}
        · {len(df)} mercados · {npos} con EV&gt;0</div>
      <div class="notes">{notes}</div>
      {warn}
      {_table(df, ev_min)}
      {unmatched}
    </section>"""


def build(ev_min):
    files = sorted(ODDS_DIR.glob("betano_*.json"))
    sections = []
    for f in files:
        try:
            df, meta = predict(f)
            sections.append(_section(df, meta, ev_min))
        except Exception as e:  # noqa: BLE001
            sections.append(f"<section><h2>{html.escape(f.name)}</h2>"
                            f"<div class='warn'>error: {html.escape(str(e))}</div></section>")
    body = "\n".join(sections) or "<p>No hay JSON de Betano en 01_data_raw/odds/</p>"
    return f"""<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Pronósticos · Futbolstats</title>
<style>
  :root {{ --bg:#0f1419; --card:#1a1f27; --ink:#e6e9ee; --muted:#9aa0a6; --line:#2a313c; --gold:#d4af37; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink); padding:24px;
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; }}
  .wrap {{ max-width:1000px; margin:0 auto; }}
  h1 {{ font-size:1.6rem; margin:0 0 4px; }}
  .sub {{ color:var(--muted); margin-bottom:8px; }}
  .legend {{ background:var(--card); border:1px solid var(--line); border-radius:10px;
    padding:10px 14px; font-size:13px; color:var(--muted); margin-bottom:20px; }}
  section {{ background:var(--card); border:1px solid var(--line); border-radius:12px;
    padding:16px 18px; margin-bottom:18px; }}
  h2 {{ font-size:1.2rem; margin:0 0 2px; }} .vs {{ color:var(--muted); font-weight:400; font-size:.9rem; }}
  .meta {{ color:var(--muted); font-size:13px; margin-bottom:8px; }}
  .notes {{ color:var(--gold); font-size:12.5px; margin-bottom:10px; line-height:1.5; }}
  .warn {{ background:#2a1f1a; border:1px solid #5c3a2e; color:#e8c9b8; border-radius:8px;
    padding:8px 12px; font-size:13px; margin-bottom:10px; }}
  table {{ width:100%; border-collapse:collapse; font-size:13.5px; }}
  thead th {{ text-align:left; color:var(--muted); font-size:11.5px; text-transform:uppercase;
    letter-spacing:.04em; padding:6px 10px; border-bottom:1px solid var(--line); }}
  td {{ padding:6px 10px; border-bottom:1px solid var(--line); }}
  .num {{ text-align:right; font-variant-numeric:tabular-nums; }}
  .muted {{ color:var(--muted); }}
  .foot {{ color:var(--muted); font-size:12px; margin-top:18px; }}
  code {{ background:#222831; padding:1px 6px; border-radius:4px; }}
</style></head><body><div class="wrap">
  <h1>Pronósticos de partidos</h1>
  <div class="sub">Cuotas de Betano vs modelo · generado {date.today().isoformat()} · consumo propio</div>
  <div class="legend">
    <b>% casa</b> = 1/cuota (probabilidad implícita, con margen) ·
    <b>p_model</b> = probabilidad del modelo ·
    <b>p_blend</b> = modelo mezclado con el mercado (w según muestra) ·
    <b>EV</b> = p_blend × cuota − 1. Filas resaltadas: EV ≥ 5%.
    <br>⚠ No es asesoría. EV alto en equipos de poca muestra puede ser error del modelo.
  </div>
  {body}
  <div class="foot">Regenerar: <code>python 10_serving/build_match_dashboard.py</code></div>
</div></body></html>"""


def main():
    ap = argparse.ArgumentParser(description="Dashboard HTML de pronósticos de partidos.")
    ap.add_argument("--ev-min", type=float, default=None,
                    help="Mostrar sólo mercados con EV>ev-min.")
    args = ap.parse_args()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(args.ev_min), encoding="utf-8")
    n = len(list(ODDS_DIR.glob("betano_*.json")))
    print(f"Dashboard -> {OUT.relative_to(PROJECT_ROOT)} ({n} partido(s))")


if __name__ == "__main__":
    main()
