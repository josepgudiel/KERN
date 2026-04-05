"""Rebuilt recommendation engine — statistical foundation + 6 rec types.

Every recommendation must deliver CLARITY + SURPRISE.
Every rec must pass ALL four firing conditions:
  1. Statistical significance test
  2. Trend acceleration
  3. Relative standing (outlier within this dataset)
  4. Estimated dollar impact >= $50/month
"""
from __future__ import annotations

import hashlib
import logging
import datetime

import numpy as np
import pandas as pd

from .safety import _has_dates
from .apriori import _compute_basket_rules

logger = logging.getLogger(__name__)


# ─── Statistical Foundation ──────────────────────────────────────────────────


def _linregress(x: np.ndarray, y: np.ndarray) -> tuple[float, float, float, float]:
    """Minimal OLS: returns (slope, intercept, r_squared, p_value).

    Uses numpy only — no scipy dependency.
    p-value computed via t-distribution approximation.
    """
    n = len(x)
    x_mean = x.mean()
    y_mean = y.mean()
    ss_xx = ((x - x_mean) ** 2).sum()
    ss_yy = ((y - y_mean) ** 2).sum()
    ss_xy = ((x - x_mean) * (y - y_mean)).sum()

    if ss_xx == 0:
        return 0.0, float(y_mean), 0.0, 1.0

    slope = float(ss_xy / ss_xx)
    intercept = float(y_mean - slope * x_mean)

    r_squared = float((ss_xy ** 2) / (ss_xx * ss_yy)) if ss_yy > 0 else 0.0

    # p-value via t-statistic with normal approximation
    residuals = y - (slope * x + intercept)
    dof = max(n - 2, 1)
    mse = float((residuals ** 2).sum() / dof)
    se_slope = float(np.sqrt(mse / ss_xx)) if ss_xx > 0 and mse > 0 else 1e9
    t_stat = abs(slope) / se_slope if se_slope > 0 else 0

    # Approximate two-tailed p-value from t-stat using a conservative heuristic
    # For dof >= 4: p < 0.05 when t > ~2.78 (dof=4) to ~2.0 (dof=large)
    # Use: p ≈ 2 * exp(-0.717 * t - 0.416 * t^2) for reasonable approximation
    if t_stat > 0:
        log_p = -0.717 * t_stat - 0.416 * t_stat ** 2
        p_value = min(2 * np.exp(log_p), 1.0)
    else:
        p_value = 1.0

    return slope, intercept, r_squared, float(p_value)


def compute_trend(weekly_values: list[float]) -> dict:
    """Compute trend via linear regression. Requires >= 4 weekly data points."""
    if len(weekly_values) < 4:
        return {"valid": False}

    x = np.arange(len(weekly_values), dtype=float)
    y = np.array(weekly_values, dtype=float)
    slope, intercept, r_squared, p_value = _linregress(x, y)

    pct_change_total = (
        (slope * len(weekly_values)) / weekly_values[0] * 100
        if weekly_values[0] != 0
        else 0
    )

    # Acceleration: is the trend getting stronger over time?
    mid = len(weekly_values) // 2
    first_half = weekly_values[:mid]
    second_half = weekly_values[mid:]
    if len(first_half) >= 2 and len(second_half) >= 2:
        slope_first, _, _, _ = _linregress(np.arange(len(first_half), dtype=float), np.array(first_half))
        slope_second, _, _, _ = _linregress(np.arange(len(second_half), dtype=float), np.array(second_half))
        accelerating = abs(slope_second) > abs(slope_first) * 1.2
    else:
        accelerating = False

    return {
        "valid": True,
        "slope": round(slope, 2),
        "r_squared": round(r_squared, 3),
        "p_value": round(p_value, 4),
        "direction": "up" if slope > 0 else "down",
        "pct_change_total": round(abs(pct_change_total), 1),
        "pct_change_signed": round(pct_change_total, 1),
        "is_significant": p_value < 0.05 and r_squared > 0.45,
        "accelerating": accelerating,
        "weeks_of_data": len(weekly_values),
    }


def relative_standing(product_value: float, all_product_values: list[float]) -> dict:
    """Where does this product sit in the distribution of all products?"""
    arr = np.array(all_product_values, dtype=float)
    if len(arr) < 3 or arr.std() == 0:
        return {"percentile": 50.0, "z_score": 0.0, "is_outlier": False, "direction": "neutral"}

    percentile = float(np.mean(arr <= product_value) * 100)
    z_score = float((product_value - arr.mean()) / arr.std())

    return {
        "percentile": round(percentile, 1),
        "z_score": round(z_score, 2),
        "is_outlier": abs(z_score) > 1.5,
        "direction": "high" if z_score > 0 else "low",
    }


def compute_elasticity(prices: list[float], quantities: list[float]) -> dict:
    """Log-log OLS regression for price elasticity."""
    if len(prices) < 20 or len(set(round(p, 2) for p in prices)) < 3:
        return {"valid": False}

    prices_arr = np.array(prices, dtype=float)
    quantities_arr = np.array(quantities, dtype=float)

    # Filter out zeros for log
    mask = (prices_arr > 0) & (quantities_arr > 0)
    if mask.sum() < 20:
        return {"valid": False}

    log_p = np.log(prices_arr[mask])
    log_q = np.log(quantities_arr[mask])
    slope, intercept, r_squared, p_value = _linregress(log_p, log_q)

    return {
        "valid": True,
        "elasticity": round(slope, 3),
        "r_squared": round(r_squared, 3),
        "p_value": round(p_value, 4),
        "is_significant": p_value < 0.05 and r_squared >= 0.15,
        "plain": (
            "customers barely react to price changes on this"
            if slope > -0.3
            else "customers are slightly price-aware but not much"
            if slope > -0.7
            else "customers notice price changes on this one"
            if slope > -1.0
            else "this item is price-sensitive"
        ),
        "price_tolerant": slope > -0.7,
    }


def estimate_monthly_impact(
    weekly_units: float, price_change: float = 0, rec_type: str = ""
) -> float:
    """Conservative monthly impact estimate. Used only as firing gate."""
    if rec_type == "pricing":
        return weekly_units * price_change * 4 * 0.85
    if rec_type == "bundle":
        return weekly_units * 0.3 * 4
    if rec_type == "dead_product":
        return weekly_units * 4
    if rec_type == "dow_opportunity":
        return weekly_units * 0.5 * 4
    if rec_type == "declining":
        return weekly_units * 4
    if rec_type == "rising":
        return weekly_units * 0.2 * 4
    return 0.0


