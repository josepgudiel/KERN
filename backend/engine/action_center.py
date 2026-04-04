"""Action center logic — recommendation ranking engine extracted from app.py."""
from __future__ import annotations

import pandas as pd

from .safety import _has_dates
from .insights import _detect_overview_insights, _find_rising_stars, _find_declining_products
from .pricing import _get_price_recommendations


def _strip_md(s: str) -> str:
    """Remove Markdown bold/italic syntax that renders as literal asterisks in plain-text UI."""
    if not isinstance(s, str):
        return s
    return s.replace("**", "").replace("__", "").replace("*", "").replace("_italic_", "")


def _tier_impact_label(amount: float | None, currency: str = "$") -> str | None:
    """Return a tiered impact label based on dollar amount."""
    if amount is None or amount <= 0:
        return None
    if amount >= 500:
        return f"Could recover ~{currency}{amount:,.0f}/month"
    if amount >= 100:
        return f"Worth ~{currency}{amount:,.0f}/month"
    return f"Small win — ~{currency}{amount:,.0f}/month"


def _prescribe_low_activity(
    df: pd.DataFrame,
    product_clusters,
    currency: str = "$",
) -> dict | None:
    """Return a computed prescription action card for Low Activity products, or None."""
    if product_clusters is None:
        return None

    dead = product_clusters[product_clusters["category"] == "Low Activity"].nlargest(3, "revenue")
    if dead.empty:
        return None

    cur = currency
    has_dates = _has_dates(df)
    months = max((df["date"].max() - df["date"].min()).days / 30, 0.034) if has_dates else 1

    prod_agg = (
        df.groupby("product")
        .agg(quantity=("quantity", "sum"), revenue=("revenue", "sum"))
        .reset_index()
    )
    prod_lookup = prod_agg.set_index("product")

    price_lines = []
    total_recovery = 0.0
    valid_products = 0

    for _, row in dead.iterrows():
        pname = row["product"]
        if pname not in prod_lookup.index:
            continue

        p_qty = prod_lookup.loc[pname, "quantity"]
        p_rev = prod_lookup.loc[pname, "revenue"]

        if "unit_price" in df.columns and df["unit_price"].notna().any():
            avg_price = df[df["product"] == pname]["unit_price"].mean()
        else:
            avg_price = p_rev / max(p_qty, 1)

        if avg_price <= 0:
            continue

        valid_products += 1
        monthly_qty = p_qty / months
        monthly_rev = p_rev / months
        discount_price = avg_price * 0.80

        new_qty = monthly_qty * (1 + 1.2 * 0.20)
        recovery_rev = discount_price * new_qty
        incremental = max(recovery_rev - monthly_rev, 0.0)
        total_recovery += incremental

        price_lines.append(
            f"{pname}: try {cur}{discount_price:.2f} (was {cur}{avg_price:.2f})"
        )

    if valid_products == 0:
        return None

    total_recovery = round(total_recovery)
    names = ", ".join(str(x) for x in dead["product"].tolist()[:3])

    return {
        "title": (
            f"Consider discounting these {len(dead)} slow items — "
            f"projected recovery: {cur}{total_recovery:,.0f}/month"
        ),
        "detail": (
            "These products are generating almost no revenue at their current price. "
            "A 20% discount could unlock dormant demand:\n"
            + "\n".join(price_lines)
            + "\nRun for 2 weeks. If volume doesn't lift, consider removing them entirely."
        ),
        "impact_dollars": float(total_recovery),
        "impact_low": round(total_recovery * 0.5, 2),
        "impact_high": round(total_recovery * 1.5, 2),
        "impact_range": (
            f"~{cur}{total_recovery:,.0f}/month if demand responds "
            f"(range: {cur}{round(total_recovery*0.5):,.0f}–"
            f"{cur}{round(total_recovery*1.5):,.0f})"
        ),
        "confidence": "directional",
        "priority": 3,
    }


