"""Utilities for model training and evaluation.

Conventions used across `08_models/` scripts:

    - Splits are always *temporal*. Random shuffling leaks future data
      into training for time-indexed observations.
    - Baselines: the simplest sensible prediction (last-N rolling mean of
      the player's history). Improvements over this baseline are the only
      claim worth making.
    - Evaluation: MAE on the natural unit (e.g. shots/match), RMSE for
      large-error sensitivity, and a calibration table (predicted-bin
      mean vs. observed mean) for distributional fidelity.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error


def temporal_split(
    df: pd.DataFrame,
    date_col: str = "date",
    train_frac: float = 0.7,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.Timestamp]:
    """Split `df` chronologically: first `train_frac` of dates → train, rest → test.

    Returns `(train, test, cutoff_date)`.
    """
    cutoff = df[date_col].quantile(train_frac)
    train = df[df[date_col] <= cutoff].copy()
    test = df[df[date_col] > cutoff].copy()
    return train, test, cutoff


def evaluate_against_baseline(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_baseline: Optional[np.ndarray] = None,
) -> dict[str, float]:
    """Return MAE / RMSE and optional comparison against a baseline predictor."""
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    out = {"mae": mae, "rmse": rmse, "n": int(len(y_true))}
    if y_baseline is not None:
        base_mae = float(mean_absolute_error(y_true, y_baseline))
        base_rmse = float(np.sqrt(mean_squared_error(y_true, y_baseline)))
        out["baseline_mae"] = base_mae
        out["baseline_rmse"] = base_rmse
        out["mae_improvement_pct"] = (base_mae - mae) / base_mae * 100 if base_mae else 0.0
    return out


def calibration_table(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_bins: int = 10,
) -> pd.DataFrame:
    """Bin predictions, return mean predicted vs mean observed per bin.

    A well-calibrated model has `pred_mean ≈ true_mean` in every bin.
    """
    cal = pd.DataFrame({"pred": y_pred, "true": y_true})
    cal["bin"] = pd.qcut(cal["pred"].rank(method="first"), n_bins, labels=False)
    return cal.groupby("bin").agg(
        pred_mean=("pred", "mean"),
        true_mean=("true", "mean"),
        n=("true", "size"),
    ).reset_index()


def format_results_md(
    target: str,
    results: dict[str, float],
    cal: pd.DataFrame,
    feature_importance: Optional[pd.DataFrame] = None,
    extra_notes: Optional[str] = None,
) -> str:
    """Render a Markdown report from an evaluation result."""
    lines = []
    lines.append(f"# Predictor de `{target}` — resultados")
    lines.append("")
    lines.append(f"- Filas de test: **{results['n']:,}**")
    lines.append(f"- MAE modelo: **{results['mae']:.4f}**")
    lines.append(f"- RMSE modelo: **{results['rmse']:.4f}**")
    if "baseline_mae" in results:
        lines.append(f"- MAE baseline (rolling 5): **{results['baseline_mae']:.4f}**")
        lines.append(f"- RMSE baseline (rolling 5): **{results['baseline_rmse']:.4f}**")
        improvement = results["mae_improvement_pct"]
        symbol = "↓ mejor" if improvement >= 0 else "↑ peor"
        lines.append(f"- Mejora MAE vs baseline: **{improvement:+.2f}%** ({symbol})")
    lines.append("")

    if feature_importance is not None and not feature_importance.empty:
        lines.append("## Importancia de features (XGBoost gain)")
        lines.append("")
        lines.append("| Feature | Importancia |")
        lines.append("|---------|------------:|")
        for _, r in feature_importance.iterrows():
            lines.append(f"| {r['feature']} | {r['importance']:.4f} |")
        lines.append("")

    lines.append("## Tabla de calibración (10 bins por predicción)")
    lines.append("")
    lines.append("| Bin | Predicho (media) | Observado (media) | n |")
    lines.append("|----:|-----------------:|------------------:|--:|")
    for _, r in cal.iterrows():
        lines.append(
            f"| {int(r['bin'])} | {r['pred_mean']:.3f} | {r['true_mean']:.3f} | {int(r['n'])} |"
        )
    lines.append("")
    lines.append("Interpretación: si `pred_mean ≈ true_mean` en cada bin, el modelo está bien calibrado.")
    if extra_notes:
        lines.append("")
        lines.append(extra_notes)
    return "\n".join(lines)
