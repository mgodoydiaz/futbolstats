"""Build the per-player-per-match training table from FBref match-level data.

Joins:
    01_data_raw/matches/fbref_<comp>_summary_<season>.parquet   (per-player stats)
    01_data_raw/matches/fbref_<comp>_schedule_<season>.parquet  (date, home/away, opponent)

Output:
    02_data_processed/players_clean/fbref_<comp>_player_match.parquet

This is THE training table for stat predictors. One row = one player in one
match. Targets: shots, passes_completed, tackles, etc. Features: rolling form,
opponent strength, days_rest. (Feature engineering is in separate scripts.)

Usage:
    python 07_features/build_player_match.py --comp PL
    python 07_features/build_player_match.py --comp PL --seasons 2023-2024,2024-2025
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.io import read_parquet, write_parquet  # noqa: E402

IN_DIR = PROJECT_ROOT / "01_data_raw" / "matches"
OUT_DIR = PROJECT_ROOT / "02_data_processed" / "players_clean"


def _seasons_present(comp: str) -> list[str]:
    seen = set()
    for f in IN_DIR.glob(f"fbref_{comp}_summary_*.parquet"):
        season = f.stem.removeprefix(f"fbref_{comp}_summary_").split("_n")[0]
        if "-" in season and len(season) == 9:
            seen.add(season)
    return sorted(seen)


def _enrich_with_schedule(player_match: pd.DataFrame, schedule: pd.DataFrame) -> pd.DataFrame:
    """Add date, home/away flag, opponent_id from the schedule."""
    if "game_id" not in player_match.columns:
        return player_match  # nothing to join on

    sched_cols = ["game_id", "date", "home_team", "away_team"]
    sched_cols = [c for c in sched_cols if c in schedule.columns]
    s = schedule[sched_cols].drop_duplicates("game_id")

    merged = player_match.merge(s, on="game_id", how="left")
    if {"team", "home_team", "away_team"}.issubset(merged.columns):
        merged["is_home"] = (merged["team"] == merged["home_team"]).astype("Int8")
        merged["opponent"] = merged.apply(
            lambda r: r["away_team"] if r["team"] == r["home_team"] else r["home_team"],
            axis=1,
        )
    return merged


def build_for(comp: str, season: str) -> pd.DataFrame | None:
    summary_path = IN_DIR / f"fbref_{comp}_summary_{season}.parquet"
    sched_path = IN_DIR / f"fbref_{comp}_schedule_{season}.parquet"
    if not summary_path.exists():
        print(f"  {season}: missing {summary_path.name}, skip")
        return None

    pm = read_parquet(summary_path)
    if sched_path.exists():
        sched = read_parquet(sched_path)
        pm = _enrich_with_schedule(pm, sched)
    else:
        print(f"  {season}: schedule not found, skipping context enrichment")

    pm["season"] = season
    pm["comp"] = comp
    return pm


def main():
    parser = argparse.ArgumentParser(description="Build per-player-per-match training table.")
    parser.add_argument("--comp", default="PL", help="Competition shortcut (default: PL)")
    parser.add_argument("--seasons", default=None,
                        help="Comma-separated seasons (default: every season found)")
    args = parser.parse_args()

    seasons = (
        [s.strip() for s in args.seasons.split(",") if s.strip()]
        if args.seasons else _seasons_present(args.comp)
    )
    if not seasons:
        print(f"No fbref_{args.comp}_summary_*.parquet files in {IN_DIR.relative_to(PROJECT_ROOT)}")
        return

    parts = []
    for season in seasons:
        df = build_for(args.comp, season)
        if df is None or len(df) == 0:
            continue
        print(f"  {season}: {len(df):>6,} player-match rows x {len(df.columns):>3} cols")
        parts.append(df)

    if not parts:
        print("Nothing to write.")
        return

    full = pd.concat(parts, ignore_index=True)
    out = OUT_DIR / f"fbref_{args.comp}_player_match.parquet"
    write_parquet(full, out)
    print()
    print(f"wrote {len(full):,} rows x {len(full.columns)} cols -> {out.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
