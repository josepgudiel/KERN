"""Canonical price-elasticity estimation and price-change sizing.

This is the single source of truth for "how price-sensitive is this product" and
"how big a price change should we test". Both product surfaces consume it:

  * Action Center      (``recommendations.py::_build_pricing_rec``, Path A) —
    high-bar, few results. Applies its own extra gates on top of this module.
  * Price Intelligence (``pricing.py::_get_price_recommendations``) —
    browse-all, up to 8 recommendations, percentile-based selection.

Selection and gating stay with the callers. Only the *math* lives here, so the
same product can never be shown two different elasticities or two different
suggested percentages depending on which page rendered it.

Sign convention
---------------
Demand curves slope down, so a "real" elasticity fit has a negative slope. The
two original implementations disagreed on how to report it, and both conventions
are still in use by callers, so ``estimate_elasticity`` returns *both*:

  ``slope``       signed regression coefficient, e.g. ``-0.509``. Negative means
                  normal downward-sloping demand; a positive value is a noisy or
                  confounded fit, not a product whose sales rise with price.
                  This is the convention ``recommendations.py`` gates on
                  (``price_tolerant`` is ``slope > -0.7``).

  ``elasticity``  magnitude, ``abs(slope)`` clipped to ``[0.05, ELASTICITY_CAP]``,
                  e.g. ``0.497``. Always non-negative. Larger = more
                  price-sensitive. This is the convention ``pricing.py`` and
                  ``action_center.py`` compare against thresholds like 1.2.

``elasticity_to_price_delta`` takes the **magnitude**. ``_elasticity_test_price``
takes the **signed** slope (it is the pre-existing dollar-space wrapper and its
signature is fixed by its callers and tests); it clamps positive slopes to zero
before converting, so a noisy upward fit is treated as fully inelastic rather
than extrapolated past the end of the scale.
"""
from __future__ import annotations

from typing import Literal

import numpy as np
import pandas as pd

from .safety import _has_dates

# Elasticity magnitudes above this are directional at best — the log-log fit on
# binned daily data is not trustworthy that far out, so we clip and say so.
ELASTICITY_CAP = 2.5
CI_CAP = 3.5

# Boundary of the Action Center's price_tolerant gate, and the knee in the raise
# curve: below it a price test is about finding headroom, above it it is about
# not losing volume.
_TOLERANT_BOUNDARY = 0.7

# Raise-side band: 12% for fully inelastic demand down to 1.5% at the cap.
_RAISE_MAX = 0.12
_RAISE_AT_BOUNDARY = 0.04
_RAISE_MIN = 0.015

# Lower-side band: 4% when a cut won't move volume, 10% once demand is clearly
# elastic. 1.2 is the elastic anchor the previous step-ladder used.
_LOWER_MIN = 0.04
_LOWER_MAX = 0.10
_LOWER_ELASTIC_ANCHOR = 1.2


def _empty_result(note: str) -> dict:
    """Return the full result shape for a product we could not estimate.

    Every key is always present so callers can index rather than ``.get()``.
    """
    return {
        "valid": False,
        "is_significant": False,
        "price_tolerant": False,
        "elasticity": None,
        "slope": None,
        "ci_low": None,
        "ci_high": None,
        "r_squared": None,
        "t_stat": None,
        "p_value": None,
        "fit_quality": None,
        "n_transactions": 0,
        "n_observations": 0,
        "n_price_points": 0,
        "note": note,
    }