def _growth_actions(
    trend: str,
    df: pd.DataFrame | None = None,
    growth_pct: float = 0,
    avg_daily: float = 0,
    projected_total: float = 0,
    forecast_weeks: int = 4,
    wow: float | None = None,
    currency: str = "$",
) -> list:
    """Actionable recommendations tied to the forecast trend direction."""
    cur = currency

    top_product    = ""
    second_product = ""
    bottom_product = ""
    top_rev        = 0.0
    bottom_rev     = 0.0
    total_rev      = 0.0
    top_avg_txn    = 0.0

    if df is not None and not df.empty:
        by_rev    = df.groupby("product")["revenue"].sum().sort_values(ascending=False)
        total_rev = float(by_rev.sum())
        if len(by_rev) >= 1:
            top_product = str(by_rev.index[0])
            top_rev     = float(by_rev.iloc[0])
        if len(by_rev) >= 2:
            second_product = str(by_rev.index[1])
        if len(by_rev) >= 1:
            bottom_product = str(by_rev.index[-1])
            bottom_rev     = float(by_rev.iloc[-1])
        top_rows    = df[df["product"] == top_product] if top_product else df
        top_avg_txn = top_rev / max(len(top_rows), 1)

    top_share_pct    = (top_rev / total_rev * 100) if total_rev > 0 else 0
    bottom_share_pct = (bottom_rev / total_rev * 100) if total_rev > 0 else 0
    weekly_avg       = avg_daily * 7

    top_ref    = f"**{top_product}**" if top_product else "your best seller"
    second_ref = f"**{second_product}**" if second_product else "your second-best item"
    bottom_ref = f"**{bottom_product}**" if bottom_product else "your lowest-volume items"

    growth_abs = abs(growth_pct)

    if trend == "upward":
        wow_note      = f" — you're already up {wow:+.1f}% vs last week" if wow is not None and wow > 0 else ""
        price_dollars = round(top_avg_txn * 0.06, 2) if top_avg_txn > 0 else 0
        price_note    = f" (about {cur}{price_dollars:,.2f} more per sale)" if price_dollars > 0 else ""
        return [_strip_md(s) for s in [
            f"**Double down on {top_ref}:** Revenue is growing at +{growth_abs:.1f}%/day{wow_note}. Introduce a complementary item alongside {top_ref} while customers are in a buying mood — bundle or upsell first, then introduce.",
            f"**Test a price increase on {second_ref}:** Growth periods absorb price changes more easily. A 5–8% increase{price_note} for 2 weeks will tell you whether volume holds — if it does, that's pure margin with no extra work.",
            f"**Build loyalty around {top_ref}:** Traffic is up and {top_ref} drives {top_share_pct:.0f}% of your revenue. A loyalty program tied to {top_ref} is cheap, captures customers now, and extends the growth curve.",
            f"**Lock in supply for {top_ref}:** Stockouts hurt most when demand is rising. Confirm inventory and supplier lead times now — at {cur}{weekly_avg:,.0f}/week in revenue, one stockout week is a real loss.",
        ]]
    elif trend == "downward":
        wow_note    = f" (down {abs(wow):.1f}% vs last week)" if wow is not None and wow < 0 else ""
        weekly_loss = weekly_avg * (growth_abs / 100)
        return [_strip_md(s) for s in [
            f"**Run a 3-day promo on {top_ref} this week{wow_note}:** A flash sale or 'bring a friend' deal can interrupt a -{growth_abs:.1f}%/day slide — act now while it's still recoverable, not after another slow week.",
            f"**Drop {bottom_ref} from your active offer:** It contributes only {bottom_share_pct:.1f}% of total revenue ({cur}{bottom_rev:,.0f}). Low performers carry hidden costs — storage, time, and operational complexity. Remove it and focus energy on what works.",
            f"**Drive repeat visits with {top_ref}:** Keeping one existing customer costs 5× less than finding a new one. A 'come back this week' incentive tied to {top_ref} — your {cur}{top_rev:,.0f} earner — is your highest-ROI move right now.",
            f"**Re-engage past customers now:** At {cur}{weekly_avg:,.0f}/week and falling, a targeted 'We miss you' offer to lapsed buyers — featuring {top_ref} — can recover revenue faster than finding new customers.",
        ]]
    else:  # flat
        addon_price = max(1, round(top_avg_txn * 0.10)) if top_avg_txn > 0 else 2
        return [_strip_md(s) for s in [
            f"**Feature {top_ref} prominently for 2 weeks:** Revenue is flat at ~{cur}{weekly_avg:,.0f}/week. Moving it to your most visible position is free and can break the plateau — track weekly totals before and after.",
            f"**Add a {cur}{addon_price} add-on when {top_ref} is ordered:** With steady traffic the easiest win is a small complement or upgrade. Even a 15% attach rate on {top_ref} lifts your weekly average meaningfully.",
            f"**Create off-peak urgency:** Identify your 2 slowest hours and run a limited offer during them. This unlocks dormant revenue without cannibalizing {top_ref} peak sales.",
            f"**Invest in reviews for {top_ref}:** Flat growth often means weak new-customer discovery. A Google/Yelp push featuring {top_ref} costs nothing, takes one afternoon to set up, and compounds for months.",
        ]]


