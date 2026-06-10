"""Download and cache StatsBomb Open Data: matches, events, lineups.

StatsBomb publishes free event-level football data on GitHub. We pull through
the `statsbombpy` package, which fetches & caches the raw JSON for us. If
statsbombpy is missing or fails, we fall back to direct GitHub raw downloads.

Usage:
    # List everything available
    python 06_ingestion/statsbomb_loader.py --list

    # Load by name (matches `competition_name`, case-insensitive, partial OK)
    python 06_ingestion/statsbomb_loader.py --competition "FIFA World Cup" --season 2022

    # Load by numeric IDs
    python 06_ingestion/statsbomb_loader.py --competition 43 --season 106

    # Multiple competitions, all available seasons
    python 06_ingestion/statsbomb_loader.py --competition "UEFA Euro" --competition "FIFA World Cup"

Output (paths relative to project root):
    01_data_raw/matches/statsbomb_<comp>_<season>.parquet
    01_data_raw/events/statsbomb_<comp>_<season>.parquet
    01_data_raw/lineups/statsbomb_<comp>_<season>.parquet
    01_data_raw/_cache/statsbomb/                  (raw JSON cache, gitignored)

Attribution required:
    Data provided by StatsBomb under their open data license. See
    https://github.com/statsbomb/open-data for terms.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import warnings
from pathlib import Path
from typing import Any

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Point statsbombpy at our project-local cache before importing it.
CACHE_DIR = PROJECT_ROOT / "01_data_raw" / "_cache" / "statsbomb"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("STATSBOMBPY_CACHE_DIR", str(CACHE_DIR))

# Silence the "no credentials" warning — we intentionally use only open data.
warnings.filterwarnings("ignore", message="credentials were not supplied")

try:
    from statsbombpy import sb  # noqa: E402
    _HAS_STATSBOMBPY = True
except Exception as exc:  # pragma: no cover
    print(f"[warn] statsbombpy not available ({exc}); falling back to raw HTTP")
    _HAS_STATSBOMBPY = False

from lib.io import write_parquet  # noqa: E402

RAW_GITHUB = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"

MATCHES_DIR = PROJECT_ROOT / "01_data_raw" / "matches"
EVENTS_DIR = PROJECT_ROOT / "01_data_raw" / "events"
LINEUPS_DIR = PROJECT_ROOT / "01_data_raw" / "lineups"


# --------------------------------------------------------------------------
# Naming helpers
# --------------------------------------------------------------------------

def slugify(text: str) -> str:
    """Compact, filename-safe slug. 'FIFA World Cup' -> 'FIFAWorldCup'."""
    t = re.sub(r"[^A-Za-z0-9]+", " ", str(text)).strip()
    parts = [p for p in t.split() if p]
    return "".join(p[0].upper() + p[1:] for p in parts) if parts else "unknown"


def season_slug(season_name: str) -> str:
    """'2022' -> '2022'. '2015/2016' -> '2015-2016'. '2023/2024' -> '2023-2024'."""
    return str(season_name).replace("/", "-")


# --------------------------------------------------------------------------
# Listing & lookup
# --------------------------------------------------------------------------

def load_competitions() -> pd.DataFrame:
    if _HAS_STATSBOMBPY:
        return sb.competitions()
    # Fallback: read the catalog JSON directly.
    import urllib.request
    url = f"{RAW_GITHUB}/competitions.json"
    with urllib.request.urlopen(url) as r:
        data = json.load(r)
    return pd.DataFrame(data)


def print_competitions(comps: pd.DataFrame) -> None:
    keep = [
        "competition_id", "season_id", "country_name", "competition_name",
        "competition_gender", "season_name",
    ]
    keep = [c for c in keep if c in comps.columns]
    print("Available StatsBomb Open Data competitions:\n")
    print(comps[keep].sort_values(["competition_name", "season_name"]).to_string(index=False))


def resolve_targets(
    comps: pd.DataFrame,
    competition_filters: list[str],
    season_filter: str | None,
    gender: str,
) -> pd.DataFrame:
    """Pick rows from the competitions catalog matching the user's --competition / --season."""
    df = comps[comps["competition_gender"].str.lower() == gender.lower()].copy()

    if competition_filters:
        masks = []
        for f in competition_filters:
            if str(f).isdigit():
                masks.append(df["competition_id"] == int(f))
            else:
                masks.append(df["competition_name"].str.contains(f, case=False, regex=False, na=False))
        df = df[pd.concat(masks, axis=1).any(axis=1)]

    if season_filter:
        if str(season_filter).isdigit() and len(str(season_filter)) <= 4:
            # 4-digit year — match the year token inside season_name like '2022' or '2023/2024'
            df = df[df["season_name"].astype(str).str.contains(str(season_filter), na=False)]
        else:
            df = df[
                (df["season_id"].astype(str) == str(season_filter))
                | (df["season_name"].astype(str) == str(season_filter))
            ]

    return df.reset_index(drop=True)