def estimate_elasticity(df: pd.DataFrame, product: str) -> dict:
    """Estimate price elasticity for one product from daily-aggregated sales.

    Aggregates to daily average price / total quantity, bins by price quantile,
    and fits log(qty) ~ log(price) by OLS on the bin means. Daily aggregation and
    binning are what make this robust to transaction-level noise: a single
    log-log regression over raw transactions mostly fits within-day scatter.

    ``valid`` and ``is_significant`` are distinct:
      * ``valid=False``          — not enough data / no price variation / the
                                   regression could not be run. No estimate exists.
      * ``is_significant=False`` — the fit ran but the price/volume relationship
                                   is too weak to trust (t-stat or r-squared gate).
                                   Values are returned for inspection but callers
                                   should treat the product as unestimated.

    Callers that want the previous "None means unusable" behaviour should use::

        e = res["elasticity"] if res["valid"] and res["is_significant"] else None
    """
    prod_df = df[(df["product"] == product) & (df["quantity"] > 0)].copy()
    prod_df["unit_price"] = prod_df["revenue"] / prod_df["quantity"]

    n_raw = len(prod_df)
    if n_raw < 10:
        return _empty_result(f"insufficient data ({n_raw} transactions — need 10+)")

    if _has_dates(prod_df):
        prod_df["date_only"] = prod_df["date"].dt.date
        daily_agg = (
            prod_df.groupby("date_only")
            .agg(avg_price=("unit_price", "mean"), total_qty=("quantity", "sum"))
            .reset_index()
        )
        n_days = len(daily_agg)
        if n_days < 5:
            return _empty_result(f"insufficient daily observations ({n_days} days — need 5+)")
        price_series = daily_agg["avg_price"]
        qty_series   = daily_agg["total_qty"]
    else:
        price_series = prod_df["unit_price"]
        qty_series   = prod_df["quantity"]
        n_days = n_raw

    price_mean = float(price_series.mean())
    price_cv   = float(price_series.std()) / (price_mean + 1e-9)
    if price_cv < 0.03:
        return _empty_result(
            "not enough price variation in the data to estimate reliably — "
            "prices appear fixed. Run a controlled price experiment to get real demand data."
        )

    try:
        n_bins = min(10, n_days // 3)
        if n_bins < 3:
            return _empty_result(f"too few daily observations for binning ({n_days} days)")
        agg_df = pd.DataFrame({"price": price_series.values, "qty": qty_series.values})
        agg_df["price_bin"] = pd.qcut(agg_df["price"], q=n_bins, duplicates="drop")
        binned = (
            agg_df.groupby("price_bin", observed=True)
            .agg(avg_price=("price", "mean"), avg_qty=("qty", "mean"), n=("qty", "count"))
            .reset_index()
        )
        binned = binned[binned["n"] >= 2]
    except Exception as e:
        return _empty_result(f"price binning failed: {e}")

    if len(binned) < 5:
        return _empty_result(
            f"insufficient price bins after filtering ({len(binned)} retained — need 5+). "
            f"More price variation or a longer history is required."
        )

    log_p = np.log(binned["avg_price"].clip(lower=0.01).values)
    log_q = np.log(binned["avg_qty"].clip(lower=0.01).values)
    n_pts = len(log_p)

    X = np.column_stack([np.ones(n_pts), log_p])
    try:
        coeffs, _, _, _ = np.linalg.lstsq(X, log_q, rcond=None)
    except Exception as e:
        return _empty_result(f"regression failed: {e}")

    b = coeffs[1]
    fitted = X @ coeffs
    resid  = log_q - fitted
    dof    = n_pts - 2
    if dof < 3:
        return _empty_result(
            "not enough data points to estimate reliably — "
            "Collect more pricing variation before estimating elasticity."
        )

    s2 = (resid ** 2).sum() / dof
    try:
        Xp_inv = np.linalg.inv(X.T @ X)
    except np.linalg.LinAlgError as e:
        return _empty_result(f"singular matrix: {e}")
    se_b = float(np.sqrt(max(s2 * Xp_inv[1, 1], 1e-9)))

    ss_tot = ((log_q - log_q.mean()) ** 2).sum()
    r2_raw = 1 - (resid ** 2).sum() / (ss_tot + 1e-9)
    r2     = float(np.clip(r2_raw, 0, 1)) if np.isfinite(r2_raw) else 0.0
    t_stat = float(abs(b) / se_b) if se_b > 0 else 0.0

    # Two-tailed p-value from the t-stat, same normal approximation used by
    # recommendations.py::_linregress — kept so _statistical_detail's shape holds.
    p_value = float(min(2 * np.exp(-0.717 * t_stat - 0.416 * t_stat ** 2), 1.0)) if t_stat > 0 else 1.0

    raw_elasticity = float(abs(b))
    slope = float(b)
    elasticity = float(np.clip(raw_elasticity, 0.05, ELASTICITY_CAP))
    low_95  = float(np.clip(raw_elasticity - 2 * se_b, 0.05, CI_CAP))
    high_95 = float(np.clip(raw_elasticity + 2 * se_b, 0.05, CI_CAP))

    t_crit = max(1.8, 1.645 + 2.0 / dof)
    is_significant = bool(t_stat >= t_crit and r2 >= 0.20)

    if not is_significant:
        weak_note = (
            "the relationship between price and sales volume is too weak to estimate reliably — "
            "price variation may be confounded by promotions or seasonality. "
            "A controlled price experiment would provide cleaner identification."
        )
        return {
            "valid": True,
            "is_significant": False,
            "price_tolerant": bool(slope > -_TOLERANT_BOUNDARY),
            "elasticity": elasticity,
            "slope": slope,
            "ci_low": low_95,
            "ci_high": high_95,
            "r_squared": r2,
            "t_stat": t_stat,
            "p_value": p_value,
            "fit_quality": "weak",
            "n_transactions": n_raw,
            "n_observations": n_days,
            "n_price_points": n_pts,
            "note": weak_note,
        }

    fit_quality = "strong" if r2 > 0.5 and t_stat > 3 else ("moderate" if r2 > 0.25 else "weak")
    cap_note = ""
    if raw_elasticity > ELASTICITY_CAP:
        cap_note = f" Raw estimate ({raw_elasticity:.2f}) capped at {ELASTICITY_CAP} — treat as directional only."
        fit_quality = "moderate"
    note = (
        f"data-estimated from {n_raw} transactions / {n_days} daily observations, "
        f"Based on {n_pts} price points — {fit_quality} confidence{cap_note}"
    )

    return {
        "valid": True,
        "is_significant": True,
        "price_tolerant": bool(slope > -_TOLERANT_BOUNDARY),
        "elasticity": elasticity,
        "slope": slope,
        "ci_low": low_95,
        "ci_high": high_95,
        "r_squared": r2,
        "t_stat": t_stat,
        "p_value": p_value,
        "fit_quality": fit_quality,
        "n_transactions": n_raw,
        "n_observations": n_days,
        "n_price_points": n_pts,
        "note": note,
    }


def elasticity_to_price_delta(
    elasticity: float | None, direction: Literal["raise", "lower"]
) -> tuple[float, str]:
    """Size a price change from an elasticity magnitude.

    ``elasticity`` is the **magnitude** (non-negative — see the module docstring).
    ``None`` means no usable estimate and returns the conservative fallback.
    Returns ``(pct_as_decimal, human_readable_label)``.

    Raise: 12% when demand is flat, falling to 4% at the 0.7 tolerance boundary,
    then continuing down to 1.5% at the elasticity cap. Continuous throughout —
    two products with similar elasticity never get wildly different tests.

    Lower: the mirror image. 4% when demand is inelastic (a cut won't buy volume,
    so don't give away margin) rising to 10% once demand is clearly elastic.
    """
    if direction not in ("raise", "lower"):
        raise ValueError(f"direction must be 'raise' or 'lower', got {direction!r}")

    if elasticity is None:
        if direction == "raise":
            return 0.03, (
                "3% (conservative starting point — not enough price variation in your data "
                "to measure demand response; run a 2-week test before committing)"
            )
        return 0.05, (
            "5% (default — no elasticity data available; a price cut may not be the "
            "right lever if customers aren't price-sensitive)"
        )

    e = abs(float(elasticity))

    if direction == "raise":
        if e <= _TOLERANT_BOUNDARY:
            # 12% at e=0 down to 4% at e=0.7.
            pct = _RAISE_MAX - (_RAISE_MAX - _RAISE_AT_BOUNDARY) * (e / _TOLERANT_BOUNDARY)
        else:
            # 4% at e=0.7 down to 1.5% at the cap; flat beyond it.
            span = ELASTICITY_CAP - _TOLERANT_BOUNDARY
            progress = min((e - _TOLERANT_BOUNDARY) / span, 1.0)
            pct = _RAISE_AT_BOUNDARY - (_RAISE_AT_BOUNDARY - _RAISE_MIN) * progress

        if e < 0.5:
            desc = f"demand is very inelastic (elasticity {e:.2f}): customers barely react to price changes"
        elif e < _TOLERANT_BOUNDARY:
            desc = f"demand is moderately inelastic (elasticity {e:.2f})"
        elif e < 1.0:
            desc = f"demand has moderate price sensitivity (elasticity {e:.2f}): test cautiously"
        else:
            desc = (
                f"demand is price-sensitive (elasticity {e:.2f}): a small test only — "
                "volume loss can outrun the margin gain"
            )
        return pct, f"{pct * 100:.1f}% — {desc}"

    # direction == "lower"
    pct = _LOWER_MIN + (_LOWER_MAX - _LOWER_MIN) * min(e / _LOWER_ELASTIC_ANCHOR, 1.0)

    if e >= _LOWER_ELASTIC_ANCHOR:
        desc = f"demand is elastic (elasticity {e:.2f}): a meaningful cut is needed to move volume"
    elif e >= _TOLERANT_BOUNDARY:
        desc = f"moderate elasticity (elasticity {e:.2f}): worth a small test"
    else:
        desc = (
            f"demand is inelastic (elasticity {e:.2f}): "
            "a price cut likely won't drive volume — investigate visibility or "
            "product-market fit first"
        )
    return pct, f"{pct * 100:.1f}% — {desc}"


def _elasticity_test_price(current_avg_price: float, elasticity: float) -> tuple[float, float]:
    """Size a bounded price test in dollars. Returns (suggested_price, increase).

    Dollar-space wrapper over ``elasticity_to_price_delta(..., "raise")``: the
    percentage is canonical, the caps/floor/rounding below are the Action
    Center's presentation rules.

    This is deliberately NOT the monopoly optimal-markup formula p*(e/(e+1)):
    that has no finite positive solution for inelastic demand (|e| < 1), which is
    the only regime that reaches this code — the price_tolerant gate requires
    slope > -0.7. What we return is a defensible test size, not a claimed
    optimum: the more tolerant the elasticity, the larger the bump we test.

    Takes the **signed** slope (see the module docstring on sign convention).
    """
    e = min(elasticity, 0.0)  # guard against noisy positive-slope fits passing the unbounded price_tolerant gate
    test_pct, _ = elasticity_to_price_delta(abs(e), "raise")
    suggested_price = current_avg_price * (1 + test_pct)
    increase = min(suggested_price - current_avg_price, current_avg_price * 0.25, 2.00)
    increase = max(increase, 0.05)
    suggested_price = round((current_avg_price + increase) * 20) / 20  # nearest nickel
    return suggested_price, increase
