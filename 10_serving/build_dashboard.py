r"""Genera un dashboard HTML autocontenido del value board del Mundial.

Lee el último ``10_serving/worldcup/value_board_<fecha>.parquet`` (producido por
``08_models/worldcup_value.py``) y emite un HTML con estilos embebidos, tabla
ordenable y EV codificado por color. Sin dependencias de red — se abre en
cualquier navegador.

Uso:
    python 08_models/worldcup_value.py            # primero, generar el board
    python 10_serving/build_dashboard.py          # luego, el dashboard
    python 10_serving/build_dashboard.py --top 50

Salida:
    10_serving/worldcup/dashboard.html
"""
from __future__ import annotations

import argparse
import html
import sys
from datetime import date
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

WC_DIR = PROJECT_ROOT / "10_serving" / "worldcup"

MARKET_ES = {"anytime_goalscorer": "Gol", "to_be_booked": "Tarjeta"}


def latest_board() -> pd.DataFrame:
    files = sorted(WC_DIR.glob("value_board_*.parquet"))
    if not files:
        raise FileNotFoundError(
            "No hay value board. Corré: python 08_models/worldcup_value.py")
    return pd.read_parquet(files[-1])


def _ev_color(ev: float) -> str:
    if ev >= 0.30:
        return "#1a7f37"
    if ev >= 0.10:
        return "#3fa34d"
    if ev > 0.0:
        return "#7cb342"
    return "#9aa0a6"


def _rows_html(board: pd.DataFrame, top: int) -> str:
    cells = []
    for _, r in board.head(top).iterrows():
        match = (f"{html.escape(str(r.get('home_team','') or ''))} – "
                 f"{html.escape(str(r.get('away_team','') or ''))}")
        market = MARKET_ES.get(r["market"], r["market"])
        ev = float(r["ev"])
        low_sample = " <span class='warn' title='Pocos partidos: mayor incertidumbre'>⚠</span>" \
            if int(r["matches"]) < 8 else ""
        cells.append(f"""
        <tr>
          <td class="player">{html.escape(str(r.get('player_name','')))}{low_sample}</td>
          <td><span class="mkt mkt-{r['market']}">{market}</span></td>
          <td class="match">{match}</td>
          <td class="num">{int(r['matches'])}</td>
          <td class="num">{float(r['p_model']):.0%}</td>
          <td class="num">{float(r['odds']):.2f}</td>
          <td class="num">{float(r['implied_prob']):.0%}</td>
          <td class="num ev" style="color:{_ev_color(ev)};font-weight:600">{ev:+.0%}</td>
          <td class="num">{float(r['kelly']):.1%}</td>
        </tr>""")
    return "".join(cells)


