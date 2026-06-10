r"""Betting math for player-prop value detection.

Pure functions — no I/O, no network, no global state. Everything here turns a
*model probability* and a *bookmaker price* into the quantities you need to
decide whether a bet has positive expected value:

    odds  ──► implied probability ──► (remove vig) ──► fair market probability
    model prediction (λ or μ) ──► P(Y over/under line)   [Poisson / NegBin]
    p_model & odds ──► expected value, Kelly stake

Conventions
-----------
- **Decimal odds** are the canonical internal representation. European decimal
  odds ``d`` pay ``d`` units total (stake included) per unit staked on a win.
  Convert American / fractional at the edges with the helpers below.
- **Probabilities** are floats in ``[0, 1]``.
- **Expected value** ``ev`` is *per unit staked*: ``ev = p * d - 1``. ``ev > 0``
  means the bet is +EV under the model. ``ev = 0.05`` ⇒ +5 % edge.
- **Lines** follow standard over/under semantics. A ``2.5`` line can't push; an
  integer line like ``2.0`` pushes (stake returned) when the stat lands exactly.

For the count distributions: a player's shots/tackles/cards per match are counts
with many zeros. Poisson assumes ``var = mean``; real football counts are
usually over-dispersed (``var > mean``), so a Negative-Binomial with a fitted
dispersion ``alpha`` is the more honest model — see :func:`negbin_over_under`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
from scipy.stats import nbinom, poisson

# --------------------------------------------------------------------------
# Odds format conversion
# --------------------------------------------------------------------------


def american_to_decimal(american: float) -> float:
    """American (moneyline) odds → decimal odds.

    ``+150`` → ``2.50``; ``-200`` → ``1.50``. Zero is undefined.
    """
    a = float(american)
    if a == 0:
        raise ValueError("American odds cannot be 0")
    return 1.0 + (a / 100.0 if a > 0 else 100.0 / -a)


def decimal_to_american(decimal: float) -> float:
    """Decimal odds → American (moneyline) odds."""
    d = float(decimal)
    if d <= 1.0:
        raise ValueError(f"decimal odds must be > 1, got {d}")
    return (d - 1.0) * 100.0 if d >= 2.0 else -100.0 / (d - 1.0)


def fractional_to_decimal(fractional: str | tuple[float, float]) -> float:
    """Fractional odds → decimal odds.

    Accepts ``"7/2"`` or ``(7, 2)``. ``7/2`` → ``4.5``.
    """
    if isinstance(fractional, str):
        num, den = (float(x) for x in fractional.split("/"))
    else:
        num, den = float(fractional[0]), float(fractional[1])
    if den == 0:
        raise ValueError("fractional denominator cannot be 0")
    return 1.0 + num / den


# --------------------------------------------------------------------------
# Implied probability & vig
# --------------------------------------------------------------------------


def implied_prob(decimal_odds: float) -> float:
    """Decimal odds → implied probability (still includes the bookmaker's vig)."""
    d = float(decimal_odds)
    if d <= 1.0:
        raise ValueError(f"decimal odds must be > 1, got {d}")
    return 1.0 / d


def fair_odds(prob: float) -> float:
    """Probability → fair decimal odds (no margin). Inverse of :func:`implied_prob`."""
    p = float(prob)
    if not 0.0 < p <= 1.0:
        raise ValueError(f"prob must be in (0, 1], got {p}")
    return 1.0 / p


def booksum(decimal_odds: Sequence[float]) -> float:
    """Sum of implied probabilities across all outcomes of a market.

    ``> 1`` by the overround (vig). A 2-way market at ``1.90 / 1.90`` sums to
    ``1.053`` → a 5.3 % book margin.
    """
    return float(sum(implied_prob(d) for d in decimal_odds))


def remove_vig(decimal_odds: Sequence[float], method: str = "proportional") -> list[float]:
    """Strip the bookmaker margin, returning fair probabilities that sum to 1.

    Parameters
    ----------
    decimal_odds
        All outcomes of one market (e.g. ``[over_odds, under_odds]``).
    method
        ``"proportional"`` (a.k.a. multiplicative): divide each implied prob by
        the booksum. Simple and standard. ``"power"``: solve for the exponent
        ``k`` such that ``sum(p_i ** k) == 1`` — reduces the favourite-longshot
        bias the proportional method leaves in place.

    Returns
    -------
    list[float]
        Devigged probabilities, same order as ``decimal_odds``, summing to 1.
    """
    raw = np.array([implied_prob(d) for d in decimal_odds], dtype=float)
    if method == "proportional":
        return list(raw / raw.sum())
    if method == "power":
        # Find k in (0, 1] so that sum(raw**k) == 1. Monotonic in k → bisection.
        lo, hi = 1e-6, 1.0
        for _ in range(100):
            mid = 0.5 * (lo + hi)
            if np.sum(raw ** mid) > 1.0:
                lo = mid
            else:
                hi = mid
        k = 0.5 * (lo + hi)
        out = raw ** k
        return list(out / out.sum())
    raise ValueError(f"unknown method: {method!r} (use 'proportional' or 'power')")


def two_way_no_vig(over_odds: float, under_odds: float, method: str = "proportional") -> tuple[float, float]:
    """Convenience: devig a 2-way over/under market → ``(p_over_fair, p_under_fair)``."""
    p_over, p_under = remove_vig([over_odds, under_odds], method=method)
    return p_over, p_under


# --------------------------------------------------------------------------
# Over/under probabilities from a count model
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class OverUnder:
    """Probabilities for an over/under line on a count target.

    ``p_over + p_under + p_push == 1``. ``p_push`` is 0 for half-lines (e.g. 2.5)
    and equals ``P(Y == line)`` for integer lines.
    """

    p_over: float
    p_under: float
    p_push: float
    line: float
    mean: float

    def prob(self, side: str) -> float:
        """Return the model probability for ``side`` ∈ {``"over"``, ``"under"``}."""
        s = side.lower()
        if s in ("over", "o"):
            return self.p_over
        if s in ("under", "u"):
            return self.p_under
        raise ValueError(f"side must be 'over' or 'under', got {side!r}")


def _over_under_from_cdf(cdf, pmf, line: float, mean: float) -> OverUnder:
    """Generic over/under split given a count distribution's ``cdf`` and ``pmf``.

    ``cdf(k) = P(Y <= k)``, ``pmf(k) = P(Y == k)``. Over wins on ``Y`` strictly
    above the line; for integer lines an exact landing pushes.
    """
    if line < 0:
        raise ValueError(f"line must be >= 0, got {line}")
    floor = int(np.floor(line))
    is_integer = float(line).is_integer()
    if is_integer:
        p_push = float(pmf(floor))
        p_over = float(1.0 - cdf(floor))            # Y >= floor + 1
        p_under = float(cdf(floor - 1)) if floor >= 1 else 0.0  # Y <= floor - 1
    else:
        p_push = 0.0
        p_over = float(1.0 - cdf(floor))            # Y >= floor + 1
        p_under = float(cdf(floor))                 # Y <= floor
    return OverUnder(
        p_over=p_over, p_under=p_under, p_push=p_push, line=float(line), mean=float(mean)
    )


def poisson_over_under(lam: float, line: float) -> OverUnder:
    """Over/under probabilities assuming ``Y ~ Poisson(lam)``.

    ``lam`` is the model's predicted mean count (e.g. expected shots).
    """
    if lam < 0:
        raise ValueError(f"lam must be >= 0, got {lam}")
    return _over_under_from_cdf(
        cdf=lambda k: poisson.cdf(k, lam),
        pmf=lambda k: poisson.pmf(k, lam),
        line=line,
        mean=lam,
    )


def negbin_over_under(mu: float, alpha: float, line: float) -> OverUnder:
    """Over/under probabilities assuming ``Y ~ NegBinomial`` with mean ``mu``.

    Uses the mean/dispersion parameterisation common in count regression:

        ``Var(Y) = mu + alpha * mu**2``

    so ``alpha = 0`` recovers Poisson. Converted to scipy's ``(n, p)`` form via
    ``n = 1 / alpha`` and ``p = 1 / (1 + alpha * mu)``. Prefer this over Poisson
    when the empirical variance of the target exceeds its mean (the usual case
    for shots / tackles / cards).
    """
    if mu < 0:
        raise ValueError(f"mu must be >= 0, got {mu}")
    if alpha < 0:
        raise ValueError(f"alpha must be >= 0, got {alpha}")
    if alpha == 0:
        return poisson_over_under(mu, line)
    n = 1.0 / alpha
    p = 1.0 / (1.0 + alpha * mu)
    return _over_under_from_cdf(
        cdf=lambda k: nbinom.cdf(k, n, p),
        pmf=lambda k: nbinom.pmf(k, n, p),
        line=line,
        mean=mu,
    )


def dispersion_from_moments(mean: float, variance: float) -> float:
    """Estimate NegBinomial ``alpha`` from a target's empirical mean & variance.

    ``alpha = (variance - mean) / mean**2``, floored at 0 (a non-over-dispersed
    sample collapses to Poisson). Feed the result to :func:`negbin_over_under`.
    """
    if mean <= 0:
        return 0.0
    return max(0.0, (variance - mean) / (mean * mean))


# --------------------------------------------------------------------------
# Expected value & staking
# --------------------------------------------------------------------------


def expected_value(p_win: float, decimal_odds: float, p_push: float = 0.0) -> float:
    """Expected value per unit staked.

    Without push: ``ev = p_win * d - 1``. With a push probability the stake is
    returned on a push, so the lose probability shrinks:

        ``ev = p_win * (d - 1) - p_lose``,   ``p_lose = 1 - p_win - p_push``

    ``ev > 0`` ⇒ +EV bet. Returns the edge as a fraction of stake.
    """
    d = float(decimal_odds)
    if d <= 1.0:
        raise ValueError(f"decimal odds must be > 1, got {d}")
    p_lose = 1.0 - p_win - p_push
    return p_win * (d - 1.0) - p_lose


def kelly_fraction(
    p_win: float, decimal_odds: float, fraction: float = 1.0, p_push: float = 0.0
) -> float:
    """Fraction of bankroll to stake by the Kelly criterion.

    ``f* = (p_win * b - p_lose) / b`` with ``b = d - 1`` (net odds) and
    ``p_lose = 1 - p_win - p_push``. Negative edge → 0 (don't bet). ``fraction``
    scales the result: pass ``0.25`` for quarter-Kelly, the practical default
    that tames the brutal drawdowns of full Kelly when ``p_win`` is uncertain.
    """
    d = float(decimal_odds)
    if d <= 1.0:
        raise ValueError(f"decimal odds must be > 1, got {d}")
    if not 0.0 <= fraction <= 1.0:
        raise ValueError(f"fraction must be in [0, 1], got {fraction}")
    b = d - 1.0
    p_lose = 1.0 - p_win - p_push
    f_star = (p_win * b - p_lose) / b
    return max(0.0, f_star) * fraction


def edge(p_model: float, decimal_odds: float) -> float:
    """Model probability minus the (vig-inclusive) implied probability.

    A quick sanity signal: positive means the model is more bullish than the
    raw price. Not the same as EV — use :func:`expected_value` to size a bet.
    """
    return float(p_model) - implied_prob(decimal_odds)


def annotate_bet(
    p_model: float,
    decimal_odds: float,
    p_push: float = 0.0,
    kelly_frac: float = 0.25,
) -> dict[str, float]:
    """Bundle the decision metrics for one (probability, price) pair.

    Returns a dict ready to drop into a DataFrame column-set:
    ``implied_prob``, ``edge``, ``ev``, ``kelly_full``, ``kelly_scaled``.
    No threshold is applied — the caller decides what counts as a bet.
    """
    return {
        "p_model": float(p_model),
        "implied_prob": implied_prob(decimal_odds),
        "edge": edge(p_model, decimal_odds),
        "ev": expected_value(p_model, decimal_odds, p_push=p_push),
        "kelly_full": kelly_fraction(p_model, decimal_odds, 1.0, p_push=p_push),
        "kelly_scaled": kelly_fraction(p_model, decimal_odds, kelly_frac, p_push=p_push),
    }


def vectorized_ev(p_model: Iterable[float], decimal_odds: Iterable[float]) -> np.ndarray:
    """EV for aligned arrays of model probabilities and decimal odds (no push)."""
    p = np.asarray(list(p_model), dtype=float)
    d = np.asarray(list(decimal_odds), dtype=float)
    if np.any(d <= 1.0):
        raise ValueError("all decimal odds must be > 1")
    return p * d - 1.0
