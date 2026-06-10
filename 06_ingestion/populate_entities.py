"""Populate 03_entities/players.csv and teams.csv from scraped parquets.

Idempotent: reads the existing CSV, merges new rows, dedups on `<entity>_id`,
writes back. Safe to run multiple times. Safe to run alongside scrapers from
other sources — IDs are prefixed by source so they don't collide.

Usage:
    python 06_ingestion/populate_entities.py
    python 06_ingestion/populate_entities.py --source fbref
    python 06_ingestion/populate_entities.py --dry-run
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.io import read_entities, read_parquet, write_entities  # noqa: E402
from lib.text import normalize_name, normalize_team_name  # noqa: E402

RAW_PLAYERS_DIR = PROJECT_ROOT / "01_data_raw" / "players"
RAW_MATCHES_DIR = PROJECT_ROOT / "01_data_raw" / "matches"


def _load_existing(name: str) -> pd.DataFrame:
    """Read entity CSV or return empty DataFrame with right columns."""
    try:
        return read_entities(name)
    except FileNotFoundError:
        return pd.DataFrame()


def extract_fbref_players() -> pd.DataFrame:
    """Pull unique players from all fbref_* season parquets.

    soccerdata does NOT expose FBref's hex player_id — we synthesize a stable
    ID from (player_name, team, nation) so the row dedups consistently across
    stat types. Real `fbref_<hex>` would need scraping player pages individually.
    """
    rows = []
    for f in sorted(RAW_PLAYERS_DIR.glob("fbref_*.parquet")):
        df = read_parquet(f)
        if "player" not in df.columns:
            continue
        keep = ["player", "team", "league", "nation", "pos", "age", "born"]
        keep = [c for c in keep if c in df.columns]
        rows.append(df[keep].assign(_source_file=f.name))

    if not rows:
        return pd.DataFrame()

    df = pd.concat(rows, ignore_index=True)
    df = df.drop_duplicates(subset=["player", "team", "nation"]).reset_index(drop=True)

    # Synthesize stable player_id: fbref_<normalized_name>_<normalized_team>
    name_n = df["player"].astype(str).map(normalize_name).str.replace(" ", "-", regex=False)
    team_n = df["team"].astype(str).map(normalize_team_name).str.replace(" ", "-", regex=False)
    synthetic_id = "fbref_" + name_n + "__" + team_n

    out = pd.DataFrame({
        "player_id":        synthetic_id,
        "name":             df["player"].astype("string"),
        "name_normalized":  df["player"].astype(str).map(normalize_name).astype("string"),
        "birth_date":       pd.Series([pd.NA] * len(df), dtype="string"),
        "nationality":      df.get("nation", pd.Series([pd.NA] * len(df))).astype("string"),
        "position":         df.get("pos", pd.Series([pd.NA] * len(df))).astype("string"),
        "foot":             pd.Series([pd.NA] * len(df), dtype="string"),
        "height_cm":        pd.Series([pd.NA] * len(df), dtype="Int16"),
        "weight_kg":        pd.Series([pd.NA] * len(df), dtype="Int16"),
        "source":           "fbref",
        "source_id":        synthetic_id.str.removeprefix("fbref_"),
    })
    return out.drop_duplicates(subset=["player_id"]).reset_index(drop=True)


def extract_fbref_teams() -> pd.DataFrame:
    """Pull unique teams from all fbref_* season parquets."""
    rows = []
    for f in sorted(RAW_PLAYERS_DIR.glob("fbref_*.parquet")):
        df = read_parquet(f)
        if "team" not in df.columns:
            continue
        keep = [c for c in ["team", "league"] if c in df.columns]
        rows.append(df[keep])
    if not rows:
        return pd.DataFrame()

    df = pd.concat(rows, ignore_index=True).drop_duplicates().reset_index(drop=True)

    # league looks like "ENG-Premier League" → "ENG"
    country_iso = df["league"].astype(str).str.split("-").str[0].str.upper()
    team_n = df["team"].astype(str).map(normalize_team_name).str.replace(" ", "-", regex=False)
    synthetic_id = "fbref_" + team_n

    out = pd.DataFrame({
        "team_id":          synthetic_id,
        "name":             df["team"].astype("string"),
        "name_normalized":  df["team"].astype(str).map(normalize_team_name).astype("string"),
        "country":          country_iso.astype("string"),
        "founded_year":     pd.Series([pd.NA] * len(df), dtype="Int16"),
        "stadium":          pd.Series([pd.NA] * len(df), dtype="string"),
        "source":           "fbref",
        "source_id":        synthetic_id.str.removeprefix("fbref_"),
    })
    return out.drop_duplicates(subset=["team_id"]).reset_index(drop=True)


def merge_dedup(existing: pd.DataFrame, new: pd.DataFrame, key: str) -> pd.DataFrame:
    """Concat and dedup on `key`, keeping first-seen row to preserve existing data."""
    if existing.empty:
        return new.copy()
    if new.empty:
        return existing.copy()
    # Align columns
    all_cols = list(dict.fromkeys(list(existing.columns) + list(new.columns)))
    existing = existing.reindex(columns=all_cols)
    new = new.reindex(columns=all_cols)
    combined = pd.concat([existing, new], ignore_index=True)
    return combined.drop_duplicates(subset=[key], keep="first").reset_index(drop=True)


def main():
    parser = argparse.ArgumentParser(description="Populate entity catalogs from raw parquets.")
    parser.add_argument("--source", choices=["fbref", "all"], default="all",
                        help="Which scraped source(s) to pull from")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print what would change, don't write")
    args = parser.parse_args()

    sources = ["fbref"] if args.source == "fbref" else ["fbref"]

    new_players = pd.concat(
        ([extract_fbref_players()] if "fbref" in sources else []),
        ignore_index=True,
    ) if sources else pd.DataFrame()

    new_teams = pd.concat(
        ([extract_fbref_teams()] if "fbref" in sources else []),
        ignore_index=True,
    ) if sources else pd.DataFrame()

    existing_players = _load_existing("players")
    existing_teams = _load_existing("teams")

    merged_players = merge_dedup(existing_players, new_players, "player_id")
    merged_teams = merge_dedup(existing_teams, new_teams, "team_id")

    print(f"players: existing={len(existing_players):>5,}  new={len(new_players):>5,}  "
          f"merged={len(merged_players):>5,}")
    print(f"teams:   existing={len(existing_teams):>5,}  new={len(new_teams):>5,}  "
          f"merged={len(merged_teams):>5,}")

    if args.dry_run:
        print("(dry-run) not writing")
        return

    write_entities(merged_players, "players")
    write_entities(merged_teams, "teams")
    print("wrote 03_entities/players.csv and teams.csv")


if __name__ == "__main__":
    main()
