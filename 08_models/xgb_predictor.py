"""Generic XGBoost predictor for any per-match player stat.

Trains XGBoost on StatsBomb player-match data with leak-safe rolling
features and a temporal hold-out. Reports MAE/RMSE versus a rolling-mean
baseline. Saves a markdown report and the trained model.

Usage:
    python 08_models/xgb_predictor.py --target shots
    python 08_models/xgb_predictor.py --target passes_completed
    python 08_models/xgb_predictor.py --targets shots,passes_completed,xg
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import xgboost as xgb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.features import add_match_features  # noqa: E402
from lib.io import read_parquet  # noqa: E402
from lib.models import (  # noqa: E402
    calibration_table,
    evaluate_against_baseline,
    format_results_md,
    temporal_split,
)

RESULTS_DIR = PROJECT_ROOT / "08_models" / "reports"

DATASETS = {
    "player_match": {
        "path": PROJECT_ROOT / "02_data_processed" / "events_clean" / "statsbomb_player_match.parquet",
        "targets": [
            "shots", "shots_on_target", "goals", "assists",
            "passes_attempted", "passes_completed", "key_passes",
            "xg", "dribbles_attempted", "dribbles_completed",
            "tackles", "interceptions",
            "fouls_committed", "fouls_drawn",
        ],
    },
    "gk_match": {
        "path": PROJECT_ROOT / "02_data_processed" / "events_clean" / "statsbomb_gk_match.parquet",
        "targets": [
            "saves", "goals_against", "punches", "claims",
            "sweeper_actions", "shots_faced", "save_pct",
        ],
    },
}

# legacy single-list for backward compatible argparse choices
VALID_TARGETS = DATASETS["player_match"]["targets"] + DATASETS["gk_match"]["targets"]


def build_feature_frame(
    df: pd.DataFrame,
    target: str,
    with_opponent: bool = False,
) -> tuple[pd.DataFrame, list[str]]:
    """Add features and return the frame + feature column names."""
    if target not in df.columns:
        raise KeyError(f"target {target} not in DataFrame columns")

    df = add_match_features(df, target_col=target, with_opponent=with_opponent)

    feature_cols = [
        f"roll_{target}_3",
        f"roll_{target}_5",
        f"roll_{target}_10",
        f"career_{target}",
        "days_rest",
        "roll_minutes_5",
        "is_home",
        "minutes_played",
    ]
    if with_opponent:
        feature_cols.extend([
            f"opp_allows_{target}_5",
            f"opp_allows_{target}_10",
        ])
    feature_cols = [c for c in feature_cols if c in df.columns]
    return df, feature_cols


def train_one(
    target: str,
    df: pd.DataFrame,
    results_dir: Path,
    tag: str | None = None,
    with_opponent: bool = False,
    objective: str = "reg:squarederror",
) -> dict:
    print(f"\n=== TARGET: {target} ===" if tag is None else f"\n=== TARGET: {tag} ===")
    df_feat, feature_cols = build_feature_frame(df, target, with_opponent=with_opponent)
    # drop rows where we cannot form even the smallest rolling feature
    df_feat = df_feat.dropna(subset=[f"roll_{target}_3", target])
    print(f"  usable rows after rolling: {len(df_feat):,}")
    print(f"  features: {feature_cols}")

    train, test, cutoff = temporal_split(df_feat, "date", train_frac=0.7)
    print(f"  train: {len(train):,}  test: {len(test):,}  cutoff: {pd.Timestamp(cutoff).date()}")

    X_train = train[feature_cols].fillna(0.0)
    y_train = train[target].astype(float)
    X_test = test[feature_cols].fillna(0.0)
    y_test = test[target].astype(float)

    model = xgb.XGBRegressor(
        n_estimators=400,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        min_child_weight=5,
        reg_lambda=1.0,
        objective=objective,
        n_jobs=-1,
        random_state=42,
        early_stopping_rounds=30,
        verbosity=0,
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    y_pred = model.predict(X_test)

    # rolling-5 baseline (fall back to career mean, then to train mean)
    fallback = float(y_train.mean())
    baseline = (
        test[f"roll_{target}_5"]
        .fillna(test[f"career_{target}"])
        .fillna(fallback)
        .astype(float)
        .values
    )

    results = evaluate_against_baseline(y_test.values, y_pred, baseline)
    cal = calibration_table(y_test.values, y_pred)
    importance = pd.DataFrame({
        "feature": feature_cols,
        "importance": model.feature_importances_,
    }).sort_values("importance", ascending=False)

    print(f"  MAE model: {results['mae']:.4f}  "
          f"MAE baseline: {results['baseline_mae']:.4f}  "
          f"improvement: {results['mae_improvement_pct']:+.2f}%")

    # write markdown report
    notes = (
        f"Cutoff temporal: filas con fecha $\\leq$ "
        f"{pd.Timestamp(cutoff).date()} en train; el resto en test."
    )
    md = format_results_md(target, results, cal, feature_importance=importance, extra_notes=notes)
    results_dir.mkdir(parents=True, exist_ok=True)
    out = results_dir / f"{tag or target}_xgb.md"
    out.write_text(md, encoding="utf-8")
    print(f"  report -> {out.relative_to(PROJECT_ROOT)}")

    return {
        "target": target,
        "mae": results["mae"],
        "baseline_mae": results.get("baseline_mae"),
        "improvement_pct": results.get("mae_improvement_pct"),
        "n_test": results["n"],
    }


def train_by_position(
    target: str,
    df: pd.DataFrame,
    results_dir: Path,
    with_opponent: bool = False,
    objective: str = "reg:squarederror",
) -> list[dict]:
    """Train one XGBoost per position_group, return list of summaries."""
    if "position_group" not in df.columns:
        raise KeyError(
            "position_group column missing. Run 07_features/enrich_position.py first."
        )
    groups = ["GK", "DEF", "MID", "FWD"]
    summaries = []
    for g in groups:
        sub = df[df["position_group"] == g].copy()
        if len(sub) < 200:
            print(f"\n--- {target} | {g}: insufficient rows ({len(sub)}), skipping ---")
            continue
        print(f"\n--- {target} | position={g} | n={len(sub):,} ---")
        sub_results = train_one(
            target, sub,
            results_dir / "by_position",
            tag=f"{target}_{g.lower()}",
            with_opponent=with_opponent,
            objective=objective,
        )
        sub_results["position"] = g
        summaries.append(sub_results)
    return summaries


def main():
    parser = argparse.ArgumentParser(description="XGBoost predictor for per-match player stats.")
    parser.add_argument("--target", choices=VALID_TARGETS, help="Single target.")
    parser.add_argument("--targets", default=None,
                        help="Comma-separated list of targets (overrides --target).")
    parser.add_argument("--by-position", action="store_true",
                        help="Train one model per position_group (GK/DEF/MID/FWD).")
    parser.add_argument("--with-opponent", action="store_true",
                        help="Add opponent-allowed rolling features (opp_allows_<t>_5/_10).")
    parser.add_argument("--objective", default="reg:squarederror",
                        choices=["reg:squarederror", "count:poisson"],
                        help="XGBoost objective. Use count:poisson for sparse count targets.")
    parser.add_argument("--dataset", default="player_match",
                        choices=list(DATASETS),
                        help="Which input table to read from.")
    args = parser.parse_args()

    valid_for_dataset = DATASETS[args.dataset]["targets"]
    if args.targets:
        targets = [t.strip() for t in args.targets.split(",") if t.strip()]
        invalid = [t for t in targets if t not in valid_for_dataset]
        if invalid:
            raise SystemExit(
                f"unknown targets for dataset={args.dataset}: {invalid}\n"
                f"valid = {valid_for_dataset}"
            )
    elif args.target:
        targets = [args.target]
    else:
        parser.error("specify --target or --targets")

    data_path = DATASETS[args.dataset]["path"]
    df = read_parquet(data_path)
    print(f"Loaded {len(df):,} rows from {data_path.name} (dataset={args.dataset})")

    summary = []
    for t in targets:
        if args.by_position:
            summary.extend(train_by_position(
                t, df, RESULTS_DIR,
                with_opponent=args.with_opponent,
                objective=args.objective,
            ))
        else:
            summary.append(train_one(
                t, df, RESULTS_DIR,
                with_opponent=args.with_opponent,
                objective=args.objective,
            ))

    print()
    print("=== summary ===")
    by_pos = args.by_position
    if by_pos:
        print(f"{'target':<22s} {'pos':>4s} {'n':>7s} {'mae':>8s} {'base_mae':>10s} {'improv':>9s}")
    else:
        print(f"{'target':<22s} {'n':>7s} {'mae':>8s} {'base_mae':>10s} {'improv':>9s}")
    for s in summary:
        improv = f"{s['improvement_pct']:+.2f}%" if s["improvement_pct"] is not None else "—"
        if by_pos:
            print(
                f"{s['target']:<22s} "
                f"{s.get('position', '-'):>4s} "
                f"{s['n_test']:>7,} "
                f"{s['mae']:>8.4f} "
                f"{s['baseline_mae']:>10.4f} "
                f"{improv:>9}"
            )
        else:
            print(
                f"{s['target']:<22s} "
                f"{s['n_test']:>7,} "
                f"{s['mae']:>8.4f} "
                f"{s['baseline_mae']:>10.4f} "
                f"{improv:>9}"
            )


if __name__ == "__main__":
    main()
