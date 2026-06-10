"""Append unique players and teams discovered in StatsBomb data to the entity catalogs.

Run after `statsbomb_loader.py` (and ideally `statsbomb_aggregate.py`).
Reads every lineups/events/matches parquet under 01_data_raw/, collects unique
players + teams, and appends new rows to 03_entities/{players,teams}.csv.

Append-only by `player_id` / `team_id` — existing rows (from fbref or other
sources) are never overwritten.

Usage:
    python 06_ingestion/statsbomb_entities.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.io import read_entities, read_parquet, write_entities  # noqa: E402
from lib.text import normalize_name, normalize_team_name  # noqa: E402

LINEUPS_DIR = PROJECT_ROOT / "01_data_raw" / "lineups"
MATCHES_DIR = PROJECT_ROOT / "01_data_raw" / "matches"


def collect_players_from_lineups() -> pd.DataFrame:
    files = sorted(LINEUPS_DIR.glob("statsbomb_*.parquet"))
    frames = []
    for f in files:
        df = read_parquet(f, columns=["player_id", "player_name", "player_nickname", "country"])
        frames.append(df)
    if not frames:
        return pd.DataFrame(columns=["player_id", "name", "name_normalized", "nationality"])
    all_p = pd.concat(frames, ignore_index=True)
    # Keep first appearance per player_id
    all_p = all_p.dropna(subset=["player_id"]).drop_duplicates(subset=["player_id"], keep="first")
    n = len(all_p)
    all_p = all_p.reset_index(drop=True)
    out = pd.DataFrame({
        "player_id": ("sb_" + all_p["player_id"].astype("Int64").astype("string")).values,
        "name": all_p["player_name"].astype("string").values,
        "name_normalized": all_p["player_name"].apply(normalize_name).astype("string").values,
        "birth_date": pd.Series([pd.NA] * n, dtype="string"),
        # `country` in StatsBomb lineups is a free-form country name — keep as-is.
        # We don't try to map to ISO alpha-3 here; that's a separate enrichment step.
        "nationality": all_p["country"].astype("string").values,
        "position": pd.Series([pd.NA] * n, dtype="string"),
        "foot": pd.Series([pd.NA] * n, dtype="string"),
        "height_cm": pd.Series([pd.NA] * n, dtype="Int16"),
        "weight_kg": pd.Series([pd.NA] * n, dtype="Int16"),
        "source": pd.Series(["statsbomb"] * n, dtype="string"),
        "source_id": all_p["player_id"].astype("Int64").astype("string").values,
    })
    return out


def collect_teams_from_matches() -> pd.DataFrame:
    files = sorted(MATCHES_DIR.glob("statsbomb_*.parquet"))
    rows: list[dict] = []
    for f in files:
        df = read_parquet(
            f,
            columns=[
                "home_team_id", "home_team", "home_team_country_name",
                "away_team_id", "away_team", "away_team_country_name",
            ],
        )
        for _, r in df.iterrows():
            rows.append({
                "team_id_raw": r["home_team_id"],
                "name": r["home_team"],
                "country": r["home_team_country_name"],
            })
            rows.append({
                "team_id_raw": r["away_team_id"],
                "name": r["away_team"],
                "country": r["away_team_country_name"],
            })
    if not rows:
        return pd.DataFrame(columns=["team_id", "name", "name_normalized", "country", "source", "source_id"])
    teams = pd.DataFrame(rows)
    teams = teams.dropna(subset=["team_id_raw"]).drop_duplicates(subset=["team_id_raw"], keep="first")
    n = len(teams)
    teams = teams.reset_index(drop=True)
    out = pd.DataFrame({
        "team_id": ("sb_" + teams["team_id_raw"].astype("Int64").astype("string")).values,
        "name": teams["name"].astype("string").values,
        "name_normalized": teams["name"].apply(normalize_team_name).astype("string").values,
        "country": teams["country"].astype("string").values,  # free-form name — same caveat as players
        "founded_year": pd.Series([pd.NA] * n, dtype="Int16"),
        "stadium": pd.Series([pd.NA] * n, dtype="string"),
        "source": pd.Series(["statsbomb"] * n, dtype="string"),
        "source_id": teams["team_id_raw"].astype("Int64").astype("string").values,
    })
    return out


def append_only(existing: pd.DataFrame, new_rows: pd.DataFrame, id_col: str) -> tuple[pd.DataFrame, int]:
    """Return (combined_df, num_added). Skip rows whose id already exists."""
    if existing.empty:
        return new_rows.copy(), len(new_rows)
    existing_ids = set(existing[id_col].dropna().astype(str).tolist())
    novel = new_rows[~new_rows[id_col].astype(str).isin(existing_ids)]
    if novel.empty:
        return existing, 0
    combined = pd.concat([existing, novel], ignore_index=True, sort=False)
    return combined, len(novel)


def main():
    print("[entities] reading existing catalogs...")
    players_existing = read_entities("players")
    teams_existing = read_entities("teams")
    print(f"  players: {len(players_existing)} existing rows")
    print(f"  teams  : {len(teams_existing)} existing rows")

    print("\n[entities] scanning statsbomb lineups for players...")
    new_players = collect_players_from_lineups()
    print(f"  found {len(new_players)} unique statsbomb player_ids")

    print("\n[entities] scanning statsbomb matches for teams...")
    new_teams = collect_teams_from_matches()
    print(f"  found {len(new_teams)} unique statsbomb team_ids")

    # Align columns to existing schema (existing may have come from another source).
    if not players_existing.empty:
        for col in players_existing.columns:
            if col not in new_players.columns:
                new_players[col] = pd.NA
        new_players = new_players[players_existing.columns]
    if not teams_existing.empty:
        for col in teams_existing.columns:
            if col not in new_teams.columns:
                new_teams[col] = pd.NA
        new_teams = new_teams[teams_existing.columns]

    players_combined, added_p = append_only(players_existing, new_players, "player_id")
    teams_combined, added_t = append_only(teams_existing, new_teams, "team_id")

    write_entities(players_combined, "players")
    write_entities(teams_combined, "teams")

    print(f"\n[entities] wrote 03_entities/players.csv  (+{added_p} new, {len(players_combined)} total)")
    print(f"[entities] wrote 03_entities/teams.csv    (+{added_t} new, {len(teams_combined)} total)")


if __name__ == "__main__":
    main()
