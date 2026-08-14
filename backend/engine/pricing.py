"""Price Intelligence recommendations — browse-all, percentile-based selection.

The elasticity estimate and the suggested percentage both come from
``pricing_core``; this module owns only *which* products get a recommendation
and how it is worded. See ``pricing_core`` for the sign convention.
"""
from __future__ import annotations

import pandas as pd

from .safety import (
    _has_dates, _QUANTILE_LOW, _QUANTILE_HIGH, _DEFAULT_ELASTICITY,
)
from .pricing_core import estimate_elasticity, elasticity_to_price_delta


def _usable_elasticity(df: pd.DataFrame, product: str) -> float | None:
    """Canonical elasticity magnitude, or None when it isn't trustworthy.

    Collapses pricing_core's valid/is_significant pair back to the single
    "None means we couldn't measure it" signal this module's messaging is
    built around.
    """
    res = estimate_elasticity(df, product)
    if res["valid"] and res["is_significant"]:
        return res["elasticity"]
    return None


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
            _e_used = _usable_elasticity(df, p)
            raise_pct, raise_pct_label = elasticity_to_price_delta(_e_used, "raise")
            sug = round(price * (1 + raise_pct), 2)

            # Gate confidence on whether elasticity could be estimated
            _raise_confidence = "directional" if _e_used is not None else "insufficient"

            if _e_used is not None:
                adj_qty = qty * (1 - _e_used * raise_pct)
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
                f"worth testing. Suggested starting point: {cur}{sug:.2f} (+{raise_pct*100:.0f}%). "
                f"Why this %: {raise_pct_label}. "
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
            _e_lower = _usable_elasticity(df, p)
            lower_pct, lower_pct_label = elasticity_to_price_delta(_e_lower, "lower")
            sug = round(price * (1 - lower_pct), 2)
            reason = (
                f"Priced in the top third of your products but selling in the bottom third "
                f"({int(qty)} units). A modest price reduction may be worth testing to see "
                f"if volume responds. Suggested: {cur}{sug:.2f} (−{lower_pct*100:.0f}%) for 2 weeks. "
                f"Why this %: {lower_pct_label}. "
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
                "current": price, "suggested": round(price, 2),
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
                "current": price, "suggested": round(price, 2),
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