# --------------------------------------------------------------------------
# Downloaders
# --------------------------------------------------------------------------

def fetch_matches(competition_id: int, season_id: int) -> pd.DataFrame:
    if _HAS_STATSBOMBPY:
        return sb.matches(competition_id=competition_id, season_id=season_id)
    import urllib.request
    url = f"{RAW_GITHUB}/matches/{competition_id}/{season_id}.json"
    with urllib.request.urlopen(url) as r:
        data = json.load(r)
    return pd.json_normalize(data, sep="_")


def fetch_events(match_id: int) -> pd.DataFrame:
    if _HAS_STATSBOMBPY:
        return sb.events(match_id=match_id)
    import urllib.request
    url = f"{RAW_GITHUB}/events/{match_id}.json"
    with urllib.request.urlopen(url) as r:
        data = json.load(r)
    df = pd.json_normalize(data, sep="_")
    df["match_id"] = match_id
    return df


def fetch_lineups(match_id: int) -> pd.DataFrame:
    """Return a single DataFrame with all lineup rows from both teams for `match_id`."""
    if _HAS_STATSBOMBPY:
        lu = sb.lineups(match_id=match_id)
        frames = []
        for team_name, df in lu.items():
            if df is None or len(df) == 0:
                continue
            d = df.copy()
            d["team"] = team_name
            d["match_id"] = match_id
            frames.append(d)
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True, sort=False)
    # Fallback
    import urllib.request
    url = f"{RAW_GITHUB}/lineups/{match_id}.json"
    with urllib.request.urlopen(url) as r:
        data = json.load(r)
    frames = []
    for entry in data:
        team_name = entry.get("team_name")
        team_id = entry.get("team_id")
        for p in entry.get("lineup", []):
            row = dict(p)
            row["team"] = team_name
            row["team_id"] = team_id
            row["match_id"] = match_id
            frames.append(row)
    return pd.json_normalize(frames, sep="_")


# --------------------------------------------------------------------------
# Dtype hygiene before write
# --------------------------------------------------------------------------

def _coerce_jsonish_to_string(df: pd.DataFrame) -> pd.DataFrame:
    """Parquet can't store python lists/dicts in object columns reliably across versions.

    Serialize any column that contains list/dict values to JSON strings.
    Also coerce *mixed* object columns (e.g. an int-id column where two managers
    got joined into one string like '4711, 3626') to plain strings so pyarrow
    doesn't try to find a uniform numeric type and crash.
    """
    if len(df) == 0:
        return df
    for col in df.columns:
        if df[col].dtype != "object":
            continue
        sample = df[col].dropna()
        if len(sample) == 0:
            continue
        first = sample.iloc[0]
        if isinstance(first, (list, dict)):
            df[col] = df[col].apply(
                lambda v: json.dumps(v, default=str, ensure_ascii=False) if isinstance(v, (list, dict)) else v
            )
            continue
        # Any remaining object column — coerce to pandas string. Prevents
        # pyarrow from inferring numeric and choking on outliers like
        # '4711, 3626' (two-manager id smushed into one string by statsbombpy).
        df[col] = df[col].astype("string")
    return df


def _shrink_ints(df: pd.DataFrame) -> pd.DataFrame:
    """Cast obvious integer-ish columns to Int16/Int32 where they fit."""
    for col in df.columns:
        s = df[col]
        # Cheap heuristic: integer typed or numeric with no fractional part.
        if pd.api.types.is_integer_dtype(s):
            mx = s.abs().max() if len(s) else 0
            if pd.isna(mx):
                continue
            if mx < 32767:
                df[col] = s.astype("Int16")
            elif mx < 2_147_483_647:
                df[col] = s.astype("Int32")
    return df


# --------------------------------------------------------------------------
# Per-season pipeline
# --------------------------------------------------------------------------

