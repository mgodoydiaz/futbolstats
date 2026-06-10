"""Enrich statsbomb_player_match.parquet with the player's position per match.

The position is the modal label across all events the player produced in
that match (a player normally stays in one position; substitutes get the
position they entered as).

Adds two new columns:
    - position           (raw StatsBomb label, e.g. "Right Center Back")
    - position_group     (collapsed: GK / DEF / MID / FWD)

Usage:
    python 07_features/enrich_position.py
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


def position_to_group(position: str) -> str:
    """Collapse a StatsBomb position label to one of GK / DEF / MID / FWD."""
    if not isinstance(position, str):
        return "UNK"
    p = position.lower()
    if "goalkeeper" in p:
        return "GK"
    # Wing Back is treated as a defender (more defensive duties than a Winger).
    if "back" in p:
        return "DEF"
    if "midfield" in p:
        return "MID"
    if "wing" in p or "forward" in p or "striker" in p:
        return "FWD"
    return "UNK"


def derive_match_position() -> pd.DataFrame:
    """Return one (match_id, player_id) -> modal position row per pairing."""
    parts = []
    for f in sorted(EVENTS_DIR.glob("statsbomb_*.parquet")):
        df = read_parquet(f, columns=["match_id", "player_id", "position"])
        df = df.dropna(subset=["player_id", "position"])
        df = df[df["position"] != "Substitute"]
        if df.empty:
            continue
        # modal (most common) position per (match_id, player_id)
        modal = (
            df.groupby(["match_id", "player_id"], dropna=False)["position"]
              .agg(lambda s: s.mode().iloc[0] if not s.mode().empty else None)
              .reset_index()
              .rename(columns={"position": "position"})
        )
        parts.append(modal)
        print(f"  {f.name}: {len(modal):,} player-match position labels")

    if not parts:
        return pd.DataFrame()
    out = pd.concat(parts, ignore_index=True).drop_duplicates(
        subset=["match_id", "player_id"], keep="first"
    )
    out["position_group"] = out["position"].map(position_to_group)
    return out


def main():
    print("[enrich-position] computing modal position from events ...")
    pos = derive_match_position()
    print(f"  total (match, player) pairs with position: {len(pos):,}")
    print(f"  position_group distribution:")
    print(pos["position_group"].value_counts().to_string().replace("\n", "\n    "))

    if not PLAYER_MATCH.exists():
        raise FileNotFoundError(f"missing {PLAYER_MATCH}")
    pm = read_parquet(PLAYER_MATCH)
    print(f"  loaded {len(pm):,} rows from {PLAYER_MATCH.name}")

    # Drop existing position columns if present to keep idempotent
    pm = pm.drop(columns=[c for c in ("position", "position_group") if c in pm.columns])
    # player_match uses the `sb_<id>` prefixed form; events use bare ints.
    # Normalize both sides to the prefixed string form.
    def _prefix(s):
        s = pd.Series(s).astype(str).str.replace(r"\.0$", "", regex=True)
        return s.where(s.str.startswith("sb_"), "sb_" + s)
    pos["match_id"] = _prefix(pos["match_id"]).values
    pos["player_id"] = _prefix(pos["player_id"]).values
    pm["match_id"] = _prefix(pm["match_id"]).values
    pm["player_id"] = _prefix(pm["player_id"]).values

    merged = pm.merge(pos, on=["match_id", "player_id"], how="left")
    matched = merged["position"].notna().sum()
    print(f"  enriched: {matched:,}/{len(merged):,} rows have a position "
          f"({matched / max(len(merged), 1):.1%})")

    write_parquet(merged, PLAYER_MATCH)
    print(f"  wrote -> {PLAYER_MATCH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