def _build_action_center(df: pd.DataFrame, product_clusters, currency: str = "$") -> dict:
    """Gather all analysis signals and rank by estimated dollar impact."""
    cur = currency
    has_dates = _has_dates(df)
    months = max((df["date"].max() - df["date"].min()).days / 30, 0.034) if has_dates else 1

    prod_agg = (
        df.groupby("product")
        .agg(quantity=("quantity", "sum"), revenue=("revenue", "sum"))
        .reset_index()
    )
    prod_agg["avg_price"] = prod_agg["revenue"] / prod_agg["quantity"].clip(lower=1)
    prod_agg["monthly_qty"] = prod_agg["quantity"] / months
    prod_lookup = prod_agg.set_index("product")
    prod_tx_counts = df.groupby("product").size()

    quick_wins: list = []
    watch_outs: list = []

    # 1. Price raise opportunities
    has_cost = "cost" in df.columns and df["cost"].notna().any()
    gross_margin_fallback = 0.65
    price_recs = _get_price_recommendations(df, currency=cur)
    for rec in price_recs:
        if rec["action"] == "↑ Raise Price" and rec["product"] in prod_lookup.index:
            mq = prod_lookup.loc[rec["product"], "monthly_qty"]
            margin_pct = rec.get("margin_pct") or gross_margin_fallback
            revenue_gain = mq * (rec["suggested"] - rec["current"])
            impact = revenue_gain * margin_pct
            impact_low = impact * 0.75
            impact_high = impact * 1.25
            metric_label = "profit" if has_cost else "revenue (est. profit)"
            # Use elasticity-derived confidence if available on the rec, else directional
            _price_confidence = rec.get("elasticity_confidence", "directional")
            _detail = (
                f"Selling ~{int(mq)}/mo at {cur}{rec['current']:.2f} — demand is high, "
                f"price is below your portfolio average. A 10% increase is unlikely to hurt volume. "
                f"({margin_pct:.0%} margin on this product)"
                if _price_confidence == "directional"
                else
                f"Selling ~{int(mq)}/mo at {cur}{rec['current']:.2f} — demand is high and "
                f"price is below your portfolio average. We can't estimate the demand response "
                f"from your current data — run a 2-week price test before committing."
            )
            quick_wins.append({
                "title": f"Raise **{rec['product']}** price → {cur}{rec['suggested']:.2f}",
                "detail": _detail,
                "impact_dollars": round(impact, 2),
                "impact_low": round(impact_low, 2),
                "impact_high": round(impact_high, 2),
                "confidence": _price_confidence,
                "impact_range": f"Could add ~{cur}{impact:,.0f}/month",
                "impact_label": f"Could add ~{cur}{impact:,.0f}/month",
                "n_transactions": int(prod_tx_counts.get(rec["product"], 0)),
                "priority": 1,
            })

    # 2. Rising Stars
    # Dynamic floor: 20th percentile of per-product revenue over the last 30 days.
    # Prevents surfacing products with trivial absolute revenue even if growth % is high.
    # Falls back to $10 if there's insufficient date data.
    if _has_dates(df):
        _max_date = df["date"].max()
        _recent_start = _max_date - pd.Timedelta(days=29)
        _recent_rev_by_product = (
            df[df["date"] >= _recent_start]
            .groupby("product")["revenue"]
            .sum()
        )
        _min_rev_floor = float(
            _recent_rev_by_product.quantile(0.20)
        ) if len(_recent_rev_by_product) >= 5 else 10.0
        _min_rev_floor = max(_min_rev_floor, 10.0)  # hard minimum $10
    else:
        _min_rev_floor = 10.0

    rising = _find_rising_stars(df, n=3, min_revenue=_min_rev_floor)
    if rising is not None:
        for _, row in rising.iterrows():
            potential = row["recent_rev"] * (row["growth_pct"] / 100)
            quick_wins.append({
                "title": f"Amplify **{row['product']}** — gaining momentum fast",
                "detail": (
                    f"Revenue up **{row['growth_pct']:.0f}%** in the last 30 days "
                    f"({cur}{row['recent_rev']:,.0f} recent). Feature as a daily special, "
                    f"stock up, and promote to sustain the trend."
                ),
                "impact_dollars": round(potential, 2),
                "confidence": "directional",
                "impact_range": f"Could add ~{cur}{potential:,.0f}/month",
                "impact_label": f"Could add ~{cur}{potential:,.0f}/month",
                "n_transactions": int(prod_tx_counts.get(row["product"], 0)),
                "priority": 2,
            })

    # 3. Cross-cluster bundle opportunity
    if product_clusters is not None:
        stars = product_clusters[product_clusters["category"] == "Stars"].nlargest(1, "revenue")
        gems  = product_clusters[product_clusters["category"] == "Hidden Gems"].nlargest(1, "quantity")
        if not stars.empty and not gems.empty:
            star_name = str(stars.iloc[0]["product"])
            gem_name  = str(gems.iloc[0]["product"])
            star_rev  = float(stars.iloc[0]["revenue"])
            gem_qty   = int(gems.iloc[0]["quantity"])
            star_cat = str(stars.iloc[0]["category"])
            gem_cat  = str(gems.iloc[0]["category"])
            if star_cat != gem_cat and star_name != gem_name:
                gem_price = float(gems.iloc[0]["revenue"]) / max(gem_qty, 1)
                bundle_upside = gem_price * (float(stars.iloc[0]["quantity"]) * 0.10)
                bundle_low  = round(bundle_upside * 0.6, 2)
                bundle_high = round(bundle_upside * 1.4, 2)
                quick_wins.append({
                    "title": f"Bundle **{star_name}** with **{gem_name}** to lift avg order",
                    "detail": (
                        f"**{star_name}** drives your highest volume. "
                        f"**{gem_name}** has strong unit economics but low awareness. "
                        f"An 'Add {gem_name} for just a little more' upsell at the point of sale captures revenue "
                        f"from existing customers at zero acquisition cost. Easy to test — no discounting required."
                    ),
                    "impact_dollars": round(bundle_upside, 2),
                    "impact_low": bundle_low,
                    "impact_high": bundle_high,
                    "confidence": "directional",
                    "impact_range": f"~{cur}{bundle_upside:,.0f}/month if 1 in 10 customers add it — test first",
                    "impact_label": f"~{cur}{bundle_upside:,.0f}/month (estimated, 10% attach rate assumed)",
                    "n_transactions": int(prod_tx_counts.get(star_name, 0)),
                    "priority": 3,
                })
        elif product_clusters is not None and not gems.empty:
            gem_row = gems.iloc[0]
            quick_wins.append({
                "title": f"Spotlight **{gem_row['product']}** — Hidden Gem with untapped demand",
                "detail": (
                    f"Sells well ({int(gem_row['quantity'])} units) but generates modest revenue. "
                    f"Feature as 'Staff Pick', highlight it at the point of sale, or run a 1-week promotion."
                ),
                "impact_dollars": None,
                "impact_label": "High potential",
                "n_transactions": int(prod_tx_counts.get(gem_row["product"], 0)),
                "priority": 3,
            })

    # 4. WoW momentum
    insights = _detect_overview_insights(df, currency=cur)
    wow = insights.get("wow_pct", 0)
    if wow > 10:
        quick_wins.append({
            "title": f"Your sales are up {wow:.0f}% this week — capitalize now",
            "detail": (
                f"Sales are up {wow:.1f}% compared to last week. Run a limited upsell on your top item "
                f"while customers are already engaged — don't let the surge pass unused."
            ),
            "impact_dollars": None,
            "impact_label": f"+{wow:.0f}% this week vs last",
            "n_transactions": len(df),
            "priority": 4,
        })
    elif wow < -10:
        watch_outs.append({
            "title": f"Sales dropped {abs(wow):.0f}% this week — act fast",
            "detail": (
                f"Sales are down {abs(wow):.1f}% compared to last week. A 3-day flash sale or 'bring a friend' deal "
                f"on your best seller can interrupt the slide. Act this week while it's recoverable."
            ),
            "impact_dollars": None,
            "impact_label": f"{wow:.0f}% this week vs last",
            "n_transactions": len(df),
            "priority": 1,
        })

    # 5. Declining products
    declining = _find_declining_products(df)
    for item in declining[:3]:
        at_risk_total = item["older_rev"] - item["recent_rev"]
        at_risk_monthly = at_risk_total
        at_risk_low = at_risk_monthly * 0.75
        at_risk_high = at_risk_monthly * 1.25
        if item.get("seasonality") == "possibly_seasonal":
            seasonality_note = (
                f" Note: your overall business is also down {abs(item['overall_pct']):.0f}% — "
                f"this may be a seasonal dip. Monitor before making changes."
            )
        elif item.get("seasonality") == "structural":
            seasonality_note = (
                f" Your overall business is {'up' if item['overall_pct'] > 0 else 'flat'} "
                f"({item['overall_pct']:+.0f}%) — this looks like a problem specific to this item."
            )
        else:
            seasonality_note = ""
        watch_outs.append({
            "title": f"**{item['product']}** is losing revenue — investigate now",
            "detail": (
                f"Revenue dropped {item['decline_pct']:.0f}% "
                f"({cur}{item['older_rev']:,.0f} → {cur}{item['recent_rev']:,.0f}). "
                f"Bundle with a Star product, run a flash sale, or evaluate for removal."
                f"{seasonality_note}"
            ),
            "impact_dollars": round(at_risk_monthly, 2),
            "impact_low": round(at_risk_low, 2),
            "impact_high": round(at_risk_high, 2),
            "confidence": "directional",
            "impact_range": f"~{cur}{at_risk_monthly:,.0f}/month at risk if nothing changes",
            "impact_label": f"~{cur}{at_risk_monthly:,.0f}/month at risk",
            "n_transactions": int(prod_tx_counts.get(item["product"], 0)),
            "priority": 2,
        })

    # 6. Low Activity products
    if product_clusters is not None:
        dead = product_clusters[product_clusters["category"] == "Low Activity"].nlargest(3, "revenue")
        if not dead.empty:
            names = ", ".join(str(x) for x in dead["product"].tolist()[:3])
            prescription = _prescribe_low_activity(df, product_clusters, currency=cur)
            if prescription is not None:
                watch_outs.append(prescription)
            else:
                _dead_txns = sum(int(prod_tx_counts.get(p, 0)) for p in dead["product"].tolist()[:3])
                watch_outs.append({
                    "title": f"These items are barely selling: {names}",
                    "detail": (
                        "Low sales and low revenue. Before removing anything, check how "
                        "long each item has been in your offer — something new may just "
                        "need more time and visibility."
                    ),
                    "impact_dollars": None,
                    "impact_label": "Operational cost",
                    "n_transactions": _dead_txns,
                    "priority": 3,
                })

    # 7. Overall trend direction
    # Require 30+ days before showing a trend warning — shorter windows can't
    # reliably distinguish a real trend from normal week-to-week variance.
    _date_span_days = int(months * 30) if has_dates else 0
    trend = insights.get("trend", "flat")
    if trend == "downward" and _date_span_days >= 30:
        _slope_pct = abs(insights.get("slope_pct", 0))
        _declining = _find_declining_products(df)
        _top_decliner = _declining[0]["product"] if _declining else None
        _decliner_note = (
            f" {_top_decliner} is showing the steepest drop."
            if _top_decliner else ""
        )
        watch_outs.append({
            "title": f"Revenue trending down {_slope_pct:.1f}%/day on average — time to act",
            "detail": (
                f"Your overall sales trend has been pointing downward over the last {_date_span_days} days.{_decliner_note} "
                f"Check whether service quality has slipped during peak hours, or whether a key product needs a promotion."
            ),
            "impact_dollars": None,
            "impact_label": f"~{_slope_pct:.1f}%/day decline",
            "n_transactions": len(df),
            "priority": 4,
        })
    elif trend == "downward" and _date_span_days < 30:
        # Not enough history — show a softer informational note instead of an alarm
        watch_outs.append({
            "title": "Revenue trend unclear — upload more history for a reliable signal",
            "detail": (
                f"You have {_date_span_days} days of data. We need at least 30 days to reliably "
                f"detect a trend vs normal week-to-week variance. Keep uploading and check back."
            ),
            "impact_dollars": None,
            "impact_label": "Need more data",
            "confidence": "insufficient",
            "n_transactions": len(df),
            "priority": 5,
        })

    # Normalize impact_labels to consistent tier format
    for items in (quick_wins, watch_outs):
        for item in items:
            imp = item.get("impact_dollars")
            if imp is not None and imp > 0:
                item["impact_label"] = _tier_impact_label(float(imp), cur)
            elif not item.get("impact_label"):
                item["impact_label"] = ""

    def _sort_key(a):
        return (-(float(a["impact_dollars"]) if a.get("impact_dollars") is not None else 0.0), a.get("priority", 99))

    quick_wins.sort(key=_sort_key)
    watch_outs.sort(key=_sort_key)

    # Strip Markdown bold/italic from all user-facing text fields
    _text_keys = ("title", "detail", "impact_label", "impact_range")
    for items in (quick_wins, watch_outs):
        for item in items:
            for k in _text_keys:
                if k in item and isinstance(item[k], str):
                    item[k] = _strip_md(item[k])

    return {"quick_wins": quick_wins, "watch_outs": watch_outs}
