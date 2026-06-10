"""Scrape per-match player stats from FBref via soccerdata.

This is the key dataset for ML — `read_player_match_stats(stat_type='summary')`
returns the rich per-player-per-match view that includes passes attempted,
key passes, tackles, interceptions, blocks, dribbles, shots, SoT, xG, xA,
fouls, cards. Per-match (not per-season) is what we need for prediction.

Output:
    01_data_raw/matches/fbref_<comp>_summary_<season>.parquet
    01_data_raw/matches/fbref_<comp>_keepers_<season>.parquet

Cost warning: first run is slow because soccerdata fetches one HTML page per
match (~3 sec rate-limit + browser navigation). A Premier League season has
~380 matches → ~20 min for the first pass. Cached pages on rerun are fast.

Usage:
    python 06_ingestion/fbref_match_scraper.py --comp PL --season 2024-2025
    python 06_ingestion/fbref_match_scraper.py --comp PL --season 2024-2025 --limit 5
    python 06_ingestion/fbref_match_scraper.py --comp PL --season 2024-2025 --stat keepers
"""
from __future__ import annotations

import argparse
import os
import sys
import traceback
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault(
    "SOCCERDATA_DIR",
    str(PROJECT_ROOT / "01_data_raw" / "_cache" / "soccerdata"),
)

import soccerdata as sd  # noqa: E402

from lib.io import write_parquet  # noqa: E402

OUT_DIR = PROJECT_ROOT / "01_data_raw" / "matches"

COMPETITIONS = {
    "PL": "ENG-Premier League",
    "LL": "ESP-La Liga",
    "SA": "ITA-Serie A",
    "BL": "GER-Bundesliga",
    "L1": "FRA-Ligue 1",
}

MATCH_STAT_TYPES = ["summary", "keepers"]


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    if not isinstance(df.columns, pd.MultiIndex):
        return df
    new_cols = []
    for col in df.columns:
        parts = [
            str(p).strip()
            for p in col
            if str(p).strip() and not str(p).startswith("Unnamed")
        ]
        new_cols.append("_".join(parts) if parts else "")
    df = df.copy()
    df.columns = new_cols
    return df


def scrape_schedule(comp: str, season: str) -> pd.DataFrame:
    """Get the season schedule (one row per match) — needed for match_ids."""
    league = COMPETITIONS[comp]
    fb = sd.FBref(leagues=league, seasons=season)
    sched = fb.read_schedule()
    out = OUT_DIR / f"fbref_{comp}_schedule_{season}.parquet"
    write_parquet(sched.reset_index(), out)
    print(f"        schedule: {len(sched):>4,} matches -> {out.name}")
    return sched


def scrape_matches(comp: str, season: str, stat: str, limit: int | None = None) -> Path | None:
    league = COMPETITIONS[comp]
    print(f"[fbref-match] {league} | {stat} | season {season}"
          + (f" | limit {limit}" if limit else ""))
    fb = sd.FBref(leagues=league, seasons=season)

    match_id = None
    if limit is not None:
        sched = fb.read_schedule().reset_index()
        sched = sched[sched.game_id.notna() & sched.match_report.notna()]
        match_id = sched["game_id"].head(limit).tolist()
        print(f"        scraping {len(match_id)} matches (limited)")

    try:
        df = fb.read_player_match_stats(stat_type=stat, match_id=match_id)
    except Exception as e:
        print(f"        [FAIL] {stat}: {type(e).__name__}: {str(e)[:200]}")
        traceback.print_exc()
        return None

    df = df.reset_index()
    df = _flatten_columns(df)
    suffix = f"_n{limit}" if limit else ""
    out = OUT_DIR / f"fbref_{comp}_{stat}_{season}{suffix}.parquet"
    write_parquet(df, out)
    print(f"        {stat:<10s} {len(df):>6,} rows x {len(df.columns):>3} cols -> {out.name}")
    return out


def main():
    parser = argparse.ArgumentParser(
        description="Scrape per-match player stats from FBref via soccerdata."
    )
    parser.add_argument("--comp", default="PL", choices=list(COMPETITIONS),
                        help="Competition (default: PL)")
    parser.add_argument("--stat", default="summary", choices=MATCH_STAT_TYPES,
                        help="Match stat type (default: summary)")
    parser.add_argument("--season", default="2024-2025",
                        help="Season YYYY-YYYY (default: 2024-2025)")
    parser.add_argument("--seasons", default=None,
                        help="Comma-separated seasons (overrides --season)")
    parser.add_argument("--limit", type=int, default=None,
                        help="Only scrape first N matches (for pilots)")
    parser.add_argument("--schedule-only", action="store_true",
                        help="Just fetch the schedule, no per-match scraping")
    args = parser.parse_args()

    if args.seasons:
        seasons = [s.strip() for s in args.seasons.split(",") if s.strip()]
    else:
        seasons = [args.season]

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for season in seasons:
        if args.schedule_only:
            scrape_schedule(args.comp, season)
            continue
        scrape_schedule(args.comp, season)
        scrape_matches(args.comp, season, args.stat, limit=args.limit)


if __name__ == "__main__":
    main()
