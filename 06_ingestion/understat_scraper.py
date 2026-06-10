"""Scrape Understat player stats — Cloudflare-free, xG-rich.

Understat (https://understat.com) covers the Big 5 European leagues + RFPL
from 2014 onwards. Their xG model is independent from StatsBomb's; useful
for cross-validation and for filling FBref's xG gap at season aggregate level.

soccerdata wraps Understat with plain HTTP (no Selenium / no Chrome).

Usage:
    python 06_ingestion/understat_scraper.py --comp Big5 --seasons 2024,2023,2022
    python 06_ingestion/understat_scraper.py --comp PL --seasons 2024 --stat match
    python 06_ingestion/understat_scraper.py --list

Outputs:
    01_data_raw/players/understat_<comp>_player_season_<season>.parquet
    01_data_raw/players/understat_<comp>_player_match_<season>.parquet
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

# Understat uses these league names (consistent with soccerdata's mapping)
COMPETITIONS = {
    "Big5": ["ENG-Premier League", "ESP-La Liga", "ITA-Serie A",
             "GER-Bundesliga", "FRA-Ligue 1"],
    "PL":   ["ENG-Premier League"],
    "LL":   ["ESP-La Liga"],
    "SA":   ["ITA-Serie A"],
    "BL":   ["GER-Bundesliga"],
    "L1":   ["FRA-Ligue 1"],
    "RU":   ["RUS-Premier League"],
}

STAT_TYPES = ["season", "match"]


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


def list_catalog() -> None:
    us = sd.Understat()
    leagues = us.read_leagues()
    print("Understat leagues available:")
    print(leagues.to_string())
    print()
    seasons = us.read_seasons()
    print("Seasons available (sample):")
    print(seasons.head(20).to_string())


def scrape(comp: str, season: str, stat: str) -> Path | None:
    leagues = COMPETITIONS[comp]
    print(f"[understat] {comp} | {stat} | season {season}")
    try:
        us = sd.Understat(leagues=leagues, seasons=season)
        if stat == "season":
            df = us.read_player_season_stats()
        elif stat == "match":
            df = us.read_player_match_stats()
        else:
            raise ValueError(f"unknown stat {stat}")
    except Exception as e:
        print(f"  [FAIL] {type(e).__name__}: {str(e)[:200]}")
        traceback.print_exc()
        return None

    df = df.reset_index()
    df = _flatten_columns(df)
    out = OUT_DIR / f"understat_{comp}_player_{stat}_{season}.parquet"
    write_parquet(df, out)
    print(f"  {len(df):,} rows x {len(df.columns)} cols -> {out.relative_to(PROJECT_ROOT)}")
    return out


def main():
    parser = argparse.ArgumentParser(description="Scrape Understat player stats.")
    parser.add_argument("--comp", default="Big5", choices=list(COMPETITIONS),
                        help="Competition shortcut (default: Big5)")
    parser.add_argument("--seasons", default="2024",
                        help="Comma-separated seasons (year format, e.g. 2024 = 2024-25)")
    parser.add_argument("--stat", default="season", choices=STAT_TYPES,
                        help="season (aggregate) or match (per-game)")
    parser.add_argument("--list", action="store_true",
                        help="List available leagues and seasons, then exit")
    args = parser.parse_args()

    if args.list:
        list_catalog()
        return

    seasons = [s.strip() for s in args.seasons.split(",") if s.strip()]
    for season in seasons:
        scrape(args.comp, season, args.stat)


if __name__ == "__main__":
    main()
