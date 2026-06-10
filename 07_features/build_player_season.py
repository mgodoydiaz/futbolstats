"""Build a single wide player-season table by joining every fbref stat type.

Input: 01_data_raw/players/fbref_<comp>_<stat>_<season>.parquet (one per stat)
Output: 02_data_processed/players_clean/fbref_<comp>_player_season.parquet

The join key is (player, team, league, season) since soccerdata doesn't expose
FBref's hex player_id. Duplicate column names across stat types get the
stat-type as suffix.

Usage:
    python 07_features/build_player_season.py --comp Big5
    python 07_features/build_player_season.py --comp Big5 --seasons 2020-2021,2024-2025
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.io import read_parquet, write_parquet  # noqa: E402

IN_DIR = PROJECT_ROOT / "01_data_raw" / "players"
OUT_DIR = PROJECT_ROOT / "02_data_processed" / "players_clean"

# Identity cols are present in every stat type. We dedup these on join.
KEY_COLS = ["player", "team", "league", "season"]
IDENTITY_COLS = KEY_COLS + ["nation", "pos", "age", "born"]


def _seasons_present(comp: str) -> list[str]:
    """Discover seasons we have for a given competition."""
    seen = set()
    for f in IN_DIR.glob(f"fbref_{comp}_*.parquet"):
        # filename: fbref_<comp>_<stat>_<season>.parquet
        parts = f.stem.split("_")
        # stat may itself contain underscores (playing_time), so season is the
        # last 9 chars (YYYY-YYYY) before .parquet
        season = "_".join(parts[-1:])
        # Actually season is always last token after stat. Reconstruct properly:
        season_token = parts[-1]
        if "-" in season_token and len(season_token) == 9:
            seen.add(season_token)
    return sorted(seen)


def join_season(comp: str, season: str) -> pd.DataFrame | None:
    files = sorted(IN_DIR.glob(f"fbref_{comp}_*_{season}.parquet"))
    if not files:
        return None

    merged: pd.DataFrame | None = None
    for f in files:
        # Stat type = filename minus "fbref_<comp>_" prefix and "_<season>" suffix
        stat = f.stem.removeprefix(f"fbref_{comp}_").removesuffix(f"_{season}")
        df = read_parquet(f)
        if not set(KEY_COLS).issubset(df.columns):
            print(f"  skip {f.name}: missing key cols")
            continue

        # Suffix all non-identity cols with stat type for traceability
        non_id_cols = [c for c in df.columns if c not in IDENTITY_COLS]
        rename = {c: f"{c}__{stat}" for c in non_id_cols}
        df = df.rename(columns=rename)

        if merged is None:
            merged = df
        else:
            # Drop identity duplicates from the right side except keys
            right_drop = [c for c in IDENTITY_COLS if c in df.columns and c not in KEY_COLS]
            df = df.drop(columns=right_drop)
            merged = merged.merge(df, on=KEY_COLS, how="outer")

    return merged


def main():
    parser = argparse.ArgumentParser(description="Join all fbref stat types into one player-season table.")
    parser.add_argument("--comp", default="Big5", help="Competition shortcut (default: Big5)")
    parser.add_argument("--seasons", default=None,
                        help="Comma-separated seasons (default: every season found)")
    args = parser.parse_args()

    seasons = (
        [s.strip() for s in args.seasons.split(",") if s.strip()]
        if args.seasons else _seasons_present(args.comp)
    )
    if not seasons:
        print(f"No fbref_{args.comp}_*.parquet files found in {IN_DIR.relative_to(PROJECT_ROOT)}")
        return

    parts = []
    for season in seasons:
        df = join_season(args.comp, season)
        if df is None or len(df) == 0:
            print(f"  {season}: no data")
            continue
        # soccerdata bug: Bundesliga rows come back with league=NaN.
        # Fill from team membership before reporting.
        if "league" in df.columns and df["league"].isna().any():
            team_to_league = (
                df.dropna(subset=["league"])
                  .drop_duplicates("team")
                  .set_index("team")["league"]
                  .to_dict()
            )
            mask = df["league"].isna()
            inferred = df.loc[mask, "team"].map(team_to_league)
            df.loc[mask, "league"] = inferred.fillna("GER-Bundesliga")
        print(f"  {season}: {len(df):>5,} players x {len(df.columns):>3} cols")
        parts.append(df)

    if not parts:
        print("Nothing to write.")
        return

    full = pd.concat(parts, ignore_index=True)
    out = OUT_DIR / f"fbref_{args.comp}_player_season.parquet"
    write_parquet(full, out)
    print()
    print(f"wrote {len(full):,} rows x {len(full.columns)} cols -> {out.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