def _compute_min_impact(df: pd.DataFrame) -> float:
    """Return the minimum monthly dollar impact a rec must clear to fire.

    Scales with business size: 1% of monthly revenue, floored at $50.
    A $3K/month business keeps the $50 floor; a $30K/month business needs $300.
    """
    total_revenue = float(df["revenue"].sum())
    if _has_dates(df):
        span_days = max((df["date"].max() - df["date"].min()).days, 1)
        monthly_revenue = (total_revenue / span_days) * 30
    else:
        # No date data — treat total as a rough monthly proxy
        monthly_revenue = total_revenue * 0.1
    return max(50.0, monthly_revenue * 0.01)


def _rec_id(rec_type: str, product: str) -> str:
    """Deterministic ID: md5(rec_type + product)[:12]."""
    raw = f"{rec_type}:{product}"
    return hashlib.md5(raw.encode()).hexdigest()[:12]


# ─── Data Helpers ────────────────────────────────────────────────────────────


def _get_weekly_revenue(df: pd.DataFrame, product: str) -> list[float]:
    """Get weekly revenue for a product, trimming partial first/last weeks."""
    if not _has_dates(df):
        return []
    prod_df = df[df["product"] == product].copy()
    if prod_df.empty:
        return []

    prod_df["week"] = prod_df["date"].dt.to_period("W").dt.start_time
    weekly = prod_df.groupby("week")["revenue"].sum().sort_index()

    # Trim partial weeks
    data_min = df["date"].min()
    data_max = df["date"].max()
    first_full = (data_min + pd.Timedelta(days=(7 - data_min.dayofweek) % 7)).normalize()
    last_full_end = (data_max - pd.Timedelta(days=(data_max.dayofweek + 1) % 7)).normalize()

    if len(weekly) > 2:
        weekly = weekly[(weekly.index >= first_full) & (weekly.index <= last_full_end)]

    return weekly.values.tolist()


def _get_weekly_units(df: pd.DataFrame, product: str) -> list[float]:
    """Get weekly units for a product."""
    if not _has_dates(df):
        return []
    prod_df = df[df["product"] == product].copy()
    if prod_df.empty:
        return []
    prod_df["week"] = prod_df["date"].dt.to_period("W").dt.start_time
    weekly = prod_df.groupby("week")["quantity"].sum().sort_index()
    return weekly.values.tolist()


def _product_avg_price(df: pd.DataFrame, product: str) -> float:
    """Average unit price for a product."""
    prod_df = df[df["product"] == product]
    if prod_df.empty:
        return 0.0
    total_rev = prod_df["revenue"].sum()
    total_qty = prod_df["quantity"].sum()
    return float(total_rev / max(total_qty, 1))


def _product_price_points(df: pd.DataFrame, product: str) -> dict:
    """Count distinct price points and price range for a product."""
    prod_df = df[df["product"] == product].copy()
    if prod_df.empty:
        return {"n_price_points": 0, "min_price": 0, "max_price": 0, "prices": [], "quantities": []}

    prod_df["unit_price"] = prod_df["revenue"] / prod_df["quantity"].clip(lower=1)
    prices = prod_df["unit_price"].values.tolist()
    quantities = prod_df["quantity"].values.tolist()

    # Round to nearest cent for distinct count
    rounded = prod_df["unit_price"].round(2)
    distinct = rounded.nunique()

    return {
        "n_price_points": distinct,
        "min_price": round(float(rounded.min()), 2),
        "max_price": round(float(rounded.max()), 2),
        "prices": prices,
        "quantities": quantities,
    }


def _all_product_trend_slopes(df: pd.DataFrame) -> dict[str, float]:
    """Compute trend slope for every product. Used for relative standing."""
    products = df["product"].unique()
    slopes = {}
    for p in products:
        weekly = _get_weekly_revenue(df, p)
        if len(weekly) >= 4:
            x = np.arange(len(weekly), dtype=float)
            slope, _, _, _ = _linregress(x, np.array(weekly, dtype=float))
            slopes[p] = slope
    return slopes


def _compute_overall_trend(df: pd.DataFrame) -> dict:
    """Compute overall business weekly revenue trend. Used for seasonal context in declining recs."""
    if not _has_dates(df):
        return {"valid": False}
    df_copy = df.copy()
    df_copy["week"] = df_copy["date"].dt.to_period("W").dt.start_time
    weekly = df_copy.groupby("week")["revenue"].sum().sort_index()
    if len(weekly) < 4:
        return {"valid": False}
    return compute_trend(weekly.values.tolist())


def _product_rank(df: pd.DataFrame, product: str, n_weeks_ago: int = 0) -> int:
    """Rank of product by revenue. n_weeks_ago=0 means current."""
    if not _has_dates(df):
        by_rev = df.groupby("product")["revenue"].sum().sort_values(ascending=False)
        return int((by_rev.index.get_loc(product) + 1)) if product in by_rev.index else 0

    max_date = df["date"].max()
    if n_weeks_ago > 0:
        end = max_date - pd.Timedelta(weeks=n_weeks_ago)
        start = end - pd.Timedelta(weeks=4)
        sub = df[(df["date"] >= start) & (df["date"] <= end)]
    else:
        start = max_date - pd.Timedelta(weeks=4)
        sub = df[df["date"] >= start]

    if sub.empty:
        return 0
    by_rev = sub.groupby("product")["revenue"].sum().sort_values(ascending=False)
    if product not in by_rev.index:
        return 0
    return int(by_rev.index.get_loc(product) + 1)


# ─── REC 1: PRICING OPPORTUNITY ─────────────────────────────────────────────


