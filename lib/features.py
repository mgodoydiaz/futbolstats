r"""Feature engineering for per-match player models.

All rolling and expanding stats use `shift(1)` to ensure features at row $t$
only see data from $t-1$ and earlier. Without that shift, the model gets to
peek at the target — classic data leakage.

The standard recipe:

    df = add_match_features(df, target='shots', group='player_id', date='date')

produces, for each player-match row, a set of features that describe the
player's recent and career-long performance \emph{before} the current match.
"""
from __future__ import annotations

from typing import Iterable

import pandas as pd


def add_rolling_features(
    df: pd.DataFrame,
    target_col: str,
    group_col: str = "player_id",
    sort_col: str = "date",
    windows: Iterable[int] = (3, 5, 10),
) -> pd.DataFrame:
    """Add `roll_<target>_<w>` columns for each window.

    Each value at row $t$ is the mean of `target_col` over the previous `w`
    rows (exclusive of $t$), within the same `group_col` group.
    """
    df = df.sort_values([group_col, sort_col]).copy()
    for w in windows:
        df[f"roll_{target_col}_{w}"] = (
            df.groupby(group_col)[target_col]
              .transform(lambda s: s.shift(1).rolling(w, min_periods=1).mean())
        )
    return df


def add_career_mean(
    df: pd.DataFrame,
    target_col: str,
    group_col: str = "player_id",
    sort_col: str = "date",
) -> pd.DataFrame:
    """Add `career_<target>` column: expanding mean strictly before current row."""
    df = df.sort_values([group_col, sort_col]).copy()
    df[f"career_{target_col}"] = (
        df.groupby(group_col)[target_col]
          .transform(lambda s: s.shift(1).expanding().mean())
    )
    return df


def add_days_rest(
    df: pd.DataFrame,
    group_col: str = "player_id",
    date_col: str = "date",
) -> pd.DataFrame:
    """Add `days_rest` column: days since this player's previous match."""
    df = df.sort_values([group_col, date_col]).copy()
    df["days_rest"] = (
        df.groupby(group_col)[date_col]
          .transform(lambda s: (s - s.shift(1)).dt.days)
    )
    return df


def add_minutes_rolling(
    df: pd.DataFrame,
    group_col: str = "player_id",
    sort_col: str = "date",
    window: int = 5,
) -> pd.DataFrame:
    """Recent minutes load. Captures rotation effects."""
    if "minutes_played" not in df.columns:
        return df
    df = df.sort_values([group_col, sort_col]).copy()
    df[f"roll_minutes_{window}"] = (
        df.groupby(group_col)["minutes_played"]
          .transform(lambda s: s.shift(1).rolling(window, min_periods=1).mean())
    )
    return df


def add_opponent_features(
    df: pd.DataFrame,
    target_col: str,
    team_col: str = "team_id",
    opponent_col: str = "opponent_id",
    match_col: str = "match_id",
    date_col: str = "date",
    windows: Iterable[int] = (5, 10),
) -> pd.DataFrame:
    """Add `opp_allows_<target>_<w>` columns: rolling mean of what the opponent
    typically *concedes* over their previous `w` matches.

    Computation:
        1. team_match: sum target per (match, team). What team produced.
        2. conceded[T, M] = total_target[M] - team_total[T, M].  (Two-team game.)
        3. Rolling mean of conceded over team's previous matches (shifted by 1).
        4. Join back to player-match by (match, opponent).
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    team_match = (
        df.groupby([match_col, team_col, date_col], as_index=False)[target_col]
          .sum()
    )
    match_totals = df.groupby(match_col)[target_col].sum()
    team_match["__conceded"] = team_match[match_col].map(match_totals) - team_match[target_col]

    team_match = team_match.sort_values([team_col, date_col])
    new_cols = []
    for w in windows:
        col = f"opp_allows_{target_col}_{w}"
        team_match[col] = (
            team_match.groupby(team_col)["__conceded"]
                      .transform(lambda s: s.shift(1).rolling(w, min_periods=1).mean())
        )
        new_cols.append(col)

    opp_join = team_match[[match_col, team_col] + new_cols].rename(columns={team_col: opponent_col})
    df = df.merge(opp_join, on=[match_col, opponent_col], how="left")
    return df


def add_match_features(
    df: pd.DataFrame,
    target_col: str,
    group_col: str = "player_id",
    date_col: str = "date",
    windows: Iterable[int] = (3, 5, 10),
    with_opponent: bool = False,
) -> pd.DataFrame:
    """High-level wrapper that adds the standard match-context features.

    Adds:
        - roll_<target>_<w> for each w in `windows`
        - career_<target> (expanding mean)
        - days_rest
        - roll_minutes_5
    Ensures `date_col` is datetime.
    """
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    df = add_rolling_features(df, target_col, group_col, date_col, windows)
    df = add_career_mean(df, target_col, group_col, date_col)
    df = add_days_rest(df, group_col, date_col)
    df = add_minutes_rolling(df, group_col, date_col)
    if with_opponent:
        df = add_opponent_features(df, target_col, date_col=date_col)
    return df
