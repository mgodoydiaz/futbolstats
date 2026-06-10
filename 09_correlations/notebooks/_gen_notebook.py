"""Generator for 01_match_betting.ipynb — writes a valid nbformat v4 notebook
without needing the nbformat package. Run once; safe to delete afterwards.

    python 09_correlations/notebooks/_gen_notebook.py
"""
import json
import os


def _src(lines):
    text = "\n".join(lines)
    parts = text.split("\n")
    return [p + ("\n" if i < len(parts) - 1 else "") for i, p in enumerate(parts)]


def md(*lines):
    return {"cell_type": "markdown", "metadata": {}, "source": _src(lines)}


def code(*lines):
    return {"cell_type": "code", "metadata": {}, "execution_count": None,
            "outputs": [], "source": _src(lines)}


cells = []

cells.append(md(
    "# 01 · Análisis de valor en apuestas (player props)",
    "",
    "Pipeline end-to-end: **predicción del modelo → probabilidad → EV vs cuota → Kelly**.",
    "",
    "Este notebook **no** decide por vos: expone `p_model`, `implied_prob`, `edge`, `ev` y",
    "`kelly` como columnas y vos elegís el threshold. Funciona en dos modos:",
    "",
    "- **Backtest** (default): carga `match_value.parquet` con outcomes realizados y odds",
    "  sintéticas → mide ROI/calibración de la lógica.",
    "- **Live**: reemplazás `match_odds.parquet` con cuotas scrapeadas de Pinnacle",
    "  (`06_ingestion/pinnacle_scraper.py`) y re-corrés el builder.",
    "",
    "> ⚠️ Las odds del backtest son **sintéticas** (mercado blando cotizado por posición).",
    "> No son una afirmación de edge real. El edge real sólo se mide contra odds de un",
    "> book de verdad. Apostar dinero conlleva riesgo de pérdida total.",
))

cells.append(md("## 1 · Setup y carga de datos"))

cells.append(code(
    "import sys, subprocess",
    "from pathlib import Path",
    "",
    "import numpy as np",
    "import pandas as pd",
    "import matplotlib.pyplot as plt",
    "",
    "# Project root = primer ancestro que contiene lib/",
    "ROOT = Path.cwd()",
    "while not (ROOT / 'lib').exists() and ROOT != ROOT.parent:",
    "    ROOT = ROOT.parent",
    "sys.path.insert(0, str(ROOT))",
    "",
    "from lib.io import read_parquet",
    "from lib import betting",
    "",
    "VIEW = ROOT / '02_data_processed' / 'matches_view'",
    "pd.set_option('display.width', 160)",
    "pd.set_option('display.max_columns', 40)",
    "print('project root:', ROOT)",
))

cells.append(md(
    "Si la vista de partidos no existe todavía, la generamos con odds sintéticas",
    "(idempotente, tarda unos segundos).",
))

cells.append(code(
    "if not (VIEW / 'match_value.parquet').exists():",
    "    print('match_value.parquet no existe — generando vista sintética...')",
    "    subprocess.run([sys.executable, str(ROOT / '07_features' / 'build_matches_view.py'),",
    "                    '--source', 'statsbomb', '--synthetic'], check=True)",
    "",
    "fixtures      = read_parquet(VIEW / 'fixtures.parquet')",
    "match_players = read_parquet(VIEW / 'match_players.parquet')",
    "match_value   = read_parquet(VIEW / 'match_value.parquet')",
    "print(f'fixtures:      {len(fixtures):>7,}')",
    "print(f'match_players: {len(match_players):>7,}')",
    "print(f'match_value:   {len(match_value):>7,}')",
    "match_value.head(3)",
))

cells.append(md(
    "## 2 · Explorar un partido concreto",
    "",
    "Elegí un `match_id` de `fixtures` y mirá todas las apuestas disponibles ordenadas por EV.",
))

cells.append(code(
    "fixtures.sort_values('date', ascending=False)["
    "['match_id','date','home_team','away_team','competition_slug']].head(10)",
))

