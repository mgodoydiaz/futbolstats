"""First-pass correlation analysis on StatsBomb player-match data.

Prints correlation matrix, top-correlated pairs, and per-player consistency.
Helps decide which targets are most predictable and which features matter.

Usage:
    python 09_correlations/explore_statsbomb.py
    python 09_correlations/explore_statsbomb.py --write 09_correlations/reports/statsbomb_corr.md
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.io import read_parquet  # noqa: E402

INPUT = PROJECT_ROOT / "02_data_processed" / "events_clean" / "statsbomb_player_match.parquet"

NUMERIC_TARGETS = [
    "minutes_played", "goals", "assists", "shots", "shots_on_target",
    "xg", "passes_attempted", "passes_completed", "key_passes",
    "dribbles_attempted", "dribbles_completed", "tackles",
    "interceptions", "fouls_committed", "fouls_drawn",
]


def correlation_report(df: pd.DataFrame) -> str:
    out = []
    out.append("# StatsBomb player-match correlation report")
    out.append("")
    out.append(f"Source: `{INPUT.relative_to(PROJECT_ROOT)}`")
    out.append(f"Rows: {len(df):,}")
    out.append(f"Players: {df['player_id'].nunique():,}")
    out.append(f"Matches: {df['match_id'].nunique():,}")
    out.append("")

    cols = [c for c in NUMERIC_TARGETS if c in df.columns]
    sub = df[cols].apply(pd.to_numeric, errors="coerce")

    out.append("## Per-match means and dispersion")
    out.append("")
    out.append("| Stat | mean | median | std | p90 |")
    out.append("|------|-----:|-------:|----:|----:|")
    for c in cols:
        s = sub[c].dropna()
        out.append(f"| {c} | {s.mean():.2f} | {s.median():.0f} | {s.std():.2f} | {s.quantile(0.9):.1f} |")
    out.append("")

    # Top correlated pairs
    corr = sub.corr()
    pairs = []
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            r = corr.loc[a, b]
            if pd.notna(r):
                pairs.append((a, b, r))
    pairs.sort(key=lambda x: abs(x[2]), reverse=True)

    out.append("## Top 15 correlated stat pairs")
    out.append("")
    out.append("| Stat A | Stat B | Pearson r |")
    out.append("|--------|--------|----------:|")
    for a, b, r in pairs[:15]:
        out.append(f"| {a} | {b} | {r:+.3f} |")
    out.append("")

    # Player consistency (std/mean per player for shots)
    out.append("## Player consistency in shots/match (top players, min 10 matches)")
    out.append("")
    pc = df.groupby(["player_id", "player_name"]).agg(
        n=("shots", "count"),
        mean_shots=("shots", "mean"),
        std_shots=("shots", "std"),
    ).reset_index()
    pc = pc[pc["n"] >= 10].copy()
    pc["cv"] = pc["std_shots"] / pc["mean_shots"].replace(0, pd.NA)
    out.append("Most consistent (low coefficient of variation, mean_shots >= 2):")
    out.append("")
    out.append("| Player | matches | mean | std | CV |")
    out.append("|--------|--------:|-----:|----:|---:|")
    consistent = pc[pc["mean_shots"] >= 2].nsmallest(10, "cv")
    for _, r in consistent.iterrows():
        out.append(f"| {r['player_name']} | {int(r['n'])} | {r['mean_shots']:.2f} | "
                   f"{r['std_shots']:.2f} | {r['cv']:.2f} |")
    out.append("")
    out.append("Most variable (high CV, mean_shots >= 2):")
    out.append("")
    out.append("| Player | matches | mean | std | CV |")
    out.append("|--------|--------:|-----:|----:|---:|")
    variable = pc[pc["mean_shots"] >= 2].nlargest(10, "cv")
    for _, r in variable.iterrows():
        out.append(f"| {r['player_name']} | {int(r['n'])} | {r['mean_shots']:.2f} | "
                   f"{r['std_shots']:.2f} | {r['cv']:.2f} |")

    return "\n".join(out)


def main():
    parser = argparse.ArgumentParser(description="Correlation exploration on StatsBomb player-match.")
    parser.add_argument("--write", default=None, help="Write report to this path (markdown).")
    args = parser.parse_args()

    if not INPUT.exists():
        print(f"Missing {INPUT.relative_to(PROJECT_ROOT)}")
        return

    df = read_parquet(INPUT)
    report = correlation_report(df)

    if args.write:
        out = PROJECT_ROOT / args.write
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(report, encoding="utf-8")
        print(f"Wrote {out.relative_to(PROJECT_ROOT)}")
    else:
        print(report)


if __name__ == "__main__":
    main()
