"""Scrape player stats from FBref via the `soccerdata` wrapper.

FBref enabled Cloudflare JS challenge in 2024 — `requests` / `curl_cffi` 403.
`soccerdata` uses SeleniumBase (headless Chrome) to solve the challenge.

Usage:
    python 06_ingestion/fbref_scraper.py --comp Big5 --stat standard
    python 06_ingestion/fbref_scraper.py --comp Big5 --all-stats
    python 06_ingestion/fbref_scraper.py --comp Big5 --all-stats \
        --seasons 2020-2021,2021-2022,2022-2023,2023-2024,2024-2025

Output:
    01_data_raw/players/fbref_<comp>_<stat>_<season>.parquet
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

OUT_DIR = PROJECT_ROOT / "01_data_raw" / "players"

# Our shortcut → soccerdata's league key
COMPETITIONS = {
    "Big5": "Big 5 European Leagues Combined",
    "PL":   "ENG-Premier League",
    "LL":   "ESP-La Liga",
    "SA":   "ITA-Serie A",
    "BL":   "GER-Bundesliga",
    "L1":   "FRA-Ligue 1",
}

# soccerdata 1.9 only exposes these stat types for read_player_season_stats.
# Passing / defense / possession / GCA detail must be sourced from
# read_player_match_stats(stat_type='summary') -> see fbref_match_scraper.py.
STAT_TYPES = [
    "standard",
    "shooting",
    "playing_time",
    "misc",
    "keeper",
]


def _flatten_columns(df: pd.DataFrame) -> pd.DataFrame:
    """('Performance','Gls') -> 'Performance_Gls'. Drop Unnamed/empty levels."""
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


def scrape_one(fb: "sd.FBref", comp: str, stat: str, season: str) -> Path | None:
    try:
        df = fb.read_player_season_stats(stat_type=stat)
    except Exception as e:
        print(f"        [FAIL] {stat}: {type(e).__name__}: {e}")
        return None
    df = df.reset_index()
    df = _flatten_columns(df)
    out = OUT_DIR / f"fbref_{comp}_{stat}_{season}.parquet"
    write_parquet(df, out)
    print(f"        {stat:<20s} {len(df):>5,} rows x {len(df.columns):>3} cols -> {out.name}")
    return out


def scrape_season(comp: str, season: str, stats: list[str]) -> dict[str, Path | None]:
    league = COMPETITIONS[comp]
    print(f"[fbref] {league} | season {season}")
    fb = sd.FBref(leagues=league, seasons=season)
    results: dict[str, Path | None] = {}
    for stat in stats:
        try:
            results[stat] = scrape_one(fb, comp, stat, season)
        except Exception:
            print(f"        [FATAL] {stat}: {traceback.format_exc().splitlines()[-1]}")
            results[stat] = None
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Scrape player stats from FBref via soccerdata."
    )
    parser.add_argument(
        "--comp", default="Big5", choices=list(COMPETITIONS),
        help="Competition (default: Big5)",
    )
    parser.add_argument(
        "--stat", default=None, choices=STAT_TYPES,
        help="Single stat category (default: standard if --all-stats not set)",
    )
    parser.add_argument(
        "--all-stats", action="store_true",
        help="Scrape every stat category for the given comp+season",
    )
    parser.add_argument(
        "--season", default="2024-2025",
        help="Season in YYYY-YYYY format (default: 2024-2025)",
    )
    parser.add_argument(
        "--seasons", default=None,
        help="Comma-separated seasons (overrides --season)",
    )
    args = parser.parse_args()

    if args.all_stats:
        stats = STAT_TYPES
    elif args.stat:
        stats = [args.stat]
    else:
        stats = ["standard"]

    if args.seasons:
        seasons = [s.strip() for s in args.seasons.split(",") if s.strip()]
    else:
        seasons = [args.season]

    overall: list[Path] = []
    for season in seasons:
        results = scrape_season(args.comp, season, stats)
        overall.extend([p for p in results.values() if p is not None])

    print()
    print(f"[fbref] done: wrote {len(overall)} parquet file(s)")


if __name__ == "__main__":
    main()
