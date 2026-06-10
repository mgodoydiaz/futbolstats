"""Aggregate cards, fouls, corners, throw-ins and goal kicks from StatsBomb events.

Two outputs:

    02_data_processed/events_clean/statsbomb_player_match_discipline.parquet
        One row per (player, match). Cards (Y, 2Y, R), fouls committed/drawn,
        fouls by pitch third. Direct targets for xCards and xFouls models.

    02_data_processed/events_clean/statsbomb_team_match_setpieces.parquet
        One row per (team, match). Counts of corners, throw-ins, free kicks
        and goal kicks taken (and conceded). Direct targets for xCorners /
        xThrows / xGoalKicks models.

Usage:
    python 07_features/build_discipline_setpieces.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.io import read_parquet, write_parquet  # noqa: E402

EVENTS_DIR = PROJECT_ROOT / "01_data_raw" / "events"
MATCHES_DIR = PROJECT_ROOT / "01_data_raw" / "matches"
OUT_DIR = PROJECT_ROOT / "02_data_processed" / "events_clean"

# StatsBomb pitch is 120 x 80. Thirds at x = 40 and x = 80.
DEF_THIRD = 40.0
ATT_THIRD = 80.0

DISCIPLINE_COLS = [
    "type", "player_id", "player", "team", "match_id", "competition_slug",
    "_season", "location",
    "foul_committed_card", "foul_committed_advantage",
    "bad_behaviour_card",
]
SET_PIECE_COLS = [
    "type", "team", "match_id", "competition_slug", "_season",
    "pass_type",
]


def _season_from_filename(path: Path) -> str:
    """Extract season tag from a statsbomb_<comp>_<season>.parquet filename."""
    stem = path.stem  # statsbomb_UEFAEuro_2024
    # last underscore-separated token holds the season label
    return stem.rsplit("_", 1)[-1]


def _read_events(path: Path, cols: list[str]) -> pd.DataFrame:
    """Read an events parquet, projecting only existing columns. Adds _season."""
    df = read_parquet(path)
    keep = [c for c in cols if c in df.columns and c != "_season"]
    out = df[keep].copy()
    out["_season"] = _season_from_filename(path)
    return out


def _third_from_location(loc) -> str:
    """Classify pitch third from a StatsBomb location [x, y]."""
    if not isinstance(loc, (list, tuple)) or len(loc) < 1:
        return "unknown"
    x = loc[0]
    if x is None:
        return "unknown"
    if x < DEF_THIRD:
        return "def"
    if x < ATT_THIRD:
        return "mid"
    return "att"


def aggregate_discipline() -> pd.DataFrame:
    """Per-player-per-match cards, fouls and discipline location."""
    parts = []
    for f in sorted(EVENTS_DIR.glob("statsbomb_*.parquet")):
        df = _read_events(f, DISCIPLINE_COLS)
        if df.empty:
            continue
        # foul committed events (drives cards via foul_committed_card)
        foul_c = df[df["type"] == "Foul Committed"].copy()
        if not foul_c.empty:
            foul_c["third"] = foul_c["location"].apply(_third_from_location)
        # foul won events (drawn fouls)
        foul_w = df[df["type"] == "Foul Won"]
        # standalone bad behaviour (dissent etc; card without foul)
        bb = df[df["type"] == "Bad Behaviour"]
        parts.append({
            "foul_c": foul_c,
            "foul_w": foul_w,
            "bb": bb,
            "source_file": f.name,
        })

    if not parts:
        return pd.DataFrame()

    fc = pd.concat([p["foul_c"] for p in parts], ignore_index=True)
    fw = pd.concat([p["foul_w"] for p in parts], ignore_index=True)
    bb = pd.concat([p["bb"] for p in parts], ignore_index=True)

    # ----- card flags from Foul Committed -----
    fc["yellow_from_foul"] = (fc["foul_committed_card"] == "Yellow Card").astype("Int16")
    fc["second_yellow"] = (fc["foul_committed_card"] == "Second Yellow").astype("Int16")
    fc["red_from_foul"] = (fc["foul_committed_card"] == "Red Card").astype("Int16")

    # fouls by third
    fc["foul_def"] = (fc["third"] == "def").astype("Int16")
    fc["foul_mid"] = (fc["third"] == "mid").astype("Int16")
    fc["foul_att"] = (fc["third"] == "att").astype("Int16")

    fc_agg = fc.groupby(["player_id", "player", "team", "match_id", "competition_slug", "_season"], dropna=False).agg(
        fouls_committed=("type", "size"),
        yellow_cards=("yellow_from_foul", "sum"),
        second_yellows=("second_yellow", "sum"),
        red_cards=("red_from_foul", "sum"),
        fouls_committed_def_third=("foul_def", "sum"),
        fouls_committed_mid_third=("foul_mid", "sum"),
        fouls_committed_att_third=("foul_att", "sum"),
    ).reset_index()

    fw_agg = fw.groupby(["player_id", "player", "team", "match_id", "competition_slug", "_season"], dropna=False).agg(
        fouls_drawn=("type", "size"),
    ).reset_index()

    # ----- standalone bad-behaviour cards -----
    if not bb.empty and "bad_behaviour_card" in bb.columns:
        bb["yellow_bb"] = (bb["bad_behaviour_card"] == "Yellow Card").astype("Int16")
        bb["red_bb"] = (bb["bad_behaviour_card"] == "Red Card").astype("Int16")
        bb_agg = bb.groupby(["player_id", "player", "team", "match_id", "competition_slug", "_season"], dropna=False).agg(
            yellow_cards_bb=("yellow_bb", "sum"),
            red_cards_bb=("red_bb", "sum"),
        ).reset_index()
    else:
        bb_agg = pd.DataFrame(columns=[
            "player_id", "player", "team", "match_id", "competition_slug", "_season",
            "yellow_cards_bb", "red_cards_bb",
        ])

    key = ["player_id", "player", "team", "match_id", "competition_slug", "_season"]
    merged = fc_agg.merge(fw_agg, on=key, how="outer").merge(bb_agg, on=key, how="outer")
    for c in [
        "fouls_committed", "yellow_cards", "second_yellows", "red_cards",
        "fouls_committed_def_third", "fouls_committed_mid_third", "fouls_committed_att_third",
        "fouls_drawn", "yellow_cards_bb", "red_cards_bb",
    ]:
        if c in merged.columns:
            merged[c] = merged[c].fillna(0).astype("Int16")

    # consolidate total yellow / red counts across both sources
    merged["yellow_total"] = (
        merged.get("yellow_cards", 0).fillna(0) +
        merged.get("yellow_cards_bb", 0).fillna(0)
    ).astype("Int16")
    merged["red_total"] = (
        merged.get("red_cards", 0).fillna(0) +
        merged.get("red_cards_bb", 0).fillna(0)
    ).astype("Int16")
    return merged


def aggregate_setpieces() -> pd.DataFrame:
    """Per-team-per-match corners, throw-ins, free kicks and goal kicks (for and against)."""
    rows = []
    for f in sorted(EVENTS_DIR.glob("statsbomb_*.parquet")):
        df = _read_events(f, SET_PIECE_COLS)
        if df.empty:
            continue
        # only Pass events carry pass_type for corner/throw-in/free kick/goal kick
        passes = df[df["type"] == "Pass"].copy()
        if passes.empty:
            continue
        # count by team
        for sp_label, sp_value in [
            ("corners", "Corner"),
            ("throw_ins", "Throw-in"),
            ("free_kicks", "Free Kick"),
            ("goal_kicks", "Goal Kick"),
            ("kick_offs", "Kick Off"),
        ]:
            sub = passes[passes["pass_type"] == sp_value]
            if sub.empty:
                continue
            agg = sub.groupby(["match_id", "team", "competition_slug", "_season"], dropna=False).size()
            for (mid, team, comp, season), n in agg.items():
                rows.append({
                    "match_id": mid, "team": team, "competition_slug": comp, "_season": season,
                    "stat": sp_label, "count": int(n),
                })

    if not rows:
        return pd.DataFrame()

    long_df = pd.DataFrame(rows)
    wide = long_df.pivot_table(
        index=["match_id", "team", "competition_slug", "_season"],
        columns="stat", values="count", aggfunc="sum", fill_value=0,
    ).reset_index()
    wide.columns.name = None
    return wide


def attach_opponent(team_match_df: pd.DataFrame) -> pd.DataFrame:
    """Add `_against` columns by self-joining on match_id with opposite team."""
    if team_match_df.empty:
        return team_match_df
    me = team_match_df.copy()
    them = team_match_df.copy().rename(columns={c: f"{c}_against" for c in team_match_df.columns if c not in ("match_id", "competition_slug", "_season")})
    them = them.rename(columns={"team_against": "team_them"})
    merged = me.merge(them[[c for c in them.columns if c == "match_id" or c.endswith("_against") or c == "team_them"]], on="match_id", how="left")
    # keep only rows where them != me
    merged = merged[merged["team"] != merged["team_them"]].drop(columns=["team_them"])
    return merged


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("[discipline] aggregating cards / fouls from events ...")
    disc = aggregate_discipline()
    if disc.empty:
        print("  no events found, skipping discipline output")
    else:
        out = OUT_DIR / "statsbomb_player_match_discipline.parquet"
        write_parquet(disc, out)
        print(f"  wrote {len(disc):,} rows x {len(disc.columns)} cols -> {out.relative_to(PROJECT_ROOT)}")
        print(f"  totals: yellow={int(disc['yellow_total'].sum())}  "
              f"second_yellow={int(disc['second_yellows'].sum())}  "
              f"red={int(disc['red_total'].sum())}  "
              f"fouls_committed={int(disc['fouls_committed'].sum())}  "
              f"fouls_drawn={int(disc['fouls_drawn'].sum())}")

    print()
    print("[setpieces] aggregating corners / throw-ins / free kicks / goal kicks ...")
    sp = aggregate_setpieces()
    if sp.empty:
        print("  no events found, skipping setpieces output")
    else:
        sp_with_against = attach_opponent(sp)
        out = OUT_DIR / "statsbomb_team_match_setpieces.parquet"
        write_parquet(sp_with_against, out)
        print(f"  wrote {len(sp_with_against):,} rows x {len(sp_with_against.columns)} cols -> {out.relative_to(PROJECT_ROOT)}")
        for c in ("corners", "throw_ins", "free_kicks", "goal_kicks"):
            if c in sp.columns:
                print(f"  total {c:<11s}: {int(sp[c].sum()):,}")


if __name__ == "__main__":
    main()
