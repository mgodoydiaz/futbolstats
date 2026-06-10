"""Unit tests for lib.betting — odds math, count O/U distributions, EV, Kelly.

Run from the project root:

    python -m pytest tests/test_betting.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import poisson

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from lib.betting import (  # noqa: E402
    american_to_decimal,
    annotate_bet,
    booksum,
    decimal_to_american,
    dispersion_from_moments,
    edge,
    expected_value,
    fair_odds,
    fractional_to_decimal,
    implied_prob,
    kelly_fraction,
    negbin_over_under,
    poisson_over_under,
    remove_vig,
    two_way_no_vig,
    vectorized_ev,
)

APPROX = dict(rel=1e-9, abs=1e-12)


# --------------------------------------------------------------------------
# Odds conversion
# --------------------------------------------------------------------------


def test_american_to_decimal_known_values():
    assert american_to_decimal(150) == pytest.approx(2.50)
    assert american_to_decimal(-200) == pytest.approx(1.50)
    assert american_to_decimal(100) == pytest.approx(2.00)
    assert american_to_decimal(-110) == pytest.approx(1.0 + 100 / 110)


def test_american_decimal_roundtrip():
    for a in (150, -200, 250, -110, 100, -150):
        assert decimal_to_american(american_to_decimal(a)) == pytest.approx(a)


def test_decimal_to_american_pivot_at_two():
    assert decimal_to_american(2.0) == pytest.approx(100.0)
    assert decimal_to_american(3.0) == pytest.approx(200.0)
    assert decimal_to_american(1.5) == pytest.approx(-200.0)


def test_fractional_to_decimal():
    assert fractional_to_decimal("7/2") == pytest.approx(4.5)
    assert fractional_to_decimal((1, 1)) == pytest.approx(2.0)
    assert fractional_to_decimal("10/11") == pytest.approx(1.0 + 10 / 11)


def test_invalid_odds_raise():
    with pytest.raises(ValueError):
        american_to_decimal(0)
    with pytest.raises(ValueError):
        decimal_to_american(1.0)
    with pytest.raises(ValueError):
        implied_prob(0.5)
    with pytest.raises(ValueError):
        fractional_to_decimal("1/0")


# --------------------------------------------------------------------------
# Implied prob, fair odds, vig
# --------------------------------------------------------------------------


def test_implied_prob_and_fair_odds_inverse():
    for d in (1.5, 2.0, 3.3, 10.0):
        p = implied_prob(d)
        assert fair_odds(p) == pytest.approx(d)


def test_booksum_overround():
    # A balanced book at 1.90/1.90 carries ~5.26% margin.
    assert booksum([1.90, 1.90]) == pytest.approx(2 / 1.90)
    assert booksum([1.90, 1.90]) > 1.0


def test_remove_vig_proportional_sums_to_one():
    probs = remove_vig([1.90, 1.90])
    assert sum(probs) == pytest.approx(1.0)
    assert probs[0] == pytest.approx(0.5)
    assert probs[1] == pytest.approx(0.5)


def test_remove_vig_asymmetric():
    # Favourite/underdog: devigged favourite prob should exceed raw-normalised.
    probs = remove_vig([1.40, 3.00])
    assert sum(probs) == pytest.approx(1.0)
    assert probs[0] > probs[1]


def test_remove_vig_power_sums_to_one():
    probs = remove_vig([1.40, 3.00], method="power")
    assert sum(probs) == pytest.approx(1.0, abs=1e-6)


def test_remove_vig_unknown_method():
    with pytest.raises(ValueError):
        remove_vig([1.9, 1.9], method="bananas")


def test_two_way_no_vig_matches_remove_vig():
    a, b = two_way_no_vig(1.83, 2.05)
    p = remove_vig([1.83, 2.05])
    assert a == pytest.approx(p[0])
    assert b == pytest.approx(p[1])


# --------------------------------------------------------------------------
# Poisson over/under
# --------------------------------------------------------------------------


def test_poisson_half_line_no_push():
    ou = poisson_over_under(lam=2.3, line=2.5)
    assert ou.p_push == 0.0
    assert ou.p_over + ou.p_under == pytest.approx(1.0)
    # Over 2.5 ⇔ Y >= 3
    assert ou.p_over == pytest.approx(1.0 - poisson.cdf(2, 2.3))
    assert ou.p_under == pytest.approx(poisson.cdf(2, 2.3))


def test_poisson_integer_line_has_push():
    ou = poisson_over_under(lam=2.0, line=2.0)
    assert ou.p_push == pytest.approx(poisson.pmf(2, 2.0))
    assert ou.p_over + ou.p_under + ou.p_push == pytest.approx(1.0)
    assert ou.p_over == pytest.approx(1.0 - poisson.cdf(2, 2.0))
    assert ou.p_under == pytest.approx(poisson.cdf(1, 2.0))


def test_poisson_zero_line():
    # Over 0.5 ⇔ at least one event.
    ou = poisson_over_under(lam=1.0, line=0.5)
    assert ou.p_over == pytest.approx(1.0 - poisson.pmf(0, 1.0))
    assert ou.p_under == pytest.approx(poisson.pmf(0, 1.0))


def test_poisson_prob_accessor():
    ou = poisson_over_under(lam=2.3, line=2.5)
    assert ou.prob("over") == ou.p_over
    assert ou.prob("under") == ou.p_under
    with pytest.raises(ValueError):
        ou.prob("sideways")


def test_poisson_negative_lambda_raises():
    with pytest.raises(ValueError):
        poisson_over_under(lam=-1.0, line=2.5)


# --------------------------------------------------------------------------
# Negative binomial over/under
# --------------------------------------------------------------------------


def test_negbin_reduces_to_poisson_when_alpha_zero():
    nb = negbin_over_under(mu=2.3, alpha=0.0, line=2.5)
    ps = poisson_over_under(lam=2.3, line=2.5)
    assert nb.p_over == pytest.approx(ps.p_over)
    assert nb.p_under == pytest.approx(ps.p_under)


def test_negbin_overdispersion_fattens_tails():
    # With var > mean, more mass in the tails ⇒ higher P(over) on a high line.
    line = 5.5
    ps = poisson_over_under(lam=2.5, line=line)
    nb = negbin_over_under(mu=2.5, alpha=0.5, line=line)
    assert nb.p_over > ps.p_over


def test_negbin_probs_sum_to_one():
    nb = negbin_over_under(mu=3.0, alpha=0.3, line=2.0)
    assert nb.p_over + nb.p_under + nb.p_push == pytest.approx(1.0)


def test_dispersion_from_moments():
    # var = mean ⇒ alpha 0 (Poisson). var > mean ⇒ positive alpha.
    assert dispersion_from_moments(mean=2.0, variance=2.0) == pytest.approx(0.0)
    assert dispersion_from_moments(mean=2.0, variance=4.0) == pytest.approx(0.5)
    # Underdispersed sample floors at 0.
    assert dispersion_from_moments(mean=2.0, variance=1.0) == 0.0


# --------------------------------------------------------------------------
# Expected value & Kelly
# --------------------------------------------------------------------------


def test_ev_fair_bet_is_zero():
    # True prob = implied prob ⇒ EV exactly 0.
    assert expected_value(0.5, 2.0) == pytest.approx(0.0)
    assert expected_value(1 / 3, 3.0) == pytest.approx(0.0)


def test_ev_positive_when_model_beats_price():
    assert expected_value(0.55, 2.0) == pytest.approx(0.10)
    assert expected_value(0.40, 3.0) == pytest.approx(0.20)


def test_ev_with_push():
    # 10% push: stake returned, so lose prob is smaller.
    ev = expected_value(p_win=0.45, decimal_odds=2.0, p_push=0.10)
    # 0.45*(1.0) - (1 - 0.45 - 0.10) = 0.45 - 0.45 = 0.0
    assert ev == pytest.approx(0.0)


def test_kelly_fair_bet_zero_stake():
    assert kelly_fraction(0.5, 2.0) == pytest.approx(0.0)


def test_kelly_positive_edge():
    # p=0.6, d=2.0, b=1 ⇒ f* = (0.6*1 - 0.4)/1 = 0.2
    assert kelly_fraction(0.6, 2.0) == pytest.approx(0.2)


def test_kelly_negative_edge_clamped():
    assert kelly_fraction(0.4, 2.0) == 0.0


def test_kelly_fractional_scaling():
    full = kelly_fraction(0.6, 2.0, fraction=1.0)
    quarter = kelly_fraction(0.6, 2.0, fraction=0.25)
    assert quarter == pytest.approx(0.25 * full)


def test_kelly_fraction_bounds():
    with pytest.raises(ValueError):
        kelly_fraction(0.6, 2.0, fraction=1.5)


def test_edge_sign():
    assert edge(0.6, 2.0) == pytest.approx(0.1)   # 0.6 - 0.5
    assert edge(0.4, 2.0) == pytest.approx(-0.1)


def test_annotate_bet_keys_and_values():
    out = annotate_bet(p_model=0.6, decimal_odds=2.0, kelly_frac=0.25)
    assert set(out) == {"p_model", "implied_prob", "edge", "ev", "kelly_full", "kelly_scaled"}
    assert out["ev"] == pytest.approx(0.2)
    assert out["kelly_full"] == pytest.approx(0.2)
    assert out["kelly_scaled"] == pytest.approx(0.05)


def test_vectorized_ev_matches_scalar():
    p = [0.5, 0.55, 0.4]
    d = [2.0, 2.0, 3.0]
    out = vectorized_ev(p, d)
    expected = np.array([expected_value(pi, di) for pi, di in zip(p, d)])
    assert np.allclose(out, expected)


def test_vectorized_ev_rejects_bad_odds():
    with pytest.raises(ValueError):
        vectorized_ev([0.5], [1.0])