def build_html(board: pd.DataFrame, top: int) -> str:
    n = len(board)
    pos = int((board["ev"] > 0).sum())
    rows = _rows_html(board.sort_values("ev", ascending=False), top)
    today = date.today().isoformat()
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Value Board · Mundial 2026 · Futbolstats</title>
<style>
  :root {{
    --bg:#0f1419; --card:#1a1f27; --ink:#e6e9ee; --muted:#9aa0a6;
    --line:#2a313c; --accent:#3fa34d; --gold:#d4af37;
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
    line-height:1.5; padding:24px; }}
  .wrap {{ max-width:1100px; margin:0 auto; }}
  h1 {{ font-size:1.7rem; margin:0 0 4px; }}
  h1 .emoji {{ filter:saturate(1.2); }}
  .sub {{ color:var(--muted); margin-bottom:20px; }}
  .stats {{ display:flex; gap:12px; flex-wrap:wrap; margin-bottom:20px; }}
  .stat {{ background:var(--card); border:1px solid var(--line); border-radius:10px;
    padding:12px 18px; min-width:120px; }}
  .stat .v {{ font-size:1.6rem; font-weight:700; color:var(--gold); }}
  .stat .l {{ font-size:.8rem; color:var(--muted); text-transform:uppercase;
    letter-spacing:.04em; }}
  .disclaimer {{ background:#2a1f1a; border:1px solid #5c3a2e; border-radius:10px;
    padding:12px 16px; font-size:.85rem; color:#e8c9b8; margin-bottom:20px; }}
  table {{ width:100%; border-collapse:collapse; background:var(--card);
    border:1px solid var(--line); border-radius:12px; overflow:hidden; }}
  thead th {{ background:#222831; text-align:left; padding:10px 12px;
    font-size:.78rem; text-transform:uppercase; letter-spacing:.04em;
    color:var(--muted); border-bottom:1px solid var(--line); }}
  td {{ padding:10px 12px; border-bottom:1px solid var(--line); font-size:.92rem; }}
  tbody tr:hover {{ background:#202632; }}
  .player {{ font-weight:600; }}
  .num {{ text-align:right; font-variant-numeric:tabular-nums; }}
  .match {{ color:var(--muted); font-size:.85rem; }}
  .mkt {{ font-size:.75rem; padding:2px 8px; border-radius:999px; }}
  .mkt-anytime_goalscorer {{ background:#1e3a2a; color:#7ee2a8; }}
  .mkt-to_be_booked {{ background:#3a2e1e; color:#e2c87e; }}
  .warn {{ color:#e2b04a; cursor:help; }}
  .legend {{ color:var(--muted); font-size:.82rem; margin-top:14px; }}
  .foot {{ color:var(--muted); font-size:.78rem; margin-top:24px;
    border-top:1px solid var(--line); padding-top:12px; }}
  code {{ background:#222831; padding:1px 6px; border-radius:4px; font-size:.85em; }}
</style>
</head>
<body>
<div class="wrap">
  <h1><span class="emoji">🏆</span> Value Board · Mundial 2026</h1>
  <div class="sub">Cuotas reales de <b>Pinnacle</b> vs modelo <code>xg_shrinkage</code> ·
     generado {today}</div>

  <div class="stats">
    <div class="stat"><div class="v">{n}</div><div class="l">mercados valuados</div></div>
    <div class="stat"><div class="v">{pos}</div><div class="l">con EV &gt; 0</div></div>
    <div class="stat"><div class="v">{top}</div><div class="l">mostrados</div></div>
  </div>

  <div class="disclaimer">
    ⚠️ <b>No es asesoría de apuestas.</b> La implícita de Pinnacle ya incluye margen,
    así que un EV&gt;0 es conservador — pero pocos partidos por jugador (⚠ marca muestra
    chica) implican alta incertidumbre. El modelo fue validado por calibración
    (LogLoss 0.27, cal-MAE 0.035) pero es más crudo que un book sharp. Apostar
    arriesga la pérdida total del capital.
  </div>

  <table>
    <thead><tr>
      <th>Jugador</th><th>Mercado</th><th>Partido</th>
      <th class="num">PJ</th><th class="num">p&nbsp;modelo</th><th class="num">cuota</th>
      <th class="num">p&nbsp;impl.</th><th class="num">EV</th><th class="num">Kelly</th>
    </tr></thead>
    <tbody>{rows}</tbody>
  </table>

  <div class="legend">
    <b>p modelo</b>: P(ocurre el evento) según el modelo · <b>p impl.</b>: 1/cuota (con
    margen) · <b>EV</b>: valor esperado por unidad · <b>Kelly</b>: stake sugerido
    (quarter-Kelly) · <b>⚠</b>: menos de 8 partidos de muestra.
  </div>
  <div class="foot">
    Futbolstats · pipeline: <code>scraper Pinnacle → lib.scoring → EV/Kelly</code> ·
    regenerar: <code>python 08_models/worldcup_value.py &amp;&amp; python 10_serving/build_dashboard.py</code>
  </div>
</div>
</body>
</html>"""


def main():
    ap = argparse.ArgumentParser(description="Dashboard HTML del value board del Mundial.")
    ap.add_argument("--top", type=int, default=40, help="Filas a mostrar (default 40).")
    args = ap.parse_args()

    board = latest_board()
    out = WC_DIR / "dashboard.html"
    out.write_text(build_html(board, args.top), encoding="utf-8")
    print(f"Dashboard -> {out.relative_to(PROJECT_ROOT)}  ({len(board)} mercados, "
          f"mostrando top {args.top})")


if __name__ == "__main__":
    main()
