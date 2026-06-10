r"""Reorganize the player-match data into a match-centric *betting view*.

The training tables in ``02_data_processed/`` are flat one-row-per-player-match
frames optimised for model fitting. Betting analysis needs a different shape —
organised around *matches → players → markets → odds → value*. This script
builds that view in ``02_data_processed/matches_view/``:

    fixtures.parquet       one row per match (date, comp, season, home/away, status)
    match_players.parquet  per (match, player): leak-safe λ prediction + dispersion
                           for every prop target, plus the realized outcome
    match_odds.parquet     long odds table the scraper fills:
                           [match_id, player_id, market, line, side, bookmaker, odds, ts]
                           (``--synthetic`` fills it with population-priced odds so the
                           whole pipeline runs before the live scraper exists)
    match_value.parquet    the join + betting math: for each (match, player, market,
                           line, side) → p_model, implied_prob, edge, ev, kelly, and
                           the realized result (won / push) for backtesting

The λ prediction here is the **leak-safe rolling baseline** (roll-5 → career →
population mean, all ``shift(1)``). It is deliberately the same quantity the
XGBoost baseline beats — swap in model predictions later by overwriting the
``lam_<market>`` columns of ``match_players.parquet``.

Usage:
    python 07_features/build_matches_view.py --source statsbomb
    python 07_features/build_matches_view.py --source statsbomb --synthetic
    python 07_features/build_matches_view.py --source statsbomb --synthetic --vig 0.05
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scipy.stats import nbinom, poisson  # noqa: E402

from lib.betting import (  # noqa: E402
    dispersion_from_moments,
    negbin_over_under,
)
from lib.features import add_career_mean, add_rolling_features  # noqa: E402
from lib.io import read_parquet, write_parquet  # noqa: E402

OUT_DIR = PROJECT_ROOT / "02_data_processed" / "matches_view"

SOURCES = {
    "statsbomb": PROJECT_ROOT / "02_data_processed" / "events_clean" / "statsbomb_player_match.parquet",
}

# Prop markets we expose, mapped to a column in the player-match table and the
# standard over/under lines a book would offer. Half-lines avoid pushes; the
# integer lines are kept where books quote them (then a push is possible).
MARKETS: dict[str, dict] = {
    "shots":            {"col": "shots",            "lines": [0.5, 1.5, 2.5]},
    "shots_on_target":  {"col": "shots_on_target",  "lines": [0.5, 1.5]},
    "tackles":          {"col": "tackles",          "lines": [0.5, 1.5, 2.5]},
    "interceptions":    {"col": "interceptions",    "lines": [0.5, 1.5]},
    "fouls_committed":  {"col": "fouls_committed",  "lines": [0.5, 1.5]},
    "passes_completed": {"col": "passes_completed", "lines": [19.5, 29.5, 39.5]},
}

SIDES = ("over", "under")


# --------------------------------------------------------------------------
# fixtures
# --------------------------------------------------------------------------

def build_fixtures(pm: pd.DataFrame) -> pd.DataFrame:
    """One row per match: id, date, comp, season, home/away teams, status."""
    pm = pm.copy()
    pm["date"] = pd.to_datetime(pm["date"], errors="coerce")

    # Home / away team per match from the is_home flag.
    home = (
        pm[pm["is_home"] == True]  # noqa: E712  (works for bool and Int8)
        .groupby("match_id")
        .agg(home_team_id=("team_id", "first"), home_team=("team_name", "first"))
    )
    away = (
        pm[pm["is_home"] != True]  # noqa: E712
        .groupby("match_id")
        .agg(away_team_id=("team_id", "first"), away_team=("team_name", "first"))
    )
    meta = (
        pm.groupby("match_id")
        .agg(
            date=("date", "first"),
            competition_id=("competition_id", "first"),
            competition_slug=("competition_slug", "first"),
            season=("season", "first"),
            n_players=("player_id", "nunique"),
        )
    )
    fixtures = meta.join(home, how="left").join(away, how="left").reset_index()

    today = pd.Timestamp.now("UTC").tz_localize(None).normalize()
    fixtures["status"] = np.where(fixtures["date"] >= today, "upcoming", "past")
    return fixtures.sort_values("date").reset_index(drop=True)


# --------------------------------------------------------------------------
# match_players: leak-safe λ predictions per target
# --------------------------------------------------------------------------

def _leak_safe_lambda(pm: pd.DataFrame, col: str) -> pd.Series:
    """roll-5 → career → population mean, all shift(1). Indexed like ``pm``."""
    tmp = add_rolling_features(pm, col, group_col="player_id", sort_col="date", windows=(5,))
    tmp = add_career_mean(tmp, col, group_col="player_id", sort_col="date")
    pop_mean = float(pm[col].mean())
    lam = tmp[f"roll_{col}_5"].fillna(tmp[f"career_{col}"]).fillna(pop_mean)
    return lam.reindex(pm.index)


def build_match_players(pm: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
    """Per (match, player): λ prediction + realized outcome for each market.

    Returns the frame plus the per-market dispersion ``alpha`` (estimated once
    from the whole sample) so downstream can pick Poisson vs NegBinomial.
    """
    pm = pm.copy()
    pm["date"] = pd.to_datetime(pm["date"], errors="coerce")
    pm = pm.sort_values(["player_id", "date"]).reset_index(drop=True)

    base_cols = [
        "match_id", "date", "competition_id", "season",
        "player_id", "player_name", "team_id", "opponent_id",
        "is_home", "minutes_played", "position_group",
    ]
    base_cols = [c for c in base_cols if c in pm.columns]
    out = pm[base_cols].copy()

    alphas: dict[str, float] = {}
    for market, spec in MARKETS.items():
        col = spec["col"]
        if col not in pm.columns:
            continue
        out[f"lam_{market}"] = _leak_safe_lambda(pm, col).values
        out[f"actual_{market}"] = pm[col].values
        alphas[market] = dispersion_from_moments(
            mean=float(pm[col].mean()), variance=float(pm[col].var())
        )
    return out, alphas


# --------------------------------------------------------------------------
# match_odds: synthetic generator (until the live scraper exists)
# --------------------------------------------------------------------------

def synthesize_odds(
    match_players: pd.DataFrame, alphas: dict[str, float], vig: float = 0.05
) -> pd.DataFrame:
    """Position-aware synthetic odds with a fixed margin — a stand-in for a book.

    Each line is priced off the base rate *within the player's position group*
    (the mean λ for GK/DEF/MID/FWD), then shortened by ``vig`` so the booksum is
    ``1 + vig``. Pricing per position is what stops the market being trivially
    beatable (a real book obviously prices a striker's shot line differently from
    a centre-back's). The residual edge the model can still find is the gap
    between a *specific* player's λ and their positional average — a realistic,
    fully reproducible market to validate the value pipeline and backtest against.

    NOTE: this is a soft synthetic book, NOT a claim of real-world edge. Replace
    ``match_odds.parquet`` with scraped Pinnacle quotes for live analysis.
    """
    pos_col = "position_group" if "position_group" in match_players.columns else None
    rows = []
    for market, spec in MARKETS.items():
        lam_col = f"lam_{market}"
        if lam_col not in match_players.columns:
            continue
        alpha = alphas.get(market, 0.0)
        # Reference λ per position group (fallback to global mean).
        if pos_col:
            grp = match_players.groupby(pos_col)[lam_col].mean()
        global_lambda = float(match_players[lam_col].mean())

        for line in spec["lines"]:
            for side in SIDES:
                sub = match_players[["match_id", "player_id"]].copy()
                if pos_col:
                    ref_lambda = match_players[pos_col].map(grp).fillna(global_lambda)
                else:
                    ref_lambda = pd.Series(global_lambda, index=match_players.index)
                # Vectorized reference probability per row's positional λ.
                p_ref, _ = _ou_probs_vec(
                    ref_lambda.to_numpy(dtype=float), alpha, float(line),
                    pd.Series(side, index=match_players.index),
                )
                p_ref = np.clip(p_ref, 1e-6, 1 - 1e-9)
                sub["market"] = market
                sub["line"] = line
                sub["side"] = side
                sub["bookmaker"] = "synthetic"
                sub["odds"] = np.round((1.0 / p_ref) / (1.0 + vig), 3)
                sub["ts"] = pd.Timestamp.now("UTC").tz_localize(None)
                rows.append(sub)
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


# --------------------------------------------------------------------------
# match_value: join predictions + odds + betting math + realized result
# --------------------------------------------------------------------------

def _ou_probs_vec(lam: np.ndarray, alpha: float, line: float, side: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """Vectorized over/under model probability and push probability.

    Same semantics as :func:`lib.betting.negbin_over_under` but evaluated over a
    whole λ array at once (scipy's cdf/pmf are vectorized). Returns
    ``(p_side, p_push)`` aligned to ``lam``.
    """
    floor = int(np.floor(line))
    is_int = float(line).is_integer()
    if alpha <= 0:
        cdf_floor = poisson.cdf(floor, lam)
        cdf_floor_m1 = poisson.cdf(floor - 1, lam) if floor >= 1 else np.zeros_like(lam)
        pmf_floor = poisson.pmf(floor, lam)
    else:
        n = 1.0 / alpha
        p = 1.0 / (1.0 + alpha * lam)
        cdf_floor = nbinom.cdf(floor, n, p)
        cdf_floor_m1 = nbinom.cdf(floor - 1, n, p) if floor >= 1 else np.zeros_like(lam)
        pmf_floor = nbinom.pmf(floor, n, p)

    p_over = 1.0 - cdf_floor
    if is_int:
        p_push = pmf_floor
        p_under = cdf_floor_m1
    else:
        p_push = np.zeros_like(lam)
        p_under = cdf_floor
    is_over = (side.values == "over")
    p_side = np.where(is_over, p_over, p_under)
    return p_side, p_push


def build_match_value(
    match_players: pd.DataFrame,
    match_odds: pd.DataFrame,
    alphas: dict[str, float],
    kelly_frac: float = 0.25,
) -> pd.DataFrame:
    """Join λ predictions with odds; compute EV/Kelly and the realized result.

    Fully vectorized per (market) group — EV/Kelly/edge are closed-form and the
    over/under probabilities use scipy's array CDFs (see :func:`_ou_probs_vec`).
    """
    if len(match_odds) == 0:
        return pd.DataFrame()

    lam_cols = [f"lam_{m}" for m in MARKETS if f"lam_{m}" in match_players.columns]
    actual_cols = [f"actual_{m}" for m in MARKETS if f"actual_{m}" in match_players.columns]
    keep = ["match_id", "player_id", "player_name", "date", "competition_id",
            "season", "team_id", "opponent_id", "position_group"]
    keep = [c for c in keep if c in match_players.columns]
    mp = match_players[keep + lam_cols + actual_cols]

    df = match_odds.merge(mp, on=["match_id", "player_id"], how="inner")

    records = []
    for market in MARKETS:
        lam_col, actual_col = f"lam_{market}", f"actual_{market}"
        if lam_col not in df.columns:
            continue
        alpha = alphas.get(market, 0.0)
        for line, sub in df[df["market"] == market].groupby("line"):
            sub = sub.copy()
            lam = sub[lam_col].astype(float).values
            p_side, p_push = _ou_probs_vec(lam, alpha, float(line), sub["side"])
            odds = sub["odds"].astype(float).values
            p_lose = 1.0 - p_side - p_push
            b = odds - 1.0

            sub["p_model"] = p_side
            sub["p_push"] = p_push
            sub["implied_prob"] = 1.0 / odds
            sub["edge"] = p_side - 1.0 / odds
            sub["ev"] = p_side * b - p_lose
            kelly_full = np.clip((p_side * b - p_lose) / b, 0.0, None)
            sub["kelly_full"] = kelly_full
            sub[f"kelly_{int(kelly_frac*100)}pct"] = kelly_full * kelly_frac

            # Realized result for backtesting: did the chosen side win?
            actual = sub[actual_col].astype(float).values
            ln = float(line)
            over_win = actual > ln
            push = actual == ln  # only possible on integer lines
            won = np.where(sub["side"].values == "over", over_win, ~over_win)
            sub["actual"] = actual
            sub["won"] = np.where(push, np.nan, won)
            records.append(sub)

    if not records:
        return pd.DataFrame()
    out = pd.concat(records, ignore_index=True)
    return out.sort_values("ev", ascending=False).reset_index(drop=True)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Build the match-centric betting view.")
    parser.add_argument("--source", default="statsbomb", choices=list(SOURCES),
                        help="Player-match table to build from (default: statsbomb).")
    parser.add_argument("--synthetic", action="store_true",
                        help="Generate synthetic population-priced odds + match_value "
                             "(so the pipeline runs before the live scraper exists).")
    parser.add_argument("--vig", type=float, default=0.05,
                        help="Bookmaker margin for synthetic odds (default: 0.05).")
    parser.add_argument("--kelly-frac", type=float, default=0.25,
                        help="Fractional-Kelly multiplier for the value table (default: 0.25).")
    args = parser.parse_args()

    src = SOURCES[args.source]
    pm = read_parquet(src)
    print(f"Loaded {len(pm):,} player-match rows from {src.name}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    fixtures = build_fixtures(pm)
    write_parquet(fixtures, OUT_DIR / "fixtures.parquet")
    n_up = int((fixtures["status"] == "upcoming").sum())
    print(f"  fixtures      {len(fixtures):>6,} matches ({n_up} upcoming) -> fixtures.parquet")

    match_players, alphas = build_match_players(pm)
    write_parquet(match_players, OUT_DIR / "match_players.parquet")
    print(f"  match_players {len(match_players):>6,} rows x {len(match_players.columns)} cols "
          f"-> match_players.parquet")
    print(f"                dispersion alpha per market: "
          + ", ".join(f"{m}={a:.3f}" for m, a in alphas.items()))

    if args.synthetic:
        match_odds = synthesize_odds(match_players, alphas, vig=args.vig)
        write_parquet(match_odds, OUT_DIR / "match_odds.parquet")
        print(f"  match_odds    {len(match_odds):>6,} synthetic quotes (vig={args.vig}) "
              f"-> match_odds.parquet")

        match_value = build_match_value(match_players, match_odds, alphas,
                                        kelly_frac=args.kelly_frac)
        write_parquet(match_value, OUT_DIR / "match_value.parquet")
        pos_ev = int((match_value["ev"] > 0).sum()) if len(match_value) else 0
        print(f"  match_value   {len(match_value):>6,} priced bets ({pos_ev} with EV>0) "
              f"-> match_value.parquet")
    else:
        print("  (no --synthetic: match_odds / match_value left for the live scraper "
              "to populate)")

    print("\nDone. Betting view in 02_data_processed/matches_view/")


if __name__ == "__main__":
    main()
