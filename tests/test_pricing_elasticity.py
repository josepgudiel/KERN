"""Path A pricing math — elasticity-scaled price tests.

Regression cover for the monopoly optimal-markup bug: p*(e/(e+1)) is only valid for
elastic demand (e < -1), but Path A is gated to inelastic demand (-0.7 < e <= 0), so the
formula went negative and every recommendation collapsed to the downstream $0.25 floor.

Path A does not currently fire end-to-end on either demo dataset (Drip Coffee is the only
product reaching the calculation, and it dies at the min_impact gate — pre-existing and out
of scope here), so these exercise the pricing math directly.
"""
from __future__ import annotations

import pytest

from backend.engine.pricing_core import _elasticity_test_price

# Drip Coffee's real average price in the coffee demo dataset — the one product whose
# elasticity fit clears the valid/significant/price_tolerant gates.
DRIP_COFFEE_PRICE = 2.34

# Spans the price_tolerant gate: near-zero inelastic through the -0.7 edge.
SWEEP = [-0.01, -0.05, -0.2, -0.4, -0.69]

FLOOR = 0.05


@pytest.mark.parametrize("e", SWEEP)
def test_suggested_price_always_exceeds_current(e: float) -> None:
    """A price *test* must be a raise — the old formula returned negatives here."""
    suggested, increase = _elasticity_test_price(DRIP_COFFEE_PRICE, e)
    assert suggested > DRIP_COFFEE_PRICE
    assert increase > 0


@pytest.mark.parametrize("e", SWEEP)
def test_floor_does_not_bind(e: float) -> None:
    """The $0.05 floor is a sub-penny guard, not the operative value at realistic prices."""
    _, increase = _elasticity_test_price(DRIP_COFFEE_PRICE, e)
    assert increase > FLOOR, f"floor bound at e={e}: increase={increase:.4f}"


def test_increase_varies_with_elasticity() -> None:
    """The bug's signature was a constant increase regardless of e. It must now scale."""
    increases = [_elasticity_test_price(DRIP_COFFEE_PRICE, e)[1] for e in SWEEP]

    assert len(set(round(i, 4) for i in increases)) == len(SWEEP), (
        f"increase collapsed to repeated values: {increases}"
    )
    # Monotonic: more elastic demand -> smaller test.
    assert increases == sorted(increases, reverse=True)
    # And the spread is meaningful, not floating-point noise.
    assert increases[0] - increases[-1] > 0.10


def test_bump_stays_within_declared_band() -> None:
    """Test size must stay inside the documented 4%-12% band across the whole gate."""
    for e in SWEEP:
        _, increase = _elasticity_test_price(DRIP_COFFEE_PRICE, e)
        pct = increase / DRIP_COFFEE_PRICE
        assert 0.04 <= pct <= 0.12, f"e={e} produced a {pct:.1%} bump"


def test_positive_slope_fits_are_clamped_to_zero() -> None:
    """price_tolerant is `slope > -0.7` with no upper bound, so noisy positive fits pass it.

    They must be treated as fully inelastic (max 12%), never extrapolated beyond it.
    """
    at_zero, inc_zero = _elasticity_test_price(DRIP_COFFEE_PRICE, 0.0)
    for noisy in (0.195, 1.806, 3.563):  # real positive fits seen in the coffee demo
        assert _elasticity_test_price(DRIP_COFFEE_PRICE, noisy) == (at_zero, inc_zero)
    assert inc_zero / DRIP_COFFEE_PRICE == pytest.approx(0.12)


def test_absolute_and_relative_caps_still_apply() -> None:
    """Expensive items stay bounded by the $2.00 / 25% clamps the fix left in place."""
    _, increase = _elasticity_test_price(100.00, 0.0)  # 12% of $100 = $12, clamped to $2
    assert increase == 2.00


def test_rounds_to_nearest_nickel() -> None:
    for e in SWEEP:
        suggested, _ = _elasticity_test_price(DRIP_COFFEE_PRICE, e)
        assert round(suggested * 20) == pytest.approx(suggested * 20)
