"""Aggregate StatsBomb events into per-player-per-match stats.

Reads the events parquet(s) produced by statsbomb_loader.py and rolls them up
to the schema in `lib/schemas.py` → PLAYER_MATCH_STATS, plus a few extra
StatsBomb-only fields (xG sum, key_passes, dribbles_completed, etc.).

Usage:
    # All loaded competitions
    python 06_ingestion/statsbomb_aggregate.py

    # Specific competition file(s)
    python 06_ingestion/statsbomb_aggregate.py --file statsbomb_FIFAWorldCup_2022

    # Append vs overwrite (default = replace by competition_slug+season_slug)
    python 06_ingestion/statsbomb_aggregate.py --mode append

Output:
    02_data_processed/events_clean/statsbomb_player_match.parquet
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.io import read_parquet, write_parquet  # noqa: E402

EVENTS_DIR = PROJECT_ROOT / "01_data_raw" / "events"
MATCHES_DIR = PROJECT_ROOT / "01_data_raw" / "matches"
OUT_PATH = PROJECT_ROOT / "02_data_processed" / "events_clean" / "statsbomb_player_match.parquet"

# Outcomes considered as "on target" — Goal & Saved (also Saved To Post in newer data).
ON_TARGET_OUTCOMES = {"Goal", "Saved", "Saved to Post", "Saved Off Target"}


# --------------------------------------------------------------------------
# Minutes played — parsed from the `tactics` and `substitution` events
# --------------------------------------------------------------------------

def _parse_tactics_starters(tactics_value) -> list[int]:
    """`tactics` is a JSON string (we serialized lists/dicts in the loader)
    containing a list of {'player': {'id': ..., 'name': ...}, 'position': ...}
    """
    if tactics_value is None or (isinstance(tactics_value, float) and pd.isna(tactics_value)):
        return []
    if isinstance(tactics_value, str):
        try:
            d = json.loads(tactics_value)
        except Exception:
            return []
    else:
        d = tactics_value
    # tactics shape: {'formation': ..., 'lineup': [{'player': {'id':..}, ...}, ...]}
    if isinstance(d, dict):
        lineup = d.get("lineup", [])
    else:
        lineup = d if isinstance(d, list) else []
    ids: list[int] = []
    for entry in lineup or []:
        pl = (entry or {}).get("player") if isinstance(entry, dict) else None
        if isinstance(pl, dict) and pl.get("id") is not None:
            try:
                ids.append(int(pl["id"]))
            except (TypeError, ValueError):
                pass
    return ids


def compute_minutes_played(events: pd.DataFrame) -> pd.DataFrame:
    """Return DataFrame[match_id, player_id, minutes_played].

    Convention: starters in the Starting XI come on at 0:00 and stay until they
    are substituted off OR until the final whistle (max minute observed for
    that match — captures stoppage time).
    """
    if len(events) == 0:
        return pd.DataFrame(columns=["match_id", "player_id", "minutes_played"])

    # ----- final-whistle minute per match (largest minute we observe) -----
    final_min = events.groupby("match_id")["minute"].max().rename("final_minute")

    # ----- starters: from "Starting XI" events -----
    starts_rows = []
    starting = events[events["type"] == "Starting XI"][["match_id", "team_id", "tactics"]]
    for _, r in starting.iterrows():
        for pid in _parse_tactics_starters(r["tactics"]):
            starts_rows.append({"match_id": r["match_id"], "player_id": pid, "on_min": 0})
    starts_df = pd.DataFrame(starts_rows)

    # ----- subs in (via Substitution event 'substitution_replacement_id') -----
    subs = events[events["type"] == "Substitution"].copy()
    sub_rows = []
    for _, r in subs.iterrows():
        # off player = `player_id` on the Substitution event; on player = `substitution_replacement_id`
        off_pid = r.get("player_id")
        in_pid = r.get("substitution_replacement_id")
        mid = r["match_id"]
        minute = r["minute"]
        if pd.notna(off_pid):
            sub_rows.append({"match_id": mid, "player_id": int(off_pid), "off_min": int(minute)})
        if pd.notna(in_pid):
            sub_rows.append({"match_id": mid, "player_id": int(in_pid), "on_min": int(minute)})
    subs_df = pd.DataFrame(sub_rows)

    # Combine: all (match,player) we know about
    all_pairs: list[pd.DataFrame] = []
    if len(starts_df) > 0:
        all_pairs.append(starts_df[["match_id", "player_id", "on_min"]])
    if len(subs_df) > 0:
        if "on_min" in subs_df.columns:
            all_pairs.append(subs_df.dropna(subset=["on_min"])[["match_id", "player_id", "on_min"]])
    if not all_pairs:
        return pd.DataFrame(columns=["match_id", "player_id", "minutes_played"])

    on_df = pd.concat(all_pairs, ignore_index=True)
    # If we ever see a player twice (starter who is also "swapped in" on a tactical shift), keep earliest.
    on_df = on_df.sort_values(["match_id", "player_id", "on_min"]).drop_duplicates(
        subset=["match_id", "player_id"], keep="first"
    )

    # Off minutes
    if len(subs_df) > 0 and "off_min" in subs_df.columns:
        off_df = subs_df.dropna(subset=["off_min"])[["match_id", "player_id", "off_min"]]
        off_df = off_df.sort_values(["match_id", "player_id", "off_min"]).drop_duplicates(
            subset=["match_id", "player_id"], keep="first"
        )
    else:
        off_df = pd.DataFrame(columns=["match_id", "player_id", "off_min"])

    merged = on_df.merge(off_df, on=["match_id", "player_id"], how="left")
    merged = merged.merge(final_min.reset_index(), on="match_id", how="left")
    # If never substituted off, played until final_minute.
    merged["off_min_filled"] = merged["off_min"].fillna(merged["final_minute"])
    merged["minutes_played"] = (merged["off_min_filled"] - merged["on_min"]).clip(lower=0)
    return merged[["match_id", "player_id", "minutes_played"]]


# --------------------------------------------------------------------------
# Player-match aggregation
# --------------------------------------------------------------------------

def aggregate_events(events: pd.DataFrame, matches: pd.DataFrame) -> pd.DataFrame:
    """Aggregate event-level rows into one row per (match_id, player_id).

    Returns a DataFrame matching PLAYER_MATCH_STATS plus StatsBomb extras.
    """
    if len(events) == 0:
        return pd.DataFrame()

    # Keep only events tied to a real player (drops Starting XI, Half Start, etc.)
    df = events.dropna(subset=["player_id"]).copy()
    df["player_id"] = df["player_id"].astype("int64")
    df["match_id"] = df["match_id"].astype("int64")
    df["team_id"] = df["team_id"].astype("int64")

    # ----- per-type counts -----
    # Some loader runs stringified bool columns ('True'/'False'/'<NA>') — normalize.
    def _to_bool(s: pd.Series) -> pd.Series:
        if pd.api.types.is_bool_dtype(s):
            return s.fillna(False)
        if pd.api.types.is_numeric_dtype(s):
            return s.fillna(0).astype(bool)
        # string or object: True iff exactly the string "True" (StatsBomb only emits True for these flags)
        return s.astype("string").eq("True").fillna(False)

    is_pass = df["type"] == "Pass"
    is_shot = df["type"] == "Shot"
    is_dribble = df["type"] == "Dribble"
    is_interception = df["type"] == "Interception"
    is_foul_committed = df["type"] == "Foul Committed"
    is_foul_won = df["type"] == "Foul Won"

    pass_shot_assist = _to_bool(df.get("pass_shot_assist", pd.Series(False, index=df.index)))
    pass_goal_assist = _to_bool(df.get("pass_goal_assist", pd.Series(False, index=df.index)))

    df["passes_attempted"] = is_pass.astype("int16")
    df["passes_completed"] = (is_pass & df["pass_outcome"].isna()).astype("int16")
    df["key_passes"] = (is_pass & (pass_shot_assist | pass_goal_assist)).astype("int16")
    df["assists"] = (is_pass & pass_goal_assist).astype("int16")
    df["shots"] = is_shot.astype("int16")
    df["shots_on_target"] = (is_shot & df["shot_outcome"].isin(ON_TARGET_OUTCOMES)).astype("int16")
    df["goals"] = (is_shot & (df["shot_outcome"] == "Goal")).astype("int16")
    df["xg"] = pd.to_numeric(df["shot_statsbomb_xg"], errors="coerce").fillna(0.0)
    df["dribbles_attempted"] = is_dribble.astype("int16")
    df["dribbles_completed"] = (is_dribble & (df["dribble_outcome"] == "Complete")).astype("int16")
    # Tackles in StatsBomb live in the Duel event with duel_type == "Tackle"
    is_tackle = (df["type"] == "Duel") & (df["duel_type"] == "Tackle")
    df["tackles"] = is_tackle.astype("int16")
    df["interceptions"] = is_interception.astype("int16")
    df["fouls_committed"] = is_foul_committed.astype("int16")
    df["fouls_drawn"] = is_foul_won.astype("int16")

    agg_cols = [
        "passes_attempted", "passes_completed", "key_passes", "assists",
        "shots", "shots_on_target", "goals", "xg",
        "dribbles_attempted", "dribbles_completed",
        "tackles", "interceptions",
        "fouls_committed", "fouls_drawn",
    ]
    grouped = (
        df.groupby(["match_id", "player_id"], as_index=False)
          .agg({c: "sum" for c in agg_cols})
    )

    # team_id and player name per (match, player) — take the modal value.
    meta = (
        df.groupby(["match_id", "player_id"], as_index=False)
          .agg(team_id=("team_id", "first"), player_name=("player", "first"), team_name=("team", "first"))
    )
    grouped = grouped.merge(meta, on=["match_id", "player_id"])

    # ---- minutes_played ----
    minutes = compute_minutes_played(events)
    if len(minutes) > 0:
        minutes["match_id"] = minutes["match_id"].astype("int64")
        minutes["player_id"] = minutes["player_id"].astype("int64")
        grouped = grouped.merge(minutes, on=["match_id", "player_id"], how="left")
    else:
        grouped["minutes_played"] = pd.NA

    # ---- enrich from matches table ----
    if matches is not None and len(matches) > 0:
        m = matches[[
            "match_id", "match_date", "season_slug", "competition_slug",
            "home_team_id", "away_team_id", "home_team", "away_team",
        ]].copy()
        m["match_id"] = m["match_id"].astype("int64")
        m["home_team_id"] = m["home_team_id"].astype("int64")
        m["away_team_id"] = m["away_team_id"].astype("int64")
        grouped = grouped.merge(m, on="match_id", how="left")

        grouped["is_home"] = grouped["team_id"] == grouped["home_team_id"]
        grouped["opponent_id"] = grouped.apply(
            lambda r: r["away_team_id"] if r["is_home"] else r["home_team_id"], axis=1
        )

    # ---- canonical IDs ----
    grouped["player_id_sb"] = grouped["player_id"].astype("Int64")
    grouped["team_id_sb"] = grouped["team_id"].astype("Int64")
    grouped["player_id"] = "sb_" + grouped["player_id"].astype(str)
    grouped["team_id"] = "sb_" + grouped["team_id"].astype(str)
    grouped["opponent_id"] = grouped["opponent_id"].apply(
        lambda x: f"sb_{int(x)}" if pd.notna(x) else pd.NA
    )
    grouped["match_id"] = "sb_" + grouped["match_id"].astype(str)
    grouped["competition_id"] = "sb_" + matches["competition_id"].astype(str).iloc[0] if (
        matches is not None and len(matches) > 0
    ) else pd.NA
    grouped["season"] = grouped["season_slug"]
    grouped["date"] = grouped["match_date"].astype(str) if "match_date" in grouped.columns else pd.NA

    # ---- dtype shrink ----
    int_cols = [
        "passes_attempted", "passes_completed", "key_passes", "assists",
        "shots", "shots_on_target", "goals",
        "dribbles_attempted", "dribbles_completed",
        "tackles", "interceptions",
        "fouls_committed", "fouls_drawn",
    ]
    for c in int_cols:
        if c in grouped.columns:
            grouped[c] = grouped[c].astype("Int16")
    if "minutes_played" in grouped.columns:
        grouped["minutes_played"] = pd.to_numeric(grouped["minutes_played"], errors="coerce").astype("Int16")
    if "xg" in grouped.columns:
        grouped["xg"] = grouped["xg"].astype("float32")
    if "is_home" in grouped.columns:
        grouped["is_home"] = grouped["is_home"].astype("boolean")

    # ---- final column order ----
    preferred = [
        "player_id", "match_id", "team_id", "opponent_id",
        "competition_id", "season", "date", "is_home",
        "minutes_played", "goals", "assists",
        "shots", "shots_on_target", "xg",
        "passes_attempted", "passes_completed", "key_passes",
        "dribbles_attempted", "dribbles_completed",
        "tackles", "interceptions",
        "fouls_committed", "fouls_drawn",
        "player_name", "team_name", "competition_slug",
        "player_id_sb", "team_id_sb",
    ]
    keep = [c for c in preferred if c in grouped.columns]
    return grouped[keep]


# --------------------------------------------------------------------------
# Discovery & I/O
# --------------------------------------------------------------------------

def list_event_files() -> list[Path]:
    return sorted(EVENTS_DIR.glob("statsbomb_*.parquet"))


def matches_path_for(events_path: Path) -> Path:
    """events file 'statsbomb_FIFAWorldCup_2022.parquet' -> matches file with same tag."""
    return MATCHES_DIR / events_path.name


def main():
    p = argparse.ArgumentParser(description="Aggregate StatsBomb events into per-player-per-match stats.")
    p.add_argument(
        "--file", "-f", action="append", default=[],
        help="Specific event parquet stem (without extension), e.g. statsbomb_FIFAWorldCup_2022. Repeatable.",
    )
    p.add_argument(
        "--mode", choices=["replace", "append"], default="replace",
        help="`replace` (default) overwrites rows for the same (competition_slug, season) keys. "
             "`append` adds without dedup.",
    )
    args = p.parse_args()

    if args.file:
        files = []
        for stem in args.file:
            stem = stem if stem.endswith(".parquet") else f"{stem}.parquet"
            candidate = EVENTS_DIR / stem
            if not candidate.exists():
                print(f"[warn] not found: {candidate}")
                continue
            files.append(candidate)
    else:
        files = list_event_files()

    if not files:
        print("[statsbomb-agg] no event files to aggregate. Run statsbomb_loader.py first.")
        return

    print(f"[statsbomb-agg] processing {len(files)} event file(s):")
    for f in files:
        print(f"  - {f.name}")

    out_frames: list[pd.DataFrame] = []
    for f in files:
        print(f"\n[agg] {f.name}")
        events = read_parquet(f)
        m_path = matches_path_for(f)
        matches = read_parquet(m_path) if m_path.exists() else None
        agg = aggregate_events(events, matches)
        print(f"  -> {len(agg):,} player-match rows")
        out_frames.append(agg)

    new_df = pd.concat(out_frames, ignore_index=True, sort=False) if out_frames else pd.DataFrame()

    # Merge with existing if present
    if OUT_PATH.exists():
        existing = read_parquet(OUT_PATH)
        if args.mode == "replace":
            # Drop existing rows that come from any (competition_slug, season) we just produced
            keys = (
                new_df[["competition_slug", "season"]]
                .drop_duplicates()
                .apply(lambda r: (r["competition_slug"], r["season"]), axis=1)
                .tolist()
            )
            mask = existing.apply(
                lambda r: (r.get("competition_slug"), r.get("season")) not in keys, axis=1
            )
            existing = existing[mask]
        combined = pd.concat([existing, new_df], ignore_index=True, sort=False)
    else:
        combined = new_df

    write_parquet(combined, OUT_PATH)
    size_mb = OUT_PATH.stat().st_size / 1024 / 1024
    print(f"\n[statsbomb-agg] wrote {len(combined):,} rows -> {OUT_PATH.relative_to(PROJECT_ROOT)} "
          f"({size_mb:.2f} MB)")

    # Quick sanity print
    print("\n[sanity] top 5 pass-completers across all loaded data:")
    top = (
        combined.groupby("player_name", as_index=False)["passes_completed"]
                .sum()
                .sort_values("passes_completed", ascending=False)
                .head(5)
    )
    for _, r in top.iterrows():
        print(f"  {r['player_name']:<35s} {int(r['passes_completed']):>5,}")

    print("\n[sanity] top 5 xG generators across all loaded data:")
    top_xg = (
        combined.groupby("player_name", as_index=False)["xg"]
                .sum()
                .sort_values("xg", ascending=False)
                .head(5)
    )
    for _, r in top_xg.iterrows():
        print(f"  {r['player_name']:<35s} {float(r['xg']):>6.2f}")


if __name__ == "__main__":
    main()