def ingest_one_season(
    competition_id: int,
    season_id: int,
    competition_name: str,
    season_name: str,
) -> dict[str, Any]:
    comp_slug = slugify(competition_name)
    s_slug = season_slug(season_name)
    tag = f"{comp_slug}_{s_slug}"

    print(f"\n[statsbomb] {competition_name} | {season_name} "
          f"(comp_id={competition_id}, season_id={season_id})")

    # ---- matches ----
    matches = fetch_matches(competition_id, season_id)
    if len(matches) == 0:
        print(f"  [skip] no matches returned")
        return {"matches": 0, "events": 0, "lineups": 0}

    matches = matches.copy()
    matches["competition_slug"] = comp_slug
    matches["season_slug"] = s_slug
    matches = _coerce_jsonish_to_string(matches)
    matches = _shrink_ints(matches)
    matches_path = MATCHES_DIR / f"statsbomb_{tag}.parquet"
    write_parquet(matches, matches_path)
    size_mb = matches_path.stat().st_size / 1024 / 1024
    print(f"  matches  {len(matches):>5,} rows -> {matches_path.name} ({size_mb:.2f} MB)")

    match_ids = matches["match_id"].astype(int).tolist()

    # ---- events ----
    print(f"  events   downloading {len(match_ids)} match files...")
    ev_frames: list[pd.DataFrame] = []
    failures = 0
    for i, mid in enumerate(match_ids, 1):
        try:
            ev = fetch_events(mid)
            ev_frames.append(ev)
        except Exception as e:
            failures += 1
            print(f"           [fail] match {mid}: {type(e).__name__}: {e}")
            continue
        if i % 20 == 0 or i == len(match_ids):
            print(f"           {i}/{len(match_ids)} matches fetched")

    events = pd.concat(ev_frames, ignore_index=True, sort=False) if ev_frames else pd.DataFrame()
    events["competition_slug"] = comp_slug
    events["season_slug"] = s_slug
    events = _coerce_jsonish_to_string(events)
    events = _shrink_ints(events)
    events_path = EVENTS_DIR / f"statsbomb_{tag}.parquet"
    write_parquet(events, events_path)
    size_mb = events_path.stat().st_size / 1024 / 1024
    print(f"  events   {len(events):>7,} rows -> {events_path.name} ({size_mb:.2f} MB) "
          f"[{failures} failure(s)]")

    # ---- lineups ----
    print(f"  lineups  downloading {len(match_ids)} match files...")
    lu_frames: list[pd.DataFrame] = []
    for i, mid in enumerate(match_ids, 1):
        try:
            lu = fetch_lineups(mid)
            if len(lu) > 0:
                lu_frames.append(lu)
        except Exception as e:
            print(f"           [fail] match {mid}: {type(e).__name__}: {e}")
            continue
    lineups = pd.concat(lu_frames, ignore_index=True, sort=False) if lu_frames else pd.DataFrame()
    lineups["competition_slug"] = comp_slug
    lineups["season_slug"] = s_slug
    lineups = _coerce_jsonish_to_string(lineups)
    lineups = _shrink_ints(lineups)
    lineups_path = LINEUPS_DIR / f"statsbomb_{tag}.parquet"
    write_parquet(lineups, lineups_path)
    size_mb = lineups_path.stat().st_size / 1024 / 1024
    print(f"  lineups  {len(lineups):>5,} rows -> {lineups_path.name} ({size_mb:.2f} MB)")

    return {
        "matches": len(matches),
        "events": len(events),
        "lineups": len(lineups),
        "competition_slug": comp_slug,
        "season_slug": s_slug,
        "competition_id": competition_id,
        "season_id": season_id,
    }


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        description="Download StatsBomb Open Data competitions (matches, events, lineups).",
    )
    p.add_argument(
        "--list", action="store_true",
        help="Print available competitions and exit.",
    )
    p.add_argument(
        "--competition", "-c", action="append", default=[],
        help="Competition name (substring, case-insensitive) or numeric id. Repeatable.",
    )
    p.add_argument(
        "--season", default=None,
        help="Season filter — id, name ('2022', '2015/2016'), or 4-digit year.",
    )
    p.add_argument(
        "--gender", default="male", choices=["male", "female"],
        help="Filter by competition gender (default: male).",
    )
    p.add_argument(
        "--limit-seasons", type=int, default=None,
        help="If a competition has multiple matching seasons, only keep the first N.",
    )
    args = p.parse_args()

    comps = load_competitions()

    if args.list:
        print_competitions(comps)
        return

    if not args.competition:
        p.error("Provide --competition (repeatable) or --list. See --help.")

    targets = resolve_targets(comps, args.competition, args.season, args.gender)
    if args.limit_seasons:
        targets = targets.head(args.limit_seasons)

    if len(targets) == 0:
        print("[statsbomb] no competitions matched your filters.")
        return

    print(f"[statsbomb] planning to download {len(targets)} competition-season(s):")
    for _, r in targets.iterrows():
        print(f"  - {r['competition_name']} | {r['season_name']} "
              f"(comp_id={r['competition_id']}, season_id={r['season_id']})")

    summaries = []
    for _, row in targets.iterrows():
        try:
            summary = ingest_one_season(
                competition_id=int(row["competition_id"]),
                season_id=int(row["season_id"]),
                competition_name=str(row["competition_name"]),
                season_name=str(row["season_name"]),
            )
            summaries.append(summary)
        except Exception as e:
            print(f"  [FATAL] {row['competition_name']} {row['season_name']}: {type(e).__name__}: {e}")

    print("\n[statsbomb] done.")
    print(f"  competitions loaded : {len(summaries)}")
    print(f"  total matches       : {sum(s['matches'] for s in summaries):,}")
    print(f"  total events        : {sum(s['events']  for s in summaries):,}")
    print(f"  total lineup rows   : {sum(s['lineups'] for s in summaries):,}")


if __name__ == "__main__":
    main()
