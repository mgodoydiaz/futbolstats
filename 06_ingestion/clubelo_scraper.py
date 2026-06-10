"""Pull club Elo ratings from clubelo.com via soccerdata.

ClubElo (http://clubelo.com) maintains daily Elo ratings for European clubs
since 1960. We use them as the canonical "strength of opponent" feature in
match-level prediction models.

Two access patterns:

    read_by_date(date)         -> snapshot of every club's Elo at one date.
    read_team_history(team)    -> full Elo history for one team.

Output:
    01_data_raw/teams/clubelo_snapshot_<date>.parquet
    01_data_raw/teams/clubelo_history_<team_slug>.parquet

Usage:
    python 06_ingestion/clubelo_scraper.py --snapshot 2025-05-01
    python 06_ingestion/clubelo_scraper.py --snapshot today
    python 06_ingestion/clubelo_scraper.py --team Barcelona
    python 06_ingestion/clubelo_scraper.py --team "Manchester United"
"""
from __future__ import annotations

import argparse
import os
import re
import sys
import traceback
from datetime import datetime
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

OUT_DIR = PROJECT_ROOT / "01_data_raw" / "teams"


def _slugify(name: str) -> str:
    s = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").lower()
    return s or "team"


def snapshot(date: str) -> Path | None:
    """Save a snapshot of every club's Elo on a given date."""
    if date == "today":
        date_obj = datetime.today()
    else:
        date_obj = datetime.strptime(date, "%Y-%m-%d")

    print(f"[clubelo] snapshot {date_obj:%Y-%m-%d}")
    try:
        elo = sd.ClubElo()
        df = elo.read_by_date(date_obj)
    except Exception as e:
        print(f"  [FAIL] {type(e).__name__}: {str(e)[:200]}")
        traceback.print_exc()
        return None

    df = df.reset_index()
    out = OUT_DIR / f"clubelo_snapshot_{date_obj:%Y-%m-%d}.parquet"
    write_parquet(df, out)
    print(f"  {len(df):,} clubs x {len(df.columns)} cols -> {out.relative_to(PROJECT_ROOT)}")
    return out


def team_history(team: str) -> Path | None:
    """Save the full Elo history for one team."""
    print(f"[clubelo] history for {team}")
    try:
        elo = sd.ClubElo()
        df = elo.read_team_history(team)
    except Exception as e:
        print(f"  [FAIL] {type(e).__name__}: {str(e)[:200]}")
        traceback.print_exc()
        return None

    df = df.reset_index()
    out = OUT_DIR / f"clubelo_history_{_slugify(team)}.parquet"
    write_parquet(df, out)
    print(f"  {len(df):,} daily ratings -> {out.relative_to(PROJECT_ROOT)}")
    return out


def main():
    parser = argparse.ArgumentParser(description="Pull club Elo ratings from clubelo.com.")
    parser.add_argument("--snapshot", default=None,
                        help="Snapshot date YYYY-MM-DD (or 'today').")
    parser.add_argument("--team", default=None,
                        help="Fetch full history for one team by name.")
    parser.add_argument("--teams", default=None,
                        help="Comma-separated team names for batch history fetch.")
    args = parser.parse_args()

    if not (args.snapshot or args.team or args.teams):
        parser.print_help()
        print("\nNo action requested. Use --snapshot, --team or --teams.")
        return

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.snapshot:
        snapshot(args.snapshot)

    teams: list[str] = []
    if args.team:
        teams.append(args.team)
    if args.teams:
        teams.extend([t.strip() for t in args.teams.split(",") if t.strip()])
    for t in teams:
        team_history(t)


if __name__ == "__main__":
    main()
