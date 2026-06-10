r"""Backtesting helpers for the value-betting pipeline.

Operates on the ``match_value`` table produced by
``07_features/build_matches_view.py`` — one row per (match, player, market,
line, side) carrying the model probability, the quoted odds, the betting
metrics (``ev``, ``kelly_*``) and the realized result (``won`` ∈ {1, 0, NaN};
NaN = push or not-yet-played).

The simulation is deliberately simple and assumption-light:

    PnL per unit staked = (odds - 1) if won else -1   (0 on a push)

Two staking schemes: **flat** (1 unit per bet) and **fractional Kelly** (stake
the ``kelly_*`` fraction of a notional unit bankroll). ROI is profit over total
amount staked. We also expose a chronological bankroll curve so the *drawdown*
is visible, not just the aggregate ROI — a strategy can be +ROI overall yet
ruin you mid-season.

Nothing here is advice. Backtested edge on soft/synthetic odds does not transfer
to a sharp book; treat positive numbers as a check that the *logic* works, not a
promise of profit.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _settled(match_value: pd.DataFrame) -> pd.DataFrame:
    """Rows with a realized win/lose result (drop pushes and unplayed)."""
    return match_value[match_value["won"].notna()].copy()


def bet_pnl(won: pd.Series | np.ndarray, odds: pd.Series | np.ndarray) -> np.ndarray:
    """Per-unit PnL: ``odds-1`` on a win, ``-1`` on a loss. Vectorized."""
    won = np.asarray(won, dtype=float)
    odds = np.asarray(odds, dtype=float)
    return np.where(won > 0.5, odds - 1.0, -1.0)


def run_backtest(
    match_value: pd.DataFrame,
    ev_min: float = 0.0,
    stake: str = "flat",
    kelly_col: str = "kelly_25pct",
) -> dict:
    """Simulate betting every settled row with ``ev > ev_min``.

    ``stake`` is ``"flat"`` (1 unit each) or ``"kelly"`` (the ``kelly_col``
    fraction). Returns aggregate metrics; ``None``-safe (empty → zeros).
    """
    bet = _settled(match_value)
    bet = bet[bet["ev"] > ev_min]
    if len(bet) == 0:
        return {"ev_min": ev_min, "stake": stake, "n_bets": 0, "staked": 0.0,
                "profit": 0.0, "roi": np.nan, "hit_rate": np.nan, "mean_ev": np.nan}

    gross = bet_pnl(bet["won"], bet["odds"])
    if stake == "flat":
        w = np.ones(len(bet))
    elif stake == "kelly":
        w = bet[kelly_col].to_numpy(dtype=float)
    else:
        raise ValueError(f"unknown stake scheme: {stake!r} (use 'flat' or 'kelly')")

    pnl = gross * w
    staked = float(w.sum())
    return {
        "ev_min": ev_min,
        "stake": stake,
        "n_bets": int(len(bet)),
        "staked": staked,
        "profit": float(pnl.sum()),
        "roi": float(pnl.sum() / staked) if staked else np.nan,
        "hit_rate": float((bet["won"] > 0.5).mean()),
        "mean_ev": float(bet["ev"].mean()),
    }


def threshold_scan(
    match_value: pd.DataFrame,
    thresholds=(0.0, 0.02, 0.05, 0.10, 0.20, 0.40),
    stakes=("flat", "kelly"),
    kelly_col: str = "kelly_25pct",
) -> pd.DataFrame:
    """Backtest across a grid of EV thresholds × staking schemes."""
    rows = [
        run_backtest(match_value, ev_min=t, stake=s, kelly_col=kelly_col)
        for t in thresholds
        for s in stakes
    ]
    return pd.DataFrame(rows)


def bankroll_curve(
    match_value: pd.DataFrame,
    ev_min: float = 0.05,
    kelly_col: str = "kelly_25pct",
    date_col: str = "date",
) -> pd.DataFrame:
    """Chronological bankroll under fractional-Kelly staking (base 1.0, additive).

    Returns a frame with ``[date, ret, bankroll, peak, drawdown]`` so callers can
    plot the curve and read off the worst drawdown.
    """
    bet = _settled(match_value)
    bet = bet[bet["ev"] > ev_min].sort_values(date_col).copy()
    if len(bet) == 0:
        return pd.DataFrame(columns=[date_col, "ret", "bankroll", "peak", "drawdown"])

    gross = bet_pnl(bet["won"], bet["odds"])
    bet["ret"] = gross * bet[kelly_col].to_numpy(dtype=float)
    bet["bankroll"] = 1.0 + bet["ret"].cumsum()
    bet["peak"] = bet["bankroll"].cummax()
    bet["drawdown"] = bet["bankroll"] - bet["peak"]
    return bet[[date_col, "ret", "bankroll", "peak", "drawdown"]].reset_index(drop=True)


def max_drawdown(curve: pd.DataFrame) -> float:
    """Worst peak-to-trough drop of a :func:`bankroll_curve` (≤ 0)."""
    return float(curve["drawdown"].min()) if len(curve) else 0.0


def calibration(match_value: pd.DataFrame, n_bins: int = 10) -> pd.DataFrame:
    """Predicted-prob bin → realized win rate. The acid test for the model.

    Columns: ``[bin, n, pred, obs, gap]``. ``gap = obs - pred``; near 0 across
    bins ⇒ well-calibrated probabilities (a precondition for trustworthy EV).
    """
    b = _settled(match_value)
    edges = np.linspace(0.0, 1.0, n_bins + 1)
    b = b.assign(_bin=pd.cut(b["p_model"], edges, include_lowest=True))
    out = (
        b.groupby("_bin", observed=True)
         .agg(n=("won", "size"), pred=("p_model", "mean"), obs=("won", "mean"))
         .dropna()
         .reset_index()
         .rename(columns={"_bin": "bin"})
    )
    out["gap"] = out["obs"] - out["pred"]
    return out


def summary(match_value: pd.DataFrame, ev_min: float = 0.05,
            kelly_col: str = "kelly_25pct") -> dict:
    """One-call rollup: threshold backtest + bankroll drawdown + calibration error."""
    bt = run_backtest(match_value, ev_min=ev_min, stake="flat")
    curve = bankroll_curve(match_value, ev_min=ev_min, kelly_col=kelly_col)
    cal = calibration(match_value)
    return {
        **bt,
        "max_drawdown": max_drawdown(curve),
        "final_bankroll": float(curve["bankroll"].iloc[-1]) if len(curve) else np.nan,
        "calibration_mae": float(cal["gap"].abs().mean()) if len(cal) else np.nan,
    }