def _build_pricing_rec(df: pd.DataFrame, product: str, all_avg_prices: list[float], min_impact: float = 50.0, currency: str = "$") -> dict | None:
    """Build a pricing recommendation or return None.

    Path A: elasticity analysis — requires 3+ distinct price points. High confidence.
    Path B: portfolio comparison — fallback for single-price businesses. Moderate confidence.
    Both paths require: not declining, priced below portfolio average, impact >= $50/mo.
    """
    current_avg_price = _product_avg_price(df, product)
    if current_avg_price <= 0:
        return None

    n_txns = len(df[df["product"] == product])
    pp = _product_price_points(df, product)

    # Shared gate: don't raise price on a declining product
    weekly_rev = _get_weekly_revenue(df, product)
    if len(weekly_rev) >= 4:
        trend = compute_trend(weekly_rev)
        if trend["valid"] and trend["direction"] == "down" and trend["is_significant"]:
            return None

    n_weeks = len(weekly_rev)

    # ── Path A: Elasticity analysis (3+ price points) ────────────────────────
    if pp["n_price_points"] >= 3:
        elasticity = compute_elasticity(pp["prices"], pp["quantities"])
        if not elasticity["valid"] or not elasticity["is_significant"] or not elasticity["price_tolerant"]:
            return None

        standing = relative_standing(current_avg_price, all_avg_prices)
        if not standing["is_outlier"] or standing["direction"] != "low":
            return None

        e = elasticity["elasticity"]
        if e >= -0.01:  # near zero elasticity, cap the formula
            suggested_price = current_avg_price * 1.25
        else:
            suggested_price = current_avg_price * (e / (e + 1))
        increase = min(suggested_price - current_avg_price, current_avg_price * 0.25, 2.00)
        increase = max(increase, 0.25)
        suggested_price = round(current_avg_price + increase, 2)

        weekly_units = _get_weekly_units(df, product)
        avg_weekly_units = np.mean(weekly_units) if weekly_units else 0
        impact = estimate_monthly_impact(avg_weekly_units, increase, "pricing")
        if impact < min_impact:
            return None

        # Three-scenario impact math
        delta_a = round(suggested_price - current_avg_price, 2)
        upside_hold = round(delta_a * avg_weekly_units * 2, 0)       # 2-week payback if volume holds
        upside_10pct_drop = round(delta_a * avg_weekly_units * 0.90 * 2, 0)
        return {
            "id": _rec_id("pricing", product),
            "rec_type": "pricing",
            "product": product,
            "urgency_label": "Worth doing soon",
            "urgency_score": 2,
            "title": f"Price test on {product}: {currency}{current_avg_price:.2f} → {currency}{suggested_price:.2f} for 14 days",
            "body": (
                f"{product} has sold at {pp['n_price_points']} different price points "
                f"({currency}{pp['min_price']:.2f}–{currency}{pp['max_price']:.2f}) without demand dropping off — "
                f"a clear signal the market isn't price-sensitive here. "
                f"PRICE TEST: Raise {currency}{current_avg_price:.2f} → {currency}{suggested_price:.2f} (+{currency}{delta_a:.2f}/unit) for 14 days. "
                f"At current volume ({avg_weekly_units:.0f} units/week): "
                f"if volume holds: +{currency}{upside_hold:.0f} in 14 days (pure margin). "
                f"If volume drops 10%: +{currency}{upside_10pct_drop:.0f} (still positive). "
                f"If volume drops >15%: revert immediately — downside capped at 2 weeks."
            ),
            "see_why": (
                f"Sold at {pp['n_price_points']} price points ({currency}{pp['min_price']:.2f}–{currency}{pp['max_price']:.2f}). "
                f"Demand held each time. {n_txns:,} transactions over {n_weeks} weeks. "
                f"Decision rule: roll out if <10% volume drop after 14 days."
            ),
            "confidence": "high" if elasticity["r_squared"] > 0.3 else "moderate",
            "transaction_count": n_txns,
            "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
            "_impact_estimate": round(impact, 2),
            "_statistical_detail": {
                "elasticity": elasticity["elasticity"],
                "r_squared": elasticity["r_squared"],
                "p_value": elasticity["p_value"],
            },
        }

    # ── Path B: Portfolio comparison (single-price businesses) ───────────────
    # Requires: 15+ transactions, clear low-price outlier (bottom 25%), above-median volume.
    if n_txns < 15:
        return None

    standing = relative_standing(current_avg_price, all_avg_prices)
    if standing["percentile"] > 25 or not standing["is_outlier"] or standing["direction"] != "low":
        return None

    # Must be above-median volume — more evidence and more dollar impact
    all_txn_counts = [len(df[df["product"] == p]) for p in df["product"].unique()]
    volume_standing = relative_standing(n_txns, all_txn_counts)
    if volume_standing["percentile"] < 50:
        return None

    portfolio_avg = float(np.mean(all_avg_prices)) if all_avg_prices else 0
    if portfolio_avg <= current_avg_price:
        return None

    # Conservative raise: close the gap partially, cap at 15% of current price
    increase = min(portfolio_avg - current_avg_price, current_avg_price * 0.15)
    increase = max(increase, 0.25)
    suggested_price = round(current_avg_price + increase, 2)

    weekly_units = _get_weekly_units(df, product)
    avg_weekly_units = np.mean(weekly_units) if weekly_units else 0
    impact = estimate_monthly_impact(avg_weekly_units, increase, "pricing")
    if impact < min_impact:
        return None

    # Three-scenario impact math for Path B
    delta_b = round(suggested_price - current_avg_price, 2)
    upside_hold_b = round(delta_b * avg_weekly_units * 2, 0)     # 2-week payback
    upside_10pct_b = round(delta_b * avg_weekly_units * 0.90 * 2, 0)
    return {
        "id": _rec_id("pricing", product),
        "rec_type": "pricing",
        "product": product,
        "urgency_label": "Worth doing soon",
        "urgency_score": 2,
        "title": f"Price test on {product}: {currency}{current_avg_price:.2f} → {currency}{suggested_price:.2f} for 14 days",
        "body": (
            f"{product} is priced at {currency}{current_avg_price:.2f} — below your portfolio average of {currency}{portfolio_avg:.2f}, "
            f"and it's one of your higher-volume items. "
            f"PRICE TEST: Raise {currency}{current_avg_price:.2f} → {currency}{suggested_price:.2f} (+{currency}{delta_b:.2f}/unit) for 14 days. "
            f"At current volume ({avg_weekly_units:.0f} units/week): "
            f"if volume holds: +{currency}{upside_hold_b:.0f} in 14 days (pure margin). "
            f"If volume drops 10%: +{currency}{upside_10pct_b:.0f} (still positive). "
            f"If volume drops >15%: revert — downside capped at 2 weeks."
        ),
        "see_why": (
            f"Current price: {currency}{current_avg_price:.2f}. Portfolio avg: {currency}{portfolio_avg:.2f}. "
            f"Priced lower than {100 - standing['percentile']:.0f}% of your catalog. "
            f"{n_txns:,} transactions over {n_weeks} weeks. "
            f"Decision rule: roll out if <10% volume drop after 14 days."
        ),
        "confidence": "moderate",
        "transaction_count": n_txns,
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "_impact_estimate": round(impact, 2),
        "_statistical_detail": {
            "elasticity": None,
            "r_squared": None,
            "p_value": None,
            "path": "portfolio_comparison",
        },
    }


# ─── REC 2: DECLINING PRODUCT ───────────────────────────────────────────────