cells.append(code(
    "# Elegí un partido (por defecto, el más reciente)",
    "MATCH_ID = fixtures.sort_values('date', ascending=False)['match_id'].iloc[0]",
    "",
    "cols = ['player_name','position_group','market','line','side','p_model',",
    "        'implied_prob','edge','ev','kelly_full','kelly_25pct','odds']",
    "m = match_value[match_value.match_id == MATCH_ID].sort_values('ev', ascending=False)",
    "print(f'{len(m)} cuotas para el partido {MATCH_ID}')",
    "m[cols].head(20)",
))

cells.append(md(
    "## 3 · Filtrar por threshold (lo definís vos)",
    "",
    "No hay umbral hard-coded. Cambiá `EV_MIN` y `KELLY_MIN` para ver qué apuestas pasan.",
))

cells.append(code(
    "EV_MIN    = 0.05   # +5% de edge esperado",
    "KELLY_MIN = 0.01   # stake mínimo de 1% bankroll (quarter-Kelly)",
    "",
    "picks = match_value[(match_value.ev > EV_MIN) &",
    "                    (match_value.kelly_25pct > KELLY_MIN)].copy()",
    "print(f'{len(picks):,} apuestas pasan EV>{EV_MIN}, kelly25>{KELLY_MIN}')",
    "picks.sort_values('ev', ascending=False)[cols].head(25)",
))

cells.append(md(
    "## 4 · Distribución de EV y calibración del modelo",
    "",
    "La **calibración** decide si las probabilidades sirven para apostar: si `p_model=0.6`,",
    "¿gana realmente el 60% de las veces? Si la curva se aleja de la diagonal, el modelo",
    "está mal calibrado y el EV miente.",
))

cells.append(code(
    "fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))",
    "",
    "# (a) Distribución de EV — la masa debería centrarse en torno a -vig",
    "ax[0].hist(match_value.ev.clip(-1, 2), bins=80, color='#4C78A8')",
    "ax[0].axvline(0, color='crimson', ls='--', lw=1, label='EV = 0')",
    "ax[0].axvline(match_value.ev.median(), color='k', ls=':', lw=1,",
    "              label=f'mediana = {match_value.ev.median():.3f}')",
    "ax[0].set(title='Distribución de EV (clip [-1,2])', xlabel='EV por unidad', ylabel='cuotas')",
    "ax[0].legend()",
    "",
    "# (b) Curva de calibración",
    "b = match_value[match_value.won.notna()].copy()",
    "b['bin'] = pd.cut(b.p_model, np.linspace(0, 1, 11))",
    "cal = b.groupby('bin', observed=True).agg(pred=('p_model','mean'), obs=('won','mean'),",
    "                                           n=('won','size')).dropna()",
    "ax[1].plot([0,1], [0,1], 'k--', lw=1, label='calibración perfecta')",
    "ax[1].plot(cal.pred, cal.obs, 'o-', color='#E45756', label='modelo')",
    "ax[1].set(title='Calibración', xlabel='p_model', ylabel='frecuencia real de acierto')",
    "ax[1].legend()",
    "plt.tight_layout(); plt.show()",
    "cal.round(3)",
))

cells.append(md(
    "## 5 · Backtest: ROI por threshold de EV",
    "",
    "Simula apostar **stake plano** vs **quarter-Kelly** sobre las apuestas que superan cada",
    "umbral de EV. PnL por apuesta = `(odds-1)` si ganó, `-1` si perdió, `0` si push.",
))

