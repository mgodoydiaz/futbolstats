"""Aggregate per-goalkeeper-per-match stats from StatsBomb events.

GK-specific targets that the generic player_match table does not capture:

    saves              total Shot Saved + Shot Saved to Post + Shot Saved Off Target + Save
    penalty_saves      Penalty Saved + Penalty Saved to Post
    goals_against      Goal Conceded events
    punches            Punch events
    claims             Collected events with outcome Claim or NaN
    sweeper_actions    Keeper Sweeper events
    shots_faced        Shot Faced events (total exposure)
    save_pct           saves / max(1, shots_faced)   (post-hoc derived metric)

Output:
    02_data_processed/events_clean/statsbomb_gk_match.parquet

Usage:
    python 07_features/build_gk_match.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.io import read_parquet, write_parquet  # noqa: E402

EVENTS_DIR = PROJECT_ROOT / "01_data_raw" / "events"
PLAYER_MATCH = PROJECT_ROOT / "02_data_processed" / "events_clean" / "statsbomb_player_match.parquet"
OUT = PROJECT_ROOT / "02_data_processed" / "events_clean" / "statsbomb_gk_match.parquet"

SAVE_TYPES = {
    "Shot Saved", "Shot Saved to Post", "Shot Saved Off Target", "Save",
}
PENALTY_SAVE_TYPES = {"Penalty Saved", "Penalty Saved to Post"}
GOAL_AGAINST_TYPE = "Goal Conceded"
PUNCH_TYPE = "Punch"
CLAIM_TYPE = "Collected"
SWEEPER_TYPE = "Keeper Sweeper"
SHOT_FACED_TYPE = "Shot Faced"


def _season_from_filename(path: Path) -> str:
    return path.stem.rsplit("_", 1)[-1]


def _prefix_id(s) -> pd.Series:
    s = pd.Series(s).astype(str).str.replace(r"\.0$", "", regex=True)
    return s.where(s.str.startswith("sb_"), "sb_" + s)


def aggregate_gk() -> pd.DataFrame:
    parts = []
    for f in sorted(EVENTS_DIR.glob("statsbomb_*.parquet")):
        df = read_parquet(
            f,
            columns=["type", "player_id", "match_id", "team", "goalkeeper_type"],
        )
        gk = df[df["type"] == "Goal Keeper"].copy()
        gk = gk.dropna(subset=["player_id", "goalkeeper_type"])
        if gk.empty:
            continue

        gk["is_save"] = gk["goalkeeper_type"].isin(SAVE_TYPES).astype("Int16")
        gk["is_penalty_save"] = gk["goalkeeper_type"].isin(PENALTY_SAVE_TYPES).astype("Int16")
        gk["is_goal_against"] = (gk["goalkeeper_type"] == GOAL_AGAINST_TYPE).astype("Int16")
        gk["is_punch"] = (gk["goalkeeper_type"] == PUNCH_TYPE).astype("Int16")
        gk["is_claim"] = (gk["goalkeeper_type"] == CLAIM_TYPE).astype("Int16")
        gk["is_sweeper"] = (gk["goalkeeper_type"] == SWEEPER_TYPE).astype("Int16")
        gk["is_shot_faced"] = (gk["goalkeeper_type"] == SHOT_FACED_TYPE).astype("Int16")

        agg = gk.groupby(["match_id", "player_id", "team"], dropna=False).agg(
            saves=("is_save", "sum"),
            penalty_saves=("is_penalty_save", "sum"),
            goals_against=("is_goal_against", "sum"),
            punches=("is_punch", "sum"),
            claims=("is_claim", "sum"),
            sweeper_actions=("is_sweeper", "sum"),
            shots_faced=("is_shot_faced", "sum"),
        ).reset_index()
        agg["_season"] = _season_from_filename(f)
        agg["competition_slug"] = f.stem.split("_")[1]
        parts.append(agg)
        print(f"  {f.name}: {len(agg):,} GK-match rows")

    if not parts:
        return pd.DataFrame()
    out = pd.concat(parts, ignore_index=True)
    out["save_pct"] = (
        out["saves"].astype(float) / out["shots_faced"].replace(0, pd.NA).astype(float)
    ).fillna(0.0).astype("Float32")
    return out


def main():
    print("[gk-match] aggregating goalkeeper events ...")
    gk = aggregate_gk()
    if gk.empty:
        print("  no GK events found")
        return

    # normalize keys for join with player_match
    gk["match_id"] = _prefix_id(gk["match_id"]).values
    gk["player_id"] = _prefix_id(gk["player_id"]).values

    # join date and minutes_played from player_match (so we can build features)
    pm = read_parquet(PLAYER_MATCH, columns=["match_id", "player_id", "date", "minutes_played", "is_home"])
    pm["match_id"] = _prefix_id(pm["match_id"]).values
    pm["player_id"] = _prefix_id(pm["player_id"]).values
    gk_enriched = gk.merge(pm, on=["match_id", "player_id"], how="left")

    write_parquet(gk_enriched, OUT)
    print(f"  wrote {len(gk_enriched):,} GK-match rows x {len(gk_enriched.columns)} cols")
    print(f"  -> {OUT.relative_to(PROJECT_ROOT)}")
    print()
    print("Stat totals across all loaded competitions:")
    for c in ("saves", "penalty_saves", "goals_against", "punches", "claims",
              "sweeper_actions", "shots_faced"):
        print(f"  {c:<18s}: {int(gk_enriched[c].sum()):,}")
    print(f"  avg save_pct       : {gk_enriched['save_pct'].mean():.3f}")
    print(f"  avg shots_faced/m  : {gk_enriched['shots_faced'].mean():.2f}")


if __name__ == "__main__":
    main()