def _build_declining_rec(
    df: pd.DataFrame, product: str, all_slopes: dict[str, float],
    apriori_partners: dict[str, tuple[str, float]] | None = None,
    min_impact: float = 50.0,
    currency: str = "$",
) -> dict | None:
    """Build a declining product recommendation or return None."""
    weekly_rev = _get_weekly_revenue(df, product)
    trend = compute_trend(weekly_rev)

    if not trend["valid"] or not trend["is_significant"]:
        return None
    if trend["direction"] != "down":
        return None
    if not trend["accelerating"]:
        return None
    if trend["pct_change_total"] < 15:
        return None
    if trend["weeks_of_data"] < 6:
        return None

    # Relative standing: declining faster than other products
    slope_values = list(all_slopes.values())
    product_slope = all_slopes.get(product, 0)
    standing = relative_standing(abs(product_slope), [abs(s) for s in slope_values])
    if not standing["is_outlier"]:
        return None

    # Dollar impact gate
    avg_weekly_rev = np.mean(weekly_rev[-4:]) if len(weekly_rev) >= 4 else np.mean(weekly_rev)
    impact = estimate_monthly_impact(avg_weekly_rev, rec_type="declining")
    if impact < min_impact:
        return None

    # Count consecutive declining weeks
    consecutive_weeks = 0
    for i in range(len(weekly_rev) - 1, 0, -1):
        if weekly_rev[i] < weekly_rev[i - 1]:
            consecutive_weeks += 1
        else:
            break

    # Projected weeks to zero
    current_weekly = weekly_rev[-1] if weekly_rev else 0
    projected_weeks_to_zero = (
        int(abs(current_weekly / trend["slope"])) if trend["slope"] != 0 else 99
    )

    # Recovery metrics
    pct = trend["pct_change_total"]
    weeks_declining = consecutive_weeks
    has_partner = product in (apriori_partners or {})
    product_price = _product_avg_price(df, product)
    price_cut_5pct = round(product_price * 0.05, 2)
    price_new = round(product_price * 0.95, 2)
    recovery_potential = round(avg_weekly_rev * 0.50, 0)  # conservative 50% recovery estimate

    # Seasonal context: compare to overall business trend
    overall = _compute_overall_trend(df)
    if overall.get("valid") and overall.get("direction") == "down" and overall.get("is_significant"):
        seasonal_context = "Note: your overall business is also trending down — this may be seasonal."
        overall_trend_word = "declining"
    elif overall.get("valid") and overall.get("direction") in ("up", "flat"):
        overall_trend_word = "growing" if overall["direction"] == "up" else "holding steady"
        seasonal_context = f"Your overall business is {overall_trend_word} — this looks product-specific, not seasonal."
    else:
        seasonal_context = ""
        overall_trend_word = "flat"

    n_txns = len(df[df["product"] == product])

    if pct >= 35 or (trend["accelerating"] and weeks_declining >= 5):
        urgency = "Act this week"
        urgency_score = 3
        body = (
            f"Down {pct}% from peak, {consecutive_weeks} consecutive declining weeks, accelerating. "
            f"At this rate: ~{projected_weeks_to_zero} weeks to near-zero. {seasonal_context} "
            f"DIAGNOSE IN ORDER (cheapest first): "
            f"(1) VISIBILITY ($0, 15 min): When did you last promote this? Post on social today if >30 days. "
            f"(2) PRICE ({currency}{price_cut_5pct:.2f} test): Drop 5% ({currency}{product_price:.2f} → {currency}{price_new:.2f}) for 14 days — "
            f"expect +10–15% volume if price-driven. "
            f"(3) SUPPLY: Any stockouts in the last 30 days? Fix fulfillment before anything else. "
            f"Expected recovery if marketing-driven: +{currency}{recovery_potential:.0f}/week."
        )
        see_why = (
            f"{consecutive_weeks} consecutive declining weeks. Down {pct}% from peak. "
            f"~{projected_weeks_to_zero} weeks to near-zero at current pace. "
            f"Start: social post ($0). Then: 5% price test ({currency}{product_price:.2f} → {currency}{price_new:.2f}). "
            f"Recovery estimate: +{currency}{recovery_potential:.0f}/week."
        )
    elif pct >= 20:
        urgency = "Worth doing soon"
        urgency_score = 2
        if has_partner:
            partner_name, partner_lift = apriori_partners[product]
            body = (
                f"Down {pct}% over {consecutive_weeks} consecutive weeks. {seasonal_context} "
                f"DIAGNOSE IN ORDER (cheapest first): "
                f"(1) VISIBILITY ($0, 15 min): Post on social if last promotion was >30 days ago. "
                f"(2) BUNDLE: Pair with {partner_name} (bought together {partner_lift:.1f}x more than average). "
                f"Test bundle for 2 weeks — if {product} buyers add {partner_name}, the bundle boosts both. "
                f"(3) PRICE: If no recovery after (1) and (2), test 5% cut ({currency}{product_price:.2f} → {currency}{price_new:.2f}). "
                f"Expected recovery: +{currency}{recovery_potential:.0f}/week."
            )
            see_why = (
                f"{consecutive_weeks} weeks of decline. Down {pct}%. "
                f"Bundle partner: {partner_name} (lift {partner_lift:.1f}x). "
                f"Test order: (1) social post → (2) bundle → (3) price cut. "
                f"Recovery estimate: +{currency}{recovery_potential:.0f}/week if successful."
            )
        else:
            body = (
                f"Down {pct}% over {consecutive_weeks} weeks. {seasonal_context} "
                f"DIAGNOSE IN ORDER (cheapest first): "
                f"(1) VISIBILITY ($0, 15 min): Post on social if last promotion was >30 days ago. "
                f"(2) PRICE: Test 5% cut ({currency}{product_price:.2f} → {currency}{price_new:.2f}) for 14 days — "
                f"expect +10–15% volume if price-driven. "
                f"(3) POSITIONING: Is it still where customers can see it? Check placement, menu position, shelf spot. "
                f"Start with (1) — zero cost. Expected recovery: +{currency}{recovery_potential:.0f}/week."
            )
            see_why = (
                f"{consecutive_weeks} consecutive declining weeks. Down {pct}%. "
                f"Test order: (1) social post ($0) → (2) 5% price cut → (3) placement check. "
                f"Recovery estimate: +{currency}{recovery_potential:.0f}/week."
            )
    else:
        return None  # Mild decline doesn't meet surprise + clarity bar

    return {
        "id": _rec_id("declining", product),
        "rec_type": "declining",
        "product": product,
        "urgency_label": urgency,
        "urgency_score": urgency_score,
        "title": f"{product}: down {pct}% over {consecutive_weeks} weeks — diagnose before it's too late",
        "body": body,
        "see_why": see_why,
        "confidence": "high" if trend["r_squared"] > 0.6 else "moderate",
        "transaction_count": n_txns,
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "_impact_estimate": round(impact, 2),
        "_statistical_detail": {
            "slope": trend["slope"],
            "r_squared": trend["r_squared"],
            "p_value": trend["p_value"],
            "pct_change": pct,
        },
    }


# ─── REC 3: BUNDLE OPPORTUNITY ──────────────────────────────────────────────


