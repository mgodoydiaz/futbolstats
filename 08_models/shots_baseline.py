"""Baseline model: predict per-match shots using rolling player average.

Smoke test for the pipeline. Trains on StatsBomb player-match data and
evaluates with a 70/30 temporal split. Reports MAE vs a "global mean"
naive baseline so we see if rolling history adds signal.

Usage:
    python 08_models/shots_baseline.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.io import read_parquet  # noqa: E402

INPUT = PROJECT_ROOT / "02_data_processed" / "events_clean" / "statsbomb_player_match.parquet"
TARGET = "shots"
ROLL_WINDOW = 5


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """Sort by player+date and compute rolling stats up to (not including) row."""
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["date", TARGET, "player_id"]).sort_values(["player_id", "date"])
    # rolling mean of last N matches BEFORE the current one
    df["roll_shots"] = (
        df.groupby("player_id")[TARGET]
          .transform(lambda s: s.shift(1).rolling(ROLL_WINDOW, min_periods=1).mean())
    )
    df["roll_minutes"] = (
        df.groupby("player_id")["minutes_played"]
          .transform(lambda s: s.shift(1).rolling(ROLL_WINDOW, min_periods=1).mean())
    )
    df["career_shots"] = (
        df.groupby("player_id")[TARGET]
          .transform(lambda s: s.shift(1).expanding().mean())
    )
    return df


def main():
    if not INPUT.exists():
        print(f"Missing {INPUT.relative_to(PROJECT_ROOT)} — run the StatsBomb pipeline first.")
        return

    df = read_parquet(INPUT)
    print(f"Loaded {len(df):,} player-match rows from {INPUT.name}")

    feats = build_features(df)
    feats = feats.dropna(subset=["roll_shots"])
    print(f"After rolling features: {len(feats):,} usable rows")

    # Temporal split: train first 70% by date, test last 30%
    split = feats["date"].quantile(0.7)
    train = feats[feats["date"] <= split]
    test = feats[feats["date"] > split]
    print(f"Train: {len(train):,}  Test: {len(test):,}  (split @ {split.date()})")

    # Baseline 1: global mean from train
    baseline_mean = train[TARGET].mean()
    naive_pred = np.full(len(test), baseline_mean)
    naive_mae = (test[TARGET] - naive_pred).abs().mean()

    # Baseline 2: player's rolling average (already in roll_shots column)
    roll_pred = test["roll_shots"].fillna(baseline_mean).values
    roll_mae = (test[TARGET] - roll_pred).abs().mean()

    # Baseline 3: career-to-date mean (longer window)
    career_pred = test["career_shots"].fillna(baseline_mean).values
    career_mae = (test[TARGET] - career_pred).abs().mean()

    print()
    print("Test MAE on shots-per-match (lower is better):")
    print(f"  global mean baseline       : {naive_mae:.3f}")
    print(f"  rolling avg (last {ROLL_WINDOW})        : {roll_mae:.3f}  "
          f"({(naive_mae-roll_mae)/naive_mae*100:+.1f}% vs naive)")
    print(f"  career-to-date mean        : {career_mae:.3f}  "
          f"({(naive_mae-career_mae)/naive_mae*100:+.1f}% vs naive)")

    # Quick distribution sanity
    print()
    print(f"Target distribution (shots/match): "
          f"mean={feats[TARGET].mean():.2f}, "
          f"median={feats[TARGET].median():.0f}, "
          f"p95={feats[TARGET].quantile(0.95):.0f}, "
          f"max={feats[TARGET].max():.0f}")


if __name__ == "__main__":
    main()
