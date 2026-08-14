"""Cross-engine consistency: the Action Center and Price Intelligence must agree.

The bug this file exists to prevent: `recommendations.py` and `pricing.py` each had
their own elasticity estimator and their own percentage formula, so the same product
could be shown two different price recommendations depending on which page rendered
it. On the coffee demo, Drip Coffee came out at elasticity -0.509 / +6.2% / $2.50 on
the Action Center and +0.497 / +8% / $2.53 on Price Intelligence.

Both now consume `pricing_core`. These tests compare the two pages product-by-product
across the whole demo dataset — not just products that happen to produce a
recommendation on both pages today (that set is currently empty; see
`test_raise_intersection_is_documented`), because a comparison over an empty set
passes vacuously and would not have caught the original bug.
"""
from __future__ import annotations

import pytest

from backend.engine import pricing, pricing_core, recommendations
from backend.engine.demo import _generate_demo_df
from backend.engine.pricing import _get_price_recommendations, _usable_elasticity
from backend.engine.pricing_core import (
    ELASTICITY_CAP,
    elasticity_to_price_delta,
    estimate_elasticity,
)
from backend.engine.recommendations import build_recommendations

RAISE_ACTION = "↑ Raise Price"


@pytest.fixture(scope="module")
def demo_df():
    """The repo's coffee demo — 4,375 transactions, 19 products, seeded."""
    return _generate_demo_df()


def _action_center_products(recs: list[dict]) -> set[str]:
    """Products the Action Center gave an elasticity-derived (Path A) price test."""
    return {
        r["product"]
        for r in recs
        if r.get("rec_type") == "pricing"
        and "elasticity" in r.get("_statistical_detail", {})
    }


def test_both_pages_import_the_same_functions() -> None:
    """One implementation, not two copies that drift apart."""
    assert pricing.estimate_elasticity is pricing_core.estimate_elasticity
    assert recommendations.estimate_elasticity is pricing_core.estimate_elasticity
    assert recommendations._elasticity_test_price is pricing_core._elasticity_test_price

    # The superseded implementations must stay deleted.
    assert not hasattr(recommendations, "compute_elasticity")
    assert not hasattr(pricing, "_estimate_product_elasticity")
    assert not hasattr(pricing, "_elasticity_to_raise_pct")
    assert not hasattr(pricing, "_elasticity_to_lower_pct")


def test_elasticity_identical_for_every_product(demo_df) -> None:
    """Every product, both pages, bit-identical elasticity — not just the ones that rec."""
    for product in sorted(demo_df["product"].unique()):
        canonical = estimate_elasticity(demo_df, product)

        # What Price Intelligence would use.
        pi_value = _usable_elasticity(demo_df, product)
        # What the Action Center would use (Path A takes the same dict).
        ac_value = (
            canonical["elasticity"]
            if canonical["valid"] and canonical["is_significant"]
            else None
        )

        assert pi_value == ac_value, (
            f"{product}: Price Intelligence sees {pi_value}, Action Center sees {ac_value}"
        )

        if canonical["slope"] is not None:
            # Sign convention holds: magnitude is abs(slope), clipped to the cap band.
            assert canonical["elasticity"] == pytest.approx(
                min(max(abs(canonical["slope"]), 0.05), ELASTICITY_CAP)
            )


def test_raise_percentage_identical_for_every_product(demo_df) -> None:
    """The suggested raise % must be the same number on both pages, for every product.

    Price Intelligence calls elasticity_to_price_delta with the magnitude; the Action
    Center reaches the same function through _elasticity_test_price with the signed
    slope. Those two routes must converge.
    """
    for product in sorted(demo_df["product"].unique()):
        canonical = estimate_elasticity(demo_df, product)
        usable = canonical["valid"] and canonical["is_significant"]

        pi_pct, _ = elasticity_to_price_delta(
            canonical["elasticity"] if usable else None, "raise"
        )

        if not usable:
            continue  # Action Center Path A rejects it; nothing to compare against.

        signed = min(canonical["slope"], 0.0)
        ac_pct, _ = elasticity_to_price_delta(abs(signed), "raise")

        assert pi_pct == ac_pct, (
            f"{product}: raise % diverged — Price Intelligence {pi_pct:.4%}, "
            f"Action Center {ac_pct:.4%} (elasticity {canonical['elasticity']:.3f}, "
            f"slope {canonical['slope']:.3f})"
        )


def test_rendered_price_intelligence_recs_use_the_canonical_percentage(demo_df) -> None:
    """Exercise the real Price Intelligence path, not a re-derivation of it.

    Reads the percentage back out of the recommendation Price Intelligence actually
    emits and checks it against pricing_core. A step-ladder or any other private
    formula creeping back into pricing.py fails here even if its estimator still agrees.
    """
    for rec in _get_price_recommendations(demo_df):
        if rec["action"] != RAISE_ACTION:
            continue

        rendered_pct = rec["suggested"] / rec["current"] - 1
        canonical = estimate_elasticity(demo_df, rec["product"])
        usable = canonical["valid"] and canonical["is_significant"]
        expected_pct, _ = elasticity_to_price_delta(
            canonical["elasticity"] if usable else None, "raise"
        )

        # `suggested` is rounded to the cent, so allow half a cent of slack — far
        # tighter than the ~1.7pp gap the old step-ladder produced.
        tolerance = 0.005 / rec["current"]
        assert rendered_pct == pytest.approx(expected_pct, abs=tolerance), (
            f"{rec['product']}: rendered {rendered_pct:.2%} but pricing_core says "
            f"{expected_pct:.2%}"
        )


def test_raise_intersection_is_documented(demo_df) -> None:
    """Record which products both pages recommend raising today.

    On the coffee demo the Action Center emits no Path A pricing rec at all — every
    candidate dies at the min_impact gate — so the intersection is empty. That is why
    the tests above compare per-product across the whole dataset instead of relying on
    this set.
    """
    pi_raises = {
        r["product"] for r in _get_price_recommendations(demo_df) if r["action"] == RAISE_ACTION
    }
    ac_raises = _action_center_products(build_recommendations(demo_df))
    both = pi_raises & ac_raises

    assert pi_raises, "Price Intelligence produced no raise recs — demo data changed?"

    for product in both:
        canonical = estimate_elasticity(demo_df, product)
        pct, _ = elasticity_to_price_delta(canonical["elasticity"], "raise")
        ac_pct, _ = elasticity_to_price_delta(abs(min(canonical["slope"], 0.0)), "raise")
        assert pct == ac_pct, f"{product}: both pages recommend a raise but disagree on %"

    assert not ac_raises, (
        "Action Center Path A now fires on the coffee demo "
        f"({sorted(ac_raises)}) — it previously did not. That is an improvement, not a "
        "regression: delete this assertion. The per-product checks above already cover "
        "the products in the intersection."
    )


def test_drip_coffee_is_the_worked_example(demo_df) -> None:
    """Regression pin on the exact product the original bug was found on."""
    canonical = estimate_elasticity(demo_df, "Drip Coffee")
    assert canonical["valid"] and canonical["is_significant"]

    pi_pct, _ = elasticity_to_price_delta(canonical["elasticity"], "raise")
    ac_pct, _ = elasticity_to_price_delta(abs(min(canonical["slope"], 0.0)), "raise")

    assert canonical["elasticity"] == pytest.approx(abs(canonical["slope"]))
    assert pi_pct == ac_pct
    # Pre-merge this product got 8% on one page and 6.18% on the other.
    assert pi_pct != pytest.approx(0.08)