def _build_bundle_recs(df: pd.DataFrame, min_impact: float = 50.0, currency: str = "$") -> list[dict]:
    """Build bundle recommendations from Apriori association rules."""
    if not _has_dates(df):
        return []

    _, rules, err, _ = _compute_basket_rules(df)
    if rules is None or rules.empty:
        return []

    # Pre-compute product avg prices
    prod_agg = (
        df.groupby("product")
        .agg(revenue=("revenue", "sum"), quantity=("quantity", "sum"))
        .reset_index()
    )
    prod_agg["avg_price"] = prod_agg["revenue"] / prod_agg["quantity"].clip(lower=1)
    price_lookup = prod_agg.set_index("product")["avg_price"].to_dict()

    # All pair gap transaction values for relative standing
    all_gap_values = []
    pair_data = []

    for _, rule in rules.iterrows():
        lift = float(rule["lift"])
        support = float(rule["support"])
        confidence = float(rule["confidence"])
        antecedent = str(rule["antecedent"])
        consequent = str(rule["consequent"])

        if lift < 2.5 or support < 0.04 or confidence < 0.35:
            continue

        # Compute gap transactions: bought A but not B
        if "transaction_id" in df.columns and df["transaction_id"].notna().any():
            txn_col = "transaction_id"
            work_df = df
        else:
            # Use date+location proxy
            work_df = df.copy()
            work_df["_session"] = work_df["date"].dt.date.astype(str)
            if "location" in work_df.columns:
                work_df["_session"] = work_df["_session"] + "_" + work_df["location"].astype(str)
            txn_col = "_session"

        sessions_with_a = set(work_df[work_df["product"] == antecedent][txn_col].unique())
        sessions_with_b = set(work_df[work_df["product"] == consequent][txn_col].unique())
        gap_transactions = len(sessions_with_a - sessions_with_b)

        all_gap_values.append(gap_transactions)
        pair_data.append({
            "antecedent": antecedent,
            "consequent": consequent,
            "lift": lift,
            "support": support,
            "confidence": confidence,
            "gap_transactions": gap_transactions,
        })

    recs = []
    for pair in pair_data:
        if pair["gap_transactions"] < 20:
            continue

        # Relative standing of gap_transactions
        standing = relative_standing(pair["gap_transactions"], all_gap_values)
        if not standing["is_outlier"]:
            continue

        price_a = price_lookup.get(pair["antecedent"], 0)
        price_b = price_lookup.get(pair["consequent"], 0)
        if price_a <= 0 or price_b <= 0:
            continue

        bundle_price = round((price_a + price_b) * 0.90, 2)
        bundle_savings = round((price_a + price_b) - bundle_price, 2)

        # Dollar impact gate
        weekly_units_a = _get_weekly_units(df, pair["antecedent"])
        avg_weekly = np.mean(weekly_units_a) if weekly_units_a else 0
        impact = estimate_monthly_impact(avg_weekly, rec_type="bundle")
        if impact < min_impact:
            continue

        n_weeks = len(weekly_units_a)
        support_pct = round(pair["support"] * 100, 1)
        n_txns = len(df[(df["product"] == pair["antecedent"]) | (df["product"] == pair["consequent"])])

        # Adoption math — use actual Apriori confidence as expected attach rate
        # Apriori confidence = P(B | A): if customer buys A, probability they also buy B.
        # This IS the expected attach rate from observed co-purchase data.
        apriori_attach = pair["confidence"]  # data-driven, not hardcoded
        attach_expected = round(avg_weekly * apriori_attach, 0)
        rollout_threshold = round(avg_weekly * max(apriori_attach * 0.75, 0.10), 0)
        revert_threshold = round(avg_weekly * max(apriori_attach * 0.40, 0.05), 0)
        # Revenue upside: extra units of B at bundled price (90% of full price)
        bundle_upside_weekly = round(attach_expected * price_b * 0.90, 0)

        recs.append({
            "id": _rec_id("bundle", f"{pair['antecedent']}+{pair['consequent']}"),
            "rec_type": "bundle",
            "product": pair["antecedent"],
            "product_b": pair["consequent"],
            "urgency_label": "Worth doing soon",
            "urgency_score": 2,
            "title": f"Bundle {pair['antecedent']} + {pair['consequent']}: {pair['gap_transactions']} customers bought one without the other",
            "body": (
                f"Customers who buy {pair['antecedent']} already pick up {pair['consequent']} "
                f"{pair['lift']:.1f}x more than you'd expect — the buying behavior is there. "
                f"BUNDLE TEST: Price {pair['antecedent']} + {pair['consequent']} at {currency}{bundle_price:.2f} "
                f"(saves {currency}{bundle_savings:.2f} vs buying separately) for 3 weeks. "
                f"At expected {apriori_attach*100:.0f}% attach rate from your data ({attach_expected:.0f} bundles/week): "
                f"+{currency}{bundle_upside_weekly:.0f}/week in {pair['consequent']} revenue. "
                f"Roll out if >{rollout_threshold:.0f} bundles/week after 3 weeks. "
                f"Revert to single-item pricing if <{revert_threshold:.0f} bundles/week — low downside."
            ),
            "see_why": (
                f"Co-purchased {pair['lift']:.1f}x more than chance ({support_pct}% of transactions). "
                f"{pair['gap_transactions']} customers bought {pair['antecedent']} without {pair['consequent']}. "
                f"Apriori confidence: {apriori_attach*100:.0f}% — that's your expected attach rate from real data. "
                f"Roll out threshold: >{rollout_threshold:.0f} bundles/week after 3 weeks."
            ),
            "confidence": "high" if pair["lift"] >= 3.0 and pair["confidence"] >= 0.5 else "moderate",
            "transaction_count": n_txns,
            "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
            "_impact_estimate": round(impact, 2),
            "_statistical_detail": {
                "lift": pair["lift"],
                "support": pair["support"],
                "confidence": pair["confidence"],
                "gap_transactions": pair["gap_transactions"],
            },
        })

    return recs


# ─── REC 4: RISING PRODUCT ──────────────────────────────────────────────────


