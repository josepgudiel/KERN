"""OLS price elasticity and price recommendations — extracted from app.py."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .safety import (
    _has_dates, _QUANTILE_LOW, _QUANTILE_HIGH, _DEFAULT_ELASTICITY,
)


def _estimate_product_elasticity(df: pd.DataFrame, product: str) -> tuple:
    """Estimate price elasticity using daily-aggregated price/volume data.

    Returns: (elasticity, low_95, high_95, note)
    Returns (None, None, None, reason) if data is insufficient.
    """
    prod_df = df[(df["product"] == product) & (df["quantity"] > 0)].copy()
    prod_df["unit_price"] = prod_df["revenue"] / prod_df["quantity"]

    n_raw = len(prod_df)
    if n_raw < 10:
        return None, None, None, f"insufficient data ({n_raw} transactions — need 10+)"

    if _has_dates(prod_df):
        prod_df["date_only"] = prod_df["date"].dt.date
        daily_agg = (
            prod_df.groupby("date_only")
            .agg(avg_price=("unit_price", "mean"), total_qty=("quantity", "sum"))
            .reset_index()
        )
        n_days = len(daily_agg)
        if n_days < 5:
            return None, None, None, f"insufficient daily observations ({n_days} days — need 5+)"
        price_series = daily_agg["avg_price"]
        qty_series   = daily_agg["total_qty"]
    else:
        price_series = prod_df["unit_price"]
        qty_series   = prod_df["quantity"]
        n_days = n_raw

    price_mean = float(price_series.mean())
    price_cv   = float(price_series.std()) / (price_mean + 1e-9)
    if price_cv < 0.03:
        return None, None, None, (
            "not enough price variation in the data to estimate reliably — "
            "prices appear fixed. Run a controlled price experiment to get real demand data."
        )

    try:
        n_bins = min(10, n_days // 3)
        if n_bins < 3:
            return None, None, None, f"too few daily observations for binning ({n_days} days)"
        agg_df = pd.DataFrame({"price": price_series.values, "qty": qty_series.values})
        agg_df["price_bin"] = pd.qcut(agg_df["price"], q=n_bins, duplicates="drop")
        binned = (
            agg_df.groupby("price_bin", observed=True)
            .agg(avg_price=("price", "mean"), avg_qty=("qty", "mean"), n=("qty", "count"))
            .reset_index()
        )
        binned = binned[binned["n"] >= 2]
    except Exception as e:
        return None, None, None, f"price binning failed: {e}"

    if len(binned) < 5:
        return None, None, None, (
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
        return None, None, None, f"regression failed: {e}"

    b = coeffs[1]
    fitted = X @ coeffs
    resid  = log_q - fitted
    dof    = n_pts - 2
    if dof < 3:
        return None, None, None, (
            "not enough data points to estimate reliably — "
            "Collect more pricing variation before estimating elasticity."
        )

    s2 = (resid ** 2).sum() / dof
    try:
        Xp_inv = np.linalg.inv(X.T @ X)
    except np.linalg.LinAlgError as e:
        return None, None, None, f"singular matrix: {e}"
    se_b = float(np.sqrt(max(s2 * Xp_inv[1, 1], 1e-9)))

    ss_tot = ((log_q - log_q.mean()) ** 2).sum()
    r2_raw = 1 - (resid ** 2).sum() / (ss_tot + 1e-9)
    r2     = float(np.clip(r2_raw, 0, 1)) if np.isfinite(r2_raw) else 0.0
    t_stat = abs(b) / se_b if se_b > 0 else 0

    t_crit = max(1.8, 1.645 + 2.0 / dof)
    if t_stat < t_crit or r2 < 0.20:
        return None, None, None, (
            "the relationship between price and sales volume is too weak to estimate reliably — "
            "price variation may be confounded by promotions or seasonality. "
            "A controlled price experiment would provide cleaner identification."
        )

    raw_elasticity = float(abs(b))
    _ELASTICITY_CAP = 2.5
    _CI_CAP = 3.5
    elasticity = float(np.clip(raw_elasticity, 0.05, _ELASTICITY_CAP))
    low_95  = float(np.clip(abs(b) - 2 * se_b, 0.05, _CI_CAP))
    high_95 = float(np.clip(abs(b) + 2 * se_b, 0.05, _CI_CAP))

    fit_quality = "strong" if r2 > 0.5 and t_stat > 3 else ("moderate" if r2 > 0.25 else "weak")
    cap_note = ""
    if raw_elasticity > _ELASTICITY_CAP:
        cap_note = f" Raw estimate ({raw_elasticity:.2f}) capped at {_ELASTICITY_CAP} — treat as directional only."
        fit_quality = "moderate"
    note = (
        f"data-estimated from {n_raw} transactions / {n_days} daily observations, "
        f"Based on {n_pts} price points — {fit_quality} confidence{cap_note}"
    )
    return elasticity, low_95, high_95, note


def _get_price_recommendations(df: pd.DataFrame, currency: str = "$") -> list:
    """Per-product pricing suggestions — percentile-based."""
    has_cost = "cost" in df.columns and df["cost"].notna().any()

    MIN_TXN_FOR_RAISE  = 25
    MIN_TXN_FOR_LOWER  = 20
    MIN_TXN_FOR_MAINTAIN = 20

    def _reliability(n: int) -> str:
        return "high" if n >= 50 else "low"

    agg_dict = {"quantity": ("quantity", "sum"), "revenue": ("revenue", "sum"),
                "transactions": ("revenue", "count")}
    if has_cost:
        agg_dict["cost"] = ("cost", "sum")
    agg = df.groupby("product").agg(**agg_dict).reset_index()
    agg["avg_price"] = agg["revenue"] / agg["quantity"].clip(lower=1)

    if has_cost:
        agg["margin"] = agg["revenue"] - agg["cost"]
        agg["margin_pct"] = agg["margin"] / agg["revenue"].clip(lower=0.01)

    agg = agg[agg["transactions"] >= MIN_TXN_FOR_LOWER].copy()

    if len(agg) < 3:
        return []

    qty_high_threshold   = agg["quantity"].quantile(_QUANTILE_HIGH)
    qty_low_threshold    = agg["quantity"].quantile(_QUANTILE_LOW)
    price_low_threshold  = agg["avg_price"].quantile(_QUANTILE_LOW)
    price_high_threshold = agg["avg_price"].quantile(_QUANTILE_HIGH)
    if has_cost:
        margin_high_threshold = agg["margin"].quantile(_QUANTILE_HIGH)

    cur = currency

    recs = []
    for _, row in agg.iterrows():
        p    = row["product"]
        price = row["avg_price"]
        qty   = row["quantity"]
        n_txn = int(row["transactions"])

        if qty >= qty_high_threshold and price <= price_low_threshold and n_txn >= MIN_TXN_FOR_RAISE:
            sug = round(price * 1.05, 2)
            _e, _, _, _note = _estimate_product_elasticity(df, p)
            _e_used = _e if _e is not None else None

            # Gate confidence on whether elasticity could be estimated
            _raise_confidence = "directional" if _e_used is not None else "insufficient"

            if _e_used is not None:
                adj_qty = qty * (1 - _e_used * 0.05)
                rev_signal = f"estimated revenue change: {cur}{adj_qty * sug - qty * price:+,.0f} (based on how customers have responded to past price changes — test before acting)"
                # Plain-language sensitivity label (never expose raw elasticity coefficient)
                if _e_used > 1.5:
                    sensitivity_label = "Customers are price-sensitive — a price increase will likely reduce revenue"
                elif _e_used >= 0.5:
                    sensitivity_label = "Moderate sensitivity — test a small increase before committing"
                else:
                    sensitivity_label = "Customers aren't very price-sensitive — a small increase is worth testing"
            else:
                rev_signal = (
                    "We don't have enough price variation in your data to estimate "
                    "how customers will respond. Run a 2-week test at the suggested "
                    "price before making it permanent."
                )
                sensitivity_label = None
            reason = (
                f"High demand relative to your other products ({int(qty)} units, in the top third) "
                f"with a below-average price (in the bottom third). A small price increase may be "
                f"worth testing. Suggested starting point: {cur}{sug:.2f} (+5%). "
                f"Run for 2 weeks and monitor unit volume. {rev_signal}."
            )
            _margin_pct_val = None
            if has_cost:
                _margin_pct_val = row["margin_pct"]
                reason += f" Current margin: {_margin_pct_val:.0%}."
                if "margin_pct" in agg.columns:
                    median_margin = agg["margin_pct"].median()
                    if _margin_pct_val < median_margin:
                        reason += (
                            f" Note: this product's margin ({_margin_pct_val:.0%}) is below your "
                            f"portfolio median ({median_margin:.0%}). Negotiating a lower cost from "
                            f"your supplier may be more impactful than raising the customer price."
                        )
            recs.append({
                "product": p, "action": "↑ Raise Price",
                "current": price, "suggested": sug,
                "n_txn": n_txn,
                "reason": reason,
                "margin_pct": _margin_pct_val,
                "elasticity_confidence": _raise_confidence,
                "reliability": _reliability(n_txn),
                "sensitivity_label": sensitivity_label,
                "priority": 0,
            })

        elif price >= price_high_threshold and qty <= qty_low_threshold and n_txn >= MIN_TXN_FOR_LOWER:
            sug = round(price * 0.95, 2)
            reason = (
                f"Priced in the top third of your products but selling in the bottom third "
                f"({int(qty)} units). A modest price reduction may be worth testing to see "
                f"if volume responds. Suggested: {cur}{sug:.2f} (−5%) for 2 weeks. "
                f"If volume doesn't improve meaningfully, the issue may be visibility or "
                f"product-market fit rather than price. Do not reduce permanently without a test."
            )
            recs.append({
                "product": p, "action": "↓ Consider Lowering",
                "current": price, "suggested": sug,
                "n_txn": n_txn,
                "reason": reason,
                "reliability": _reliability(n_txn),
                "sensitivity_label": None,
                "priority": 1,
            })

        elif has_cost and price >= price_high_threshold and row["margin"] >= margin_high_threshold and n_txn >= MIN_TXN_FOR_MAINTAIN:
            recs.append({
                "product": p, "action": "✓ Maintain",
                "current": price, "suggested": price,
                "n_txn": n_txn,
                "reason": (
                    f"Strong margin ({row['margin_pct']:.0%}) at a competitive price point. "
                    "Avoid discounting. Consider bundling with a lower-margin item to lift "
                    "average order value without eroding this product's unit economics."
                ),
                "reliability": _reliability(n_txn),
                "sensitivity_label": None,
                "priority": 2,
            })
        elif not has_cost and price >= price_high_threshold and qty >= qty_high_threshold and n_txn >= MIN_TXN_FOR_MAINTAIN:
            recs.append({
                "product": p, "action": "✓ Maintain",
                "current": price, "suggested": price,
                "n_txn": n_txn,
                "reason": (
                    f"High price and high volume ({int(qty)} units) — a strong revenue signal. "
                    "Protect this price point and consider a bundle to lift average order value."
                ),
                "reliability": _reliability(n_txn),
                "sensitivity_label": None,
                "priority": 2,
            })

    recs.sort(key=lambda x: x["priority"])
    return recs[:8]


def compute_price_simulation(df: pd.DataFrame, currency: str = "$") -> dict | None:
    """Compute quick price check for top product."""
    sim = df.groupby("product").agg(
        quantity=("quantity", "sum"),
        revenue=("revenue", "sum"),
    ).reset_index()
    sim["avg_price"]   = sim["revenue"] / sim["quantity"].clip(lower=1)
    has_d              = _has_dates(df)
    n_months           = max((df["date"].max() - df["date"].min()).days / 30, 1.0) if has_d else 1
    sim["monthly_qty"] = sim["quantity"] / n_months

    top         = sim.sort_values("revenue", ascending=False).iloc[0]
    cur_price   = float(top["avg_price"])
    monthly_qty = float(top["monthly_qty"])

    return {
        "product": top["product"],
        "current_price": cur_price,
        "monthly_qty": monthly_qty,
        "monthly_revenue": cur_price * monthly_qty,
    }
