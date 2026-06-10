r"""Backtest the value-betting pipeline and write a markdown report.

Reads ``02_data_processed/matches_view/match_value.parquet`` (regenerating it
with synthetic odds if missing), runs the threshold scan, calibration table and
bankroll/drawdown analysis from ``lib.backtest``, and writes a report to
``08_models/reports/betting_backtest.md``.

Usage:
    python 08_models/backtest_betting.py
    python 08_models/backtest_betting.py --ev-min 0.05
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.backtest import (  # noqa: E402
    bankroll_curve,
    calibration,
    max_drawdown,
    summary,
    threshold_scan,
)
from lib.io import read_parquet  # noqa: E402

VIEW = PROJECT_ROOT / "02_data_processed" / "matches_view"
REPORT = PROJECT_ROOT / "08_models" / "reports" / "betting_backtest.md"


def _ensure_match_value() -> pd.DataFrame:
    path = VIEW / "match_value.parquet"
    if not path.exists():
        print("match_value.parquet missing — building synthetic view...")
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "07_features" / "build_matches_view.py"),
             "--source", "statsbomb", "--synthetic"],
            check=True,
        )
    return read_parquet(path)


def main():
    parser = argparse.ArgumentParser(description="Backtest the betting pipeline.")
    parser.add_argument("--ev-min", type=float, default=0.05,
                        help="EV threshold for the headline bankroll curve (default 0.05).")
    args = parser.parse_args()

    mv = _ensure_match_value()
    book = mv["bookmaker"].iloc[0] if len(mv) else "—"
    print(f"Loaded {len(mv):,} priced bets (bookmaker={book})")

    scan = threshold_scan(mv)
    cal = calibration(mv)
    curve = bankroll_curve(mv, ev_min=args.ev_min)
    s = summary(mv, ev_min=args.ev_min)

    synthetic = (book == "synthetic")
    warn = (
        "> ⚠️ **Odds sintéticas** (mercado blando cotizado por posición). Los ROI de\n"
        "> abajo miden que la *lógica* del pipeline funciona, NO un edge real. Contra un\n"
        "> book sharp como Pinnacle el ROI esperado es ≈ −vig. Apostar arriesga el capital.\n"
        if synthetic else
        f"> Odds reales de `{book}`. Aun así, edge pasado no garantiza edge futuro.\n"
    )

    def _fmt(df):
        """Render a DataFrame as a GitHub markdown table (no tabulate dep)."""
        cols = list(df.columns)

        def cell(v):
            if isinstance(v, float):
                return f"{v:.4f}"
            return str(v)

        header = "| " + " | ".join(cols) + " |"
        sep = "| " + " | ".join("---" for _ in cols) + " |"
        body = [
            "| " + " | ".join(cell(v) for v in row) + " |"
            for row in df.itertuples(index=False, name=None)
        ]
        return "\n".join([header, sep, *body])

    lines = []
    lines.append("# Backtest — pipeline de value betting\n")
    lines.append(f"Generado desde `match_value.parquet` ({len(mv):,} apuestas cotizadas, "
                 f"bookmaker=`{book}`).\n")
    lines.append(warn)
    lines.append("\n## 1 · Barrido de threshold de EV\n")
    lines.append("ROI = profit / total apostado. `flat` = 1 unidad por apuesta; "
                 "`kelly` = fracción quarter-Kelly del bankroll.\n")
    lines.append(_fmt(scan.round(4)))
    lines.append("\n\n## 2 · Calibración (predicho vs observado)\n")
    lines.append("`gap = obs − pred`. Cercano a 0 en todos los bins ⇒ probabilidades "
                 "bien calibradas (precondición para confiar en el EV).\n")
    cal_show = cal.copy()
    cal_show["bin"] = cal_show["bin"].astype(str)
    lines.append(_fmt(cal_show.round(4)))
    lines.append(f"\n\nMAE de calibración: **{s['calibration_mae']:.4f}**\n")
    lines.append("\n## 3 · Curva de bankroll (quarter-Kelly, orden cronológico)\n")
    lines.append(f"Threshold EV > {args.ev_min}. Bankroll base 1.0, aditivo.\n")
    lines.append(
        f"- apuestas: **{s['n_bets']:,}**\n"
        f"- hit rate: **{s['hit_rate']:.3f}**\n"
        f"- ROI (flat): **{s['roi']:+.4f}**\n"
        f"- bankroll final: **{s['final_bankroll']:.3f}**\n"
        f"- max drawdown: **{max_drawdown(curve):.3f}**\n"
    )
    lines.append("\n## Lectura\n")
    lines.append(
        "- El **median EV** del universo completo ≈ −vig es la señal sana: la mayoría de\n"
        "  cuotas son −EV, como en cualquier mercado.\n"
        "- Donde el ROI realizado **sigue** al EV esperado al subir el threshold, la lógica\n"
        "  de selección está rankeando bien.\n"
        "- La **calibración** es la guardarraíl: si los bins altos de `p_model` aciertan\n"
        "  menos de lo que predicen (overconfidence), el EV de favoritos está inflado.\n"
        "- Antes de jugar plata real: re-entrenar los targets sparse con `count:poisson`\n"
        "  y validar calibración out-of-sample, no in-sample.\n"
    )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("".join(lines), encoding="utf-8")
    print(f"\nReport -> {REPORT.relative_to(PROJECT_ROOT)}")
    print(f"  n_bets={s['n_bets']:,}  roi={s['roi']:+.4f}  "
          f"hit_rate={s['hit_rate']:.3f}  cal_mae={s['calibration_mae']:.4f}")


if __name__ == "__main__":
    main()