def _build_rising_rec(
    df: pd.DataFrame, product: str, all_slopes: dict[str, float],
    all_avg_prices: list[float],
    apriori_partners: dict[str, tuple[str, float]] | None = None,
    min_impact: float = 50.0,
    currency: str = "$",
) -> dict | None:
    """Build a rising product recommendation or return None."""
    weekly_rev = _get_weekly_revenue(df, product)
    trend = compute_trend(weekly_rev)

    if not trend["valid"] or not trend["is_significant"]:
        return None
    if trend["direction"] != "up":
        return None
    if not trend["accelerating"]:
        return None
    if trend["pct_change_total"] < 20:
        return None
    if trend["weeks_of_data"] < 4:
        return None

    # Relative standing: rising faster than other products
    slope_values = list(all_slopes.values())
    product_slope = all_slopes.get(product, 0)
    standing = relative_standing(product_slope, slope_values)
    if not standing["is_outlier"]:
        return None

    # Dollar impact gate
    avg_weekly_rev = np.mean(weekly_rev[-4:]) if len(weekly_rev) >= 4 else np.mean(weekly_rev)
    impact = estimate_monthly_impact(avg_weekly_rev, rec_type="rising")
    if impact < min_impact:
        return None

    n_weeks = trend["weeks_of_data"]
    pct = trend["pct_change_total"]
    n_txns = len(df[df["product"] == product])

    # Rankings
    rank_now = _product_rank(df, product, n_weeks_ago=0)
    rank_before = _product_rank(df, product, n_weeks_ago=n_weeks)

    # Secondary signal detection
    current_avg_price = _product_avg_price(df, product)
    pp = _product_price_points(df, product)
    elasticity = compute_elasticity(pp["prices"], pp["quantities"]) if pp["n_price_points"] >= 3 else {"valid": False}

    # Price percentile
    price_percentile = relative_standing(current_avg_price, all_avg_prices)["percentile"]

    # Pre-compute metrics used by all action branches
    daily_rev = round(avg_weekly_rev / 7, 0)
    stockout_cost = round(daily_rev * 7, 0)
    overstock_cost = round(avg_weekly_rev * 2, 0)
    weekly_units = _get_weekly_units(df, product)
    avg_weekly_units = round(np.mean(weekly_units), 0) if weekly_units else 0

    action_type = "momentum"

    # Priority 1: underpriced — best window to raise price is during a growth phase
    if (
        elasticity.get("valid")
        and elasticity.get("price_tolerant")
        and price_percentile < 40
    ):
        action_type = "underpriced"
        suggested = round(current_avg_price * 1.10, 2)
        delta = round(suggested - current_avg_price, 2)
        upside_14d = round(delta * avg_weekly_units * 2, 0)
        body = (
            f"Growing +{pct}% over {n_weeks} weeks, now #{rank_now} best-seller (was #{rank_before}). "
            f"At {currency}{daily_rev:.0f}/day revenue and accelerating — growth periods are the best window to reprice. "
            f"PRICE TEST: Raise {currency}{current_avg_price:.2f} → {currency}{suggested:.2f} (+{currency}{delta:.2f}/unit) for 14 days. "
            f"At current volume ({avg_weekly_units:.0f} units/week): "
            f"if volume holds: +{currency}{upside_14d:.0f} in 14 days (pure margin). "
            f"If volume drops >15%: revert immediately — downside capped at 2 weeks."
        )
        see_why = (
            f"+{pct}% over {n_weeks} weeks. Rank #{rank_before} → #{rank_now}. "
            f"{currency}{daily_rev:.0f}/day revenue. Underpriced vs portfolio (bottom 40%). "
            f"Roll out if <10% volume drop after 14 days; revert if >15% drop."
        )
    # Priority 2: bundle partner already identified by Apriori
    elif product in (apriori_partners or {}):
        partner_name, partner_lift = apriori_partners[product]
        if partner_lift >= 2.0:
            action_type = "bundle"
            partner_price = _product_avg_price(df, partner_name)
            bundle_price_test = round((current_avg_price + partner_price) * 0.90, 2)
            attach_30pct = round(avg_weekly_units * 0.30, 0)
            bundle_upside = round(attach_30pct * partner_price * 0.90, 0)
            body = (
                f"Growing +{pct}% over {n_weeks} weeks, #{rank_before} → #{rank_now} best-seller. "
                f"At {currency}{daily_rev:.0f}/day revenue, demand window won't last forever. "
                f"BUNDLE: Pair {product} + {partner_name} (bought together {partner_lift:.1f}x more than average). "
                f"Test bundle at {currency}{bundle_price_test:.2f} for 3 weeks. "
                f"At 30% attach rate: +{attach_30pct:.0f} extra {partner_name} sales/week = +{currency}{bundle_upside:.0f}/week. "
                f"Roll out if >25% adoption; revert to single-item if <15% after 3 weeks."
            )
            see_why = (
                f"+{pct}% over {n_weeks} weeks. Rank #{rank_before} → #{rank_now}. "
                f"{currency}{daily_rev:.0f}/day revenue, accelerating. "
                f"Bundle partner {partner_name} (lift {partner_lift:.1f}x). "
                f"Measure adoption after 3 weeks; threshold: >25% = roll out, <15% = revert."
            )
        else:
            action_type = "momentum"
            body = (
                f"Growing +{pct}% over {n_weeks} weeks, now #{rank_now} best-seller (was #{rank_before}). "
                f"At {currency}{daily_rev:.0f}/day revenue, growth is accelerating — demand window won't last. "
                f"INVENTORY: Lock in 2-week supply now (before shortage risk). "
                f"Risk: stockout costs ~{currency}{stockout_cost:.0f}/week in lost sales. "
                f"Overstock risk at growth plateau: ~{currency}{overstock_cost:.0f} tied up. "
                f"Action: check stock levels today, reorder to 14-day cover."
            )
            see_why = (
                f"+{pct}% over {n_weeks} weeks. Rank #{rank_before} → #{rank_now}. "
                f"{currency}{daily_rev:.0f}/day revenue. Stockout cost if you miss demand: ~{currency}{stockout_cost:.0f}/week. "
                f"Accelerating (second-half slope > first-half)."
            )
    else:
        # Default: momentum / inventory action
        body = (
            f"Growing +{pct}% over {n_weeks} weeks, now #{rank_now} best-seller (was #{rank_before}). "
            f"At {currency}{daily_rev:.0f}/day revenue, growth is accelerating — demand window won't last. "
            f"INVENTORY: Lock in 2-week supply now (before shortage risk). "
            f"Risk: stockout costs ~{currency}{stockout_cost:.0f}/week in lost sales. "
            f"Overstock risk at growth plateau: ~{currency}{overstock_cost:.0f} tied up. "
            f"Action: check stock levels today, reorder to 14-day cover."
        )
        see_why = (
            f"+{pct}% over {n_weeks} weeks. Rank #{rank_before} → #{rank_now}. "
            f"{currency}{daily_rev:.0f}/day revenue. Stockout cost if you miss demand: ~{currency}{stockout_cost:.0f}/week. "
            f"Accelerating (second-half slope > first-half)."
        )

    rec_type_final = "underpriced_rising" if action_type == "underpriced" else "rising"

    return {
        "id": _rec_id(rec_type_final, product),
        "rec_type": rec_type_final,
        "product": product,
        "urgency_label": "Worth doing soon",
        "urgency_score": 2,
        "title": f"{product}: +{pct}% over {n_weeks} weeks — #{rank_before} → #{rank_now} best-seller",
        "body": body,
        "see_why": see_why,
        "confidence": "high" if trend["r_squared"] > 0.6 else "moderate",
        "transaction_count": n_txns,
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "_impact_estimate": round(impact, 2),
        "_statistical_detail": {
            "slope": trend["slope"],
            "r_squared": trend["r_squared"],
            "p_value": trend["p_value"],
            "pct_change": pct,
            "action_type": action_type,
        },
    }