cells.append(code(
    "def backtest(df, ev_min, stake='flat'):",
    "    bet = df[(df.ev > ev_min) & (df.won.notna())].copy()",
    "    if len(bet) == 0:",
    "        return None",
    "    win = bet.won.astype(bool)",
    "    gross = np.where(win, bet.odds - 1.0, -1.0)        # PnL por unidad apostada",
    "    w = np.ones(len(bet)) if stake == 'flat' else bet.kelly_25pct.to_numpy()",
    "    pnl = gross * w",
    "    return {'ev_min': ev_min, 'stake': stake, 'n_bets': len(bet),",
    "            'staked': w.sum(), 'profit': pnl.sum(),",
    "            'roi': pnl.sum() / w.sum() if w.sum() else np.nan,",
    "            'hit_rate': win.mean(), 'mean_ev': bet.ev.mean()}",
    "",
    "rows = []",
    "for thr in [0.0, 0.02, 0.05, 0.10, 0.20, 0.40]:",
    "    for stake in ['flat', 'kelly']:",
    "        r = backtest(match_value, thr, stake)",
    "        if r: rows.append(r)",
    "bt = pd.DataFrame(rows)",
    "bt.round(4)",
))

cells.append(code(
    "flat = bt[bt.stake == 'flat']",
    "fig, ax = plt.subplots(figsize=(8, 4.5))",
    "ax.plot(flat.ev_min, flat.mean_ev, 'o-', label='EV medio (esperado)')",
    "ax.plot(flat.ev_min, flat.roi, 's-', label='ROI realizado')",
    "ax.axhline(0, color='k', lw=0.8)",
    "ax.set(title='Backtest: EV esperado vs ROI realizado', xlabel='threshold EV_min',",
    "       ylabel='retorno por unidad')",
    "ax.legend(); plt.tight_layout(); plt.show()",
))

cells.append(md(
    "## 6 · Curva de bankroll (orden cronológico)",
    "",
    "Apuesta secuencial en el tiempo con quarter-Kelly sobre las apuestas filtradas.",
    "Muestra el drawdown real, no sólo el ROI agregado.",
))

cells.append(code(
    "EV_MIN_BT = 0.05",
    "seq = match_value[(match_value.ev > EV_MIN_BT) & (match_value.won.notna())].copy()",
    "seq = seq.sort_values('date')",
    "win = seq.won.astype(bool)",
    "seq['ret'] = np.where(win, seq.odds - 1.0, -1.0) * seq.kelly_25pct",
    "seq['bankroll'] = 1.0 + seq['ret'].cumsum()   # bankroll aditivo, base 1.0",
    "",
    "fig, ax = plt.subplots(figsize=(11, 4.5))",
    "ax.plot(seq.date.values, seq.bankroll.values, lw=1, color='#54A24B')",
    "ax.axhline(1.0, color='k', ls='--', lw=0.8)",
    "ax.set(title=f'Bankroll quarter-Kelly (EV>{EV_MIN_BT}) — odds SINTÉTICAS',",
    "       xlabel='fecha', ylabel='bankroll (base 1.0)')",
    "plt.tight_layout(); plt.show()",
    "print('bankroll final:', round(seq.bankroll.iloc[-1], 3), '| apuestas:', len(seq))",
))

cells.append(md(
    "## 7 · Modo live (cuando esté el scraper de Pinnacle)",
    "",
    "```bash",
    "# 1. Scrapear cuotas reales de Pinnacle para los fixtures próximos",
    "python 06_ingestion/pinnacle_scraper.py --sport soccer --markets player_props",
    "",
    "# 2. Reconstruir la vista usando esas odds (sin --synthetic)",
    "python 07_features/build_matches_view.py --source statsbomb",
    "```",
    "",
    "Después re-corrés las celdas: `match_value` traerá `bookmaker='pinnacle'` y EV real.",
    "Para apuestas futuras `won` será `NaN` (todavía no se jugó) — filtrá por `ev` y `kelly`.",
    "Revisá la **calibración** (sección 4) sobre histórico antes de confiar en el EV de",
    "partidos futuros.",
))

nb = {
    "cells": cells,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.12"},
    },
    "nbformat": 4,
    "nbformat_minor": 5,
}

out = os.path.join(os.path.dirname(__file__), "01_match_betting.ipynb")
with open(out, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)
print("wrote", out, "with", len(cells), "cells")