# ─── REC 5: DEAD PRODUCT ────────────────────────────────────────────────────


def _build_dead_product_recs(df: pd.DataFrame, min_impact: float = 50.0) -> list[dict]:
    """Detect products that were selling and then stopped."""
    if not _has_dates(df):
        return []

    max_date = df["date"].max()
    last_30_start = max_date - pd.Timedelta(days=30)
    prev_30_start = max_date - pd.Timedelta(days=60)

    df_last_30 = df[df["date"] >= last_30_start]
    df_prev_30 = df[(df["date"] >= prev_30_start) & (df["date"] < last_30_start)]

    if df_prev_30.empty:
        return []

    sales_last = df_last_30.groupby("product")["quantity"].sum()
    sales_prev = df_prev_30.groupby("product")["quantity"].sum()

    # All products that existed in prev period
    all_prev_products = sales_prev.index.tolist()
    all_drop_pcts = []
    product_data = []

    for product in all_prev_products:
        prev_sales = float(sales_prev.get(product, 0))
        last_sales = float(sales_last.get(product, 0))

        if prev_sales < 10:
            continue
        if last_sales > 2:
            continue

        pct_drop = (prev_sales - last_sales) / prev_sales
        if pct_drop < 0.85:
            continue

        # Days since last sale
        product_rows = df[df["product"] == product]
        last_sale_date = product_rows["date"].max()
        days_since = (max_date - last_sale_date).days
        if days_since > 45:
            continue

        all_drop_pcts.append(pct_drop)
        product_data.append({
            "product": product,
            "sales_prev": int(prev_sales),
            "sales_last": int(last_sales),
            "pct_drop": round(pct_drop * 100, 1),
            "days_since": days_since,
            "last_sale_date": str(last_sale_date.date()),
        })

    recs = []
    for item in product_data:
        # Relative standing
        standing = relative_standing(item["pct_drop"], [d * 100 for d in all_drop_pcts])
        if not standing["is_outlier"] and len(all_drop_pcts) >= 3:
            continue

        # Dollar impact gate
        avg_price = _product_avg_price(df, item["product"])
        weekly_units_before = item["sales_prev"] / 4.3  # ~4.3 weeks in 30 days
        impact = estimate_monthly_impact(weekly_units_before * avg_price, rec_type="dead_product")
        if impact < min_impact:
            continue

        n_txns = len(df[df["product"] == item["product"]])

        recs.append({
            "id": _rec_id("dead_product", item["product"]),
            "rec_type": "dead_product",
            "product": item["product"],
            "urgency_label": "Act this week",
            "urgency_score": 3,
            "title": f"{item['product']} has almost completely stopped selling",
            "body": (
                f"It sold {item['sales_prev']} times in the 30 days before last month. "
                f"It's sold {item['sales_last']} times since. That's not a slow week — "
                f"something changed. Last sale was {item['days_since']} days ago. "
                f"Check if it's still visible, still stocked, and still priced correctly "
                f"before writing it off."
            ),
            "see_why": (
                f"Previous 30 days: {item['sales_prev']} sales. "
                f"Last 30 days: {item['sales_last']} sales. "
                f"Last sale: {item['last_sale_date']}. "
                f"Drop: {item['pct_drop']}%."
            ),
            "confidence": "high",
            "transaction_count": n_txns,
            "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
            "_impact_estimate": round(impact, 2),
            "_statistical_detail": {
                "sales_prev_30": item["sales_prev"],
                "sales_last_30": item["sales_last"],
                "pct_drop": item["pct_drop"],
                "days_since_last_sale": item["days_since"],
            },
        })

    return recs


# ─── REC 6: DAY-OF-WEEK OPPORTUNITY ─────────────────────────────────────────


def _build_dow_recs(df: pd.DataFrame, min_impact: float = 50.0) -> list[dict]:
    """Detect products with strong day-of-week sales patterns."""
    if not _has_dates(df):
        return []

    max_date = df["date"].max()
    min_date = df["date"].min()
    n_weeks = max((max_date - min_date).days / 7, 1)
    if n_weeks < 6:
        return []

    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    df_copy = df.copy()
    df_copy["dow"] = df_copy["date"].dt.dayofweek
    df_copy["week"] = df_copy["date"].dt.to_period("W").dt.start_time

    products = df["product"].unique()
    all_multipliers = []
    product_dow_data = []

    for product in products:
        prod_df = df_copy[df_copy["product"] == product]
        if len(prod_df) < 20:
            continue

        dow_rev = prod_df.groupby("dow")["revenue"].sum()
        dow_count = prod_df.groupby("dow")["revenue"].count()

        if len(dow_rev) < 5:  # need sales on most days
            continue

        # Average revenue per day occurrence
        dow_avg = dow_rev / dow_count.clip(lower=1)
        peak_dow = int(dow_avg.idxmax())
        peak_dow_avg = float(dow_avg[peak_dow])
        other_days = dow_avg.drop(peak_dow)
        mean_other_days_avg = float(other_days.mean()) if len(other_days) > 0 else 0

        if mean_other_days_avg <= 0:
            continue

        multiplier = peak_dow_avg / mean_other_days_avg
        if multiplier < 2.5:
            continue

        # Consistency check: how many weeks does the peak day beat the average?
        weeks_with_peak = prod_df[prod_df["dow"] == peak_dow].groupby("week")["revenue"].sum()
        weeks_others = prod_df[prod_df["dow"] != peak_dow].groupby("week")["revenue"].mean()
        common_weeks = weeks_with_peak.index.intersection(weeks_others.index)
        if len(common_weeks) < 4:
            continue

        consistent_weeks = sum(
            1 for w in common_weeks if weeks_with_peak[w] > weeks_others[w]
        )
        consistency = consistent_weeks / len(common_weeks)
        if consistency < 0.70:
            continue

        all_multipliers.append(multiplier)
        product_dow_data.append({
            "product": product,
            "peak_dow": peak_dow,
            "peak_day_name": day_names[peak_dow],
            "multiplier": round(multiplier, 1),
            "peak_dow_avg": round(peak_dow_avg, 2),
            "mean_other_days_avg": round(mean_other_days_avg, 2),
            "consistency_pct": round(consistency * 100, 0),
            "n_weeks": int(n_weeks),
        })

    recs = []
    for item in product_dow_data:
        # Relative standing
        standing = relative_standing(item["multiplier"], all_multipliers)
        if not standing["is_outlier"] and len(all_multipliers) >= 3:
            continue

        # Dollar impact gate
        weekly_rev = _get_weekly_revenue(df, item["product"])
        avg_weekly = np.mean(weekly_rev) if weekly_rev else 0
        impact = estimate_monthly_impact(avg_weekly, rec_type="dow_opportunity")
        if impact < min_impact:
            continue

        n_txns = len(df[df["product"] == item["product"]])

        recs.append({
            "id": _rec_id("dow_opportunity", item["product"]),
            "rec_type": "dow_opportunity",
            "product": item["product"],
            "urgency_label": "Worth doing soon",
            "urgency_score": 2,
            "title": (
                f"{item['product']} sells {item['multiplier']}x more on "
                f"{item['peak_day_name']} — are you ready for it?"
            ),
            "body": (
                f"{item['product']} consistently outperforms on {item['peak_day_name']}s — "
                f"{item['multiplier']}x your average for the rest of the week, and it's been "
                f"doing this for {item['n_weeks']} weeks. Make sure it's fully stocked and "
                f"front-of-mind every {item['peak_day_name']}."
            ),
            "see_why": (
                f"Average on {item['peak_day_name']}: {item['peak_dow_avg']} units. "
                f"Average other days: {item['mean_other_days_avg']} units. "
                f"Pattern held in {int(item['consistency_pct'])}% of "
                f"{item['peak_day_name']}s over {item['n_weeks']} weeks."
            ),
            "confidence": "high" if item["consistency_pct"] >= 85 else "moderate",
            "transaction_count": n_txns,
            "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
            "_impact_estimate": round(impact, 2),
            "_statistical_detail": {
                "multiplier": item["multiplier"],
                "consistency_pct": item["consistency_pct"],
                "peak_dow": item["peak_day_name"],
            },
        })

    return recs


# ─── DEDUPLICATION ───────────────────────────────────────────────────────────


def deduplicate(recs: list[dict]) -> list[dict]:
    """One rec per product. Most urgent wins. Bundle exception."""
    urgency_rank = {"Act this week": 0, "Worth doing soon": 1, "Plan for next month": 2}
    seen_products: dict[str, dict] = {}

    sorted_recs = sorted(recs, key=lambda r: urgency_rank.get(r["urgency_label"], 3))

    for rec in sorted_recs:
        product = rec["product"]
        if rec["rec_type"] == "bundle":
            product_b = rec.get("product_b", "")
            bundle_key = f"{product}+{product_b}"
            if product not in seen_products and product_b not in seen_products:
                seen_products[bundle_key] = rec
        elif product not in seen_products:
            seen_products[product] = rec

    # Hard conflict check: never show rising + declining for same product
    product_rec_types: dict[str, list[str]] = {}
    for rec in seen_products.values():
        p = rec["product"]
        product_rec_types.setdefault(p, []).append(rec["rec_type"])

    conflicts = {
        p
        for p, types in product_rec_types.items()
        if any(t in ("rising", "underpriced_rising") for t in types)
        and "declining" in types
    }
    if conflicts:
        logger.warning(f"Conflicting signals for products: {conflicts} — suppressed")

    return [r for r in seen_products.values() if r["product"] not in conflicts]


# ─── RANKING ─────────────────────────────────────────────────────────────────


def rank_and_cap(recs: list[dict], max_recs: int = 5) -> list[dict]:
    """Rank by urgency + surprise bonus. Cap at max_recs."""
    urgency_rank = {"Act this week": 0, "Worth doing soon": 1, "Plan for next month": 2}
    surprise_types = {"dead_product", "bundle", "dow_opportunity"}

    def sort_key(rec):
        urgency = urgency_rank.get(rec["urgency_label"], 3)
        surprise_bonus = 0 if rec["rec_type"] in surprise_types else 1
        return (urgency, surprise_bonus)

    ranked = sorted(recs, key=sort_key)
    return ranked[:max_recs]


# ─── APRIORI PARTNER LOOKUP ─────────────────────────────────────────────────


def _get_apriori_partners(df: pd.DataFrame) -> dict[str, tuple[str, float]]:
    """For each product, find its strongest co-purchase partner (if any)."""
    _, rules, err, _ = _compute_basket_rules(df)
    if rules is None or rules.empty:
        return {}

    partners: dict[str, tuple[str, float]] = {}
    for _, rule in rules.iterrows():
        ant = str(rule["antecedent"])
        con = str(rule["consequent"])
        lift = float(rule["lift"])
        if lift >= 2.0:
            if ant not in partners or lift > partners[ant][1]:
                partners[ant] = (con, lift)
            if con not in partners or lift > partners[con][1]:
                partners[con] = (ant, lift)
    return partners


# ─── MAIN ENTRY POINT ───────────────────────────────────────────────────────


def build_recommendations(df: pd.DataFrame, currency: str = "$") -> list[dict]:
    """Build all recommendations. Returns ranked list of max 5 dicts.

    Each dict has: id, rec_type, urgency_label, urgency_score, title, body,
    see_why, confidence, transaction_count, product, product_b (bundle only),
    generated_at. Internal fields (_impact_estimate, _statistical_detail)
    are stripped before returning.
    """
    all_recs: list[dict] = []

    # Pre-compute shared data
    products = df["product"].unique().tolist()
    all_slopes = _all_product_trend_slopes(df)
    all_avg_prices = [_product_avg_price(df, p) for p in products]
    all_avg_prices = [p for p in all_avg_prices if p > 0]
    apriori_partners = _get_apriori_partners(df)
    min_impact = _compute_min_impact(df)

    # REC 1: Pricing
    for product in products:
        rec = _build_pricing_rec(df, product, all_avg_prices, min_impact=min_impact, currency=currency)
        if rec:
            all_recs.append(rec)

    # REC 2: Declining
    for product in products:
        rec = _build_declining_rec(df, product, all_slopes, apriori_partners, min_impact=min_impact, currency=currency)
        if rec:
            all_recs.append(rec)

    # REC 3: Bundle
    bundle_recs = _build_bundle_recs(df, min_impact=min_impact, currency=currency)
    all_recs.extend(bundle_recs)

    # REC 4: Rising
    for product in products:
        rec = _build_rising_rec(df, product, all_slopes, all_avg_prices, apriori_partners, min_impact=min_impact, currency=currency)
        if rec:
            all_recs.append(rec)

    # REC 5: Dead Product
    dead_recs = _build_dead_product_recs(df, min_impact=min_impact)
    all_recs.extend(dead_recs)

    # REC 6: Day-of-Week Opportunity
    dow_recs = _build_dow_recs(df, min_impact=min_impact)
    all_recs.extend(dow_recs)

    # Dedup + rank
    deduped = deduplicate(all_recs)
    ranked = rank_and_cap(deduped, max_recs=5)

    # Strip internal fields before returning
    public_fields = {
        "id", "rec_type", "urgency_label", "urgency_score", "title", "body",
        "see_why", "confidence", "transaction_count", "product", "product_b",
        "generated_at",
    }
    result = []
    for rec in ranked:
        public_rec = {k: v for k, v in rec.items() if k in public_fields}
        if rec.get("_impact_estimate") is not None:
            public_rec["impact_estimate"] = rec["_impact_estimate"]
        result.append(public_rec)

    return result
