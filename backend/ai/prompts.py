"""Prompt-building helpers — extracted from app.py."""
from __future__ import annotations

import re

import pandas as pd

from engine.safety import _has_dates
from engine.insights import _detect_overview_insights, _find_rising_stars, _find_declining_products
from engine.pricing import _get_price_recommendations
from engine.apriori import _compute_basket_rules


def _sanitize_for_prompt(value: str, max_len: int = 120) -> str:
    """Remove characters that could break prompt structure and cap length."""
    cleaned = str(value).replace("\n", " ").replace("\r", " ").replace("\x00", "")
    return cleaned[:max_len]


MARGIN_CAVEAT = (
    "Note on margins: all profit figures below are rough estimates based on industry "
    "averages — actual margins vary significantly by product type. Verify impact with "
    "real cost data before acting on profit-based recommendations."
)

# Industry-specific margin fallbacks (applied when no cost column exists).
# Only used when _detect_industry_from_data() returns a confident match.
_INDUSTRY_MARGIN_DEFAULTS: dict[str, float] = {
    "café": 0.68,           # blended: drinks ~75%, food ~45%
    "restaurant": 0.62,     # blended: mains ~60%, drinks ~75%
    "bakery": 0.55,
    "clothing retail": 0.50,
    "beauty / salon": 0.65,
}


_INDUSTRY_TEMPLATES: dict = {
    "(none)": {
        "label": "(none)",
        "primary_metrics": [],
        "surface_first":   [],
        "collapse_first":  [],
        "action_center_emphasis": [],
        "ai_hint": "",
    },
    "Restaurant / Bar": {
        "label": "Restaurant / Bar",
        "primary_metrics":  ["revenue", "avg_order_value"],
        "surface_first":    ["declining_products"],
        "collapse_first":   ["forecast", "basket"],
        "action_center_emphasis": ["declining", "wow"],
        "ai_hint": (
            "Focus on table turn rate, check average, and service period performance. "
            "Flag items with food cost > 35%. Use 'covers', 'check average', 'comp' language."
        ),
    },
    "Retail": {
        "label": "Retail",
        "primary_metrics":  ["revenue", "units_sold", "sell_through"],
        "surface_first":    ["best_sellers", "low_activity", "pricing"],
        "collapse_first":   [],
        "action_center_emphasis": ["low_activity", "pricing", "bundle"],
        "ai_hint": (
            "Focus on sell-through rate, slow-moving inventory, and margin per SKU. "
            "Use 'units sold', 'markdown', 'SKU', 'footfall' language."
        ),
    },
    "Café / Coffee Shop": {
        "label": "Café / Coffee Shop",
        "primary_metrics":  ["revenue", "avg_order_value", "top_product"],
        "surface_first":    ["best_sellers", "rising_stars"],
        "collapse_first":   ["forecast"],
        "action_center_emphasis": ["rising", "bundle", "pricing"],
        "ai_hint": (
            "Focus on loyalty, morning rush, and add-on upsells. "
            "Benchmark ticket at $6–9 drink-only. Use 'covers', 'upsell', 'regulars' language."
        ),
    },
    "E-commerce": {
        "label": "E-commerce",
        "primary_metrics":  ["revenue", "avg_order_value", "units_sold"],
        "surface_first":    ["best_sellers", "basket", "pricing"],
        "collapse_first":   [],
        "action_center_emphasis": ["bundle", "pricing", "rising"],
        "ai_hint": (
            "Focus on basket size, repeat purchase rates, and conversion by product. "
            "Use 'AOV', 'SKU', 'add-to-cart', 'bundle' language."
        ),
    },
    "Services": {
        "label": "Services",
        "primary_metrics":  ["revenue", "avg_order_value"],
        "surface_first":    ["best_sellers"],
        "collapse_first":   ["basket", "forecast"],
        "action_center_emphasis": ["pricing", "rising"],
        "ai_hint": (
            "Focus on service utilization, appointment density, and upsell per visit. "
            "Use 'appointments', 'utilization', 'add-on service' language."
        ),
    },
}


def _infer_industry_template(df: pd.DataFrame, raw_cols: list[str] | None = None) -> str | None:
    """Return the most likely _INDUSTRY_TEMPLATES key from product names, or None."""
    if "product" not in df.columns or df.empty:
        return None

    products = df["product"].dropna().astype(str).str.lower().unique().tolist()
    if not products:
        return None

    _KEYWORDS: dict[str, list[str]] = {
        "Café / Coffee Shop": [
            "espresso", "latte", "cappuccino", "americano", "flat white",
            "cold brew", "drip", "cortado", "matcha", "chai",
            "croissant", "muffin", "scone", "bagel",
        ],
        "Restaurant / Bar": [
            "burger", "pizza", "pasta", "steak", "wings", "nachos",
            "cocktail", "beer", "wine", "draft", "entrée", "appetizer",
            "fries", "tacos", "sushi", "ramen",
        ],
        "Retail": [
            "shirt", "pants", "jacket", "dress", "shoe", "hat", "bag",
            "wallet", "hoodie", "jeans", "tee", "blouse", "scarf", "belt",
            "cap", "hardware", "tool", "wrench", "bolt", "lumber",
        ],
        "Services": [
            "haircut", "trim", "color", "massage", "facial", "manicure",
            "pedicure", "consult", "session", "lesson", "class",
            "appointment", "fitting", "repair", "service",
        ],
    }

    scores: dict[str, int] = {}
    for category, keywords in _KEYWORDS.items():
        scores[category] = sum(1 for p in products if any(kw in p for kw in keywords))

    _raw_cols_lower = [c.lower() for c in (raw_cols or [])]
    _has_sku_col = any("sku" in c or c == "order_id" for c in _raw_cols_lower)
    if _has_sku_col:
        _sku_pat = re.compile(r"^[a-z0-9]{4,12}$")
        _no_space = sum(1 for p in products if " " not in p and _sku_pat.match(p))
        scores["E-commerce"] = _no_space if len(products) > 0 and _no_space / len(products) >= 0.5 else 0
    else:
        scores["E-commerce"] = 0

    qualified = {cat: cnt for cat, cnt in scores.items() if cnt >= 2}
    if not qualified:
        return None

    top = max(qualified.values())
    winners = [cat for cat, cnt in qualified.items() if cnt == top]
    return winners[0] if len(winners) == 1 else None


def _build_data_context(df: pd.DataFrame, product_clusters, currency: str = "$", forecast_data: dict | None = None) -> str:
    """Build a rich text summary of the data to feed to the AI as context."""
    lines = []
    sym = currency

    total_revenue = df["revenue"].sum()
    total_orders = len(df)
    avg_order = total_revenue / total_orders if total_orders else 0
    unique_products = df["product"].nunique()
    has_cost = "cost" in df.columns and df["cost"].notna().any()
    lines.append("BUSINESS OVERVIEW:")
    lines.append(f"- Total revenue: {sym}{total_revenue:,.2f}")
    lines.append(f"- Total orders/rows: {total_orders:,}")
    lines.append(f"- Average order value: {sym}{avg_order:.2f}")
    lines.append(f"- Unique products: {unique_products}")
    lines.append(f"- Cost data available: {'Yes' if has_cost else 'No (margin estimates only)'}")

    if _has_dates(df):
        date_min = df["date"].min().date()
        date_max = df["date"].max().date()
        span_days = (date_max - date_min).days
        span_months = round(span_days / 30, 1)
        lines.append(f"- Data period: {date_min} to {date_max} ({span_days} days / ~{span_months} months)")
        daily_avg = total_revenue / max(span_days, 1)
        lines.append(f"- Average daily revenue: {sym}{daily_avg:,.2f}")
    else:
        lines.append("- No date column available (snapshot data only)")

    if "location" in df.columns and df["location"].nunique() > 1:
        by_loc = df.groupby("location")["revenue"].sum().sort_values(ascending=False)
        lines.append("\nREVENUE BY LOCATION:")
        for loc, rev in by_loc.items():
            lines.append(f"- {_sanitize_for_prompt(loc)}: {sym}{rev:,.2f}")

    agg_dict = {"quantity": ("quantity", "sum"), "revenue": ("revenue", "sum")}
    if has_cost:
        agg_dict["cost"] = ("cost", "sum")
    top_products = (
        df.groupby("product")
        .agg(**agg_dict)
        .reset_index()
        .nlargest(10, "revenue")
    )
    top_products["avg_price"] = top_products["revenue"] / top_products["quantity"].clip(lower=1)
    if has_cost:
        top_products["gross_profit"] = top_products["revenue"] - top_products["cost"]
        top_products["margin_pct"] = top_products["gross_profit"] / top_products["revenue"].clip(lower=0.01)
    _industry = _detect_industry_from_data(df)
    gross_margin_fallback = _INDUSTRY_MARGIN_DEFAULTS.get(_industry, 0.65)

    lines.append("\nTOP 10 PRODUCTS BY REVENUE:")
    if not has_cost:
        lines.append(
            f"(Profit estimates below use a ~{gross_margin_fallback:.0%} industry average — "
            "actual margins vary by product. Do not present these as exact figures.)"
        )
    for _, row in top_products.iterrows():
        prod = _sanitize_for_prompt(row["product"])
        if has_cost:
            lines.append(
                f"- {prod}: {sym}{row['revenue']:,.2f} revenue, {int(row['quantity'])} units, "
                f"avg price {sym}{row['avg_price']:.2f}, gross profit {sym}{row['gross_profit']:,.2f} "
                f"({row['margin_pct']:.0%} margin)"
            )
        else:
            est_profit = row["revenue"] * gross_margin_fallback
            lines.append(
                f"- {prod}: {sym}{row['revenue']:,.2f} revenue, {int(row['quantity'])} units, "
                f"avg price {sym}{row['avg_price']:.2f}, est. profit ~{sym}{est_profit:,.2f} "
                f"(~{gross_margin_fallback:.0%} est. margin — actual varies by product)"
            )

    if product_clusters is not None and len(product_clusters) >= 4:
        lines.append("\nPRODUCT CLUSTERS (K-Means):")
        for cat in ["Stars", "Cash Cows", "Hidden Gems", "Low Activity"]:
            group = product_clusters[product_clusters["category"] == cat].nlargest(5, "revenue")
            if not group.empty:
                names = ", ".join(_sanitize_for_prompt(p) for p in group["product"].astype(str))
                lines.append(f"- {cat}: {names}")

    if _has_dates(df):
        df_time = df.copy()
        df_time["hour"] = df_time["date"].dt.hour
        df_time["day_of_week"] = df_time["date"].dt.day_name()
        by_hour = df_time.groupby("hour")["revenue"].sum()
        by_day = df_time.groupby("day_of_week")["revenue"].sum()
        if not by_hour.empty and not by_day.empty:
            peak_hour = by_hour.idxmax()
            peak_day = by_day.idxmax()
            lines.append("\nPEAK TRADING TIMES:")
            # H5: Only report busiest hour if the data actually has time variation
            _has_time = df["date"].dt.hour.nunique() > 2
            if _has_time:
                lines.append(f"- Busiest hour: {peak_hour}:00")
            lines.append(f"- Busiest day: {peak_day}")

    agg_price = df.groupby("product").agg(
        quantity=("quantity", "sum"), revenue=("revenue", "sum")
    ).reset_index()
    agg_price["avg_price"] = agg_price["revenue"] / agg_price["quantity"].clip(lower=1)
    lines.append("\nPRICING:")
    lines.append(f"- Lowest avg product price: {sym}{agg_price['avg_price'].min():.2f}")
    lines.append(f"- Highest avg product price: {sym}{agg_price['avg_price'].max():.2f}")
    lines.append(f"- Median avg product price: {sym}{agg_price['avg_price'].median():.2f}")

    if _has_dates(df):
        insights = _detect_overview_insights(df, currency=sym)
        wow = insights.get("wow_pct")
        trend = insights.get("trend", "flat")
        slope_pct = insights.get("slope_pct", 0)
        lines.append("\nMOMENTUM:")
        lines.append(f"- Overall trend: {trend} ({slope_pct:+.2f}% per day avg)")
        if wow is not None:
            lines.append(f"- Week-over-week change: {wow:+.1f}%")

        rising = _find_rising_stars(df, n=5)
        if rising is not None and not rising.empty:
            lines.append("\nRISING PRODUCTS (last 30 days vs prior period):")
            for _, row in rising.iterrows():
                lines.append(
                    f"- {_sanitize_for_prompt(row['product'])}: +{row['growth_pct']:.0f}% revenue growth "
                    f"({sym}{row['recent_rev']:,.0f} recent)"
                )

        declining = _find_declining_products(df)
        if declining:
            lines.append("\nDECLINING PRODUCTS:")
            for item in declining[:5]:
                lines.append(
                    f"- {_sanitize_for_prompt(item['product'])}: -{item['decline_pct']:.0f}% revenue "
                    f"({sym}{item['older_rev']:,.0f} → {sym}{item['recent_rev']:,.0f}), "
                    f"seasonality: {item['seasonality']}"
                )

    price_recs = _get_price_recommendations(df, currency=sym)
    if price_recs:
        lines.append("\nPRICING OPPORTUNITIES:")
        for rec in price_recs[:6]:
            lines.append(
                f"- {_sanitize_for_prompt(rec['product'])}: {_sanitize_for_prompt(rec['action'])} "
                f"({sym}{rec['current']:.2f} → {sym}{rec['suggested']:.2f}). {_sanitize_for_prompt(rec['reason'])}"
            )

    try:
        from engine.apriori import _MLXTEND_AVAILABLE
        if _MLXTEND_AVAILABLE and _has_dates(df):
            _, basket_rules, basket_err, _bm = _compute_basket_rules(df)
            _is_proxy = _bm and "transaction ID" not in _bm
            if basket_rules is not None and not basket_rules.empty:
                if _is_proxy:
                    lines.append(
                        "\nPRODUCT CO-OCCURRENCE (proxy only — day × location, NOT individual baskets):"
                    )
                else:
                    lines.append("\nTOP PRODUCT BUNDLES (market basket — order-level, reliable):")
                for _, rule in basket_rules.head(5).iterrows():
                    lines.append(
                        f"- {_sanitize_for_prompt(rule['antecedent'])} → {_sanitize_for_prompt(rule['consequent'])} "
                        f"(lift {rule['lift']:.1f}×, confidence {rule['confidence']*100:.0f}%)"
                    )
    except Exception:
        pass

    # M6: Add forecast data to AI context if available
    if forecast_data and forecast_data.get("trend"):
        trend = forecast_data["trend"]
        growth_actions = forecast_data.get("growth_actions", [])
        lines.append(
            f"\nFORECAST OUTLOOK:\n"
            f"Revenue trend: {trend}"
        )
        if growth_actions:
            lines.append(f"Top growth action: {growth_actions[0]}")

    return "\n".join(lines)


def _build_profile_context(business_profile: dict | None = None) -> str:
    """Return a compact profile block for AI prompt injection."""
    profile = business_profile or {}
    if not profile.get("profile_saved"):
        return ""

    _skip = {"", "(not set)"}
    lines = []
    if profile.get("business_name", "") not in _skip:
        lines.append(f"- Name: {profile['business_name']}")
    if profile.get("industry", "") not in _skip:
        lines.append(f"- Industry: {profile['industry']}")
    if profile.get("business_size", "") not in _skip:
        lines.append(f"- Size: {profile['business_size']}")
    if profile.get("customer_type", "") not in _skip:
        lines.append(f"- Customers: {profile['customer_type']}")
    if profile.get("seasonality", "") not in _skip:
        lines.append(f"- Seasonality: {profile['seasonality']}")
    if profile.get("goals", "") not in _skip:
        lines.append(f"- Current goal: {profile['goals']}")

    if not lines:
        return ""

    return "BUSINESS PROFILE:\n" + "\n".join(lines)


def _detect_industry_from_data(df: pd.DataFrame) -> str:
    """Pure heuristic industry detection from product names."""
    try:
        products_lower = df["product"].dropna().astype(str).str.lower().tolist()

        def _hits(keywords):
            return sum(1 for p in products_lower if any(kw in p for kw in keywords))

        if _hits(["espresso", "latte", "cappuccino", "americano", "flat white",
                   "cold brew", "macchiato", "cortado"]) >= 2:
            return "café"
        elif _hits(["burger", "pizza", "pasta", "entree", "entrée", "starter",
                    "main course", "side dish", "dessert", "appetizer"]) >= 2:
            return "restaurant"
        elif _hits(["croissant", "muffin", "loaf", "sourdough", "brioche",
                    "éclair", "tart", "scone"]) >= 2:
            return "bakery"
        elif _hits(["t-shirt", "jeans", "dress", "jacket", "sneakers",
                    "blouse", "hoodie", "cardigan"]) >= 2:
            return "clothing retail"
        elif _hits(["shampoo", "conditioner", "facial", "massage",
                    "manicure", "wax", "blowout"]) >= 2:
            return "beauty / salon"
        return ""
    except Exception:
        return ""


def build_data_summary(df: pd.DataFrame, currency: str = "$") -> dict:
    """Build a concise data summary dict for the AI advisor system prompt."""
    sym = currency
    summary: dict = {}

    # date_range: "Jan 1 – Mar 31, 2025"
    if _has_dates(df):
        d_min = df["date"].min()
        d_max = df["date"].max()
        summary["date_range"] = (
            f"{d_min.strftime('%b')} {d_min.day} – "
            f"{d_max.strftime('%b')} {d_max.day}, {d_max.year}"
        )
    else:
        summary["date_range"] = "unknown"

    # total_transactions
    summary["total_transactions"] = len(df)

    # top_products: top 5 by revenue
    top5 = (
        df.groupby("product")["revenue"]
        .sum()
        .nlargest(5)
        .reset_index()
    )
    summary["top_products"] = [
        f"{row['product']} ({sym}{row['revenue']:,.0f} total)"
        for _, row in top5.iterrows()
    ]

    # best_dow: day with highest average daily revenue
    if _has_dates(df):
        daily = df.groupby(df["date"].dt.date)["revenue"].sum().reset_index()
        daily.columns = ["date", "rev"]
        daily["dow"] = pd.to_datetime(daily["date"]).dt.day_name()
        best_dow = daily.groupby("dow")["rev"].mean().idxmax()
        summary["best_dow"] = best_dow
    else:
        summary["best_dow"] = "unknown"

    # anomalies: plain-language descriptions, max 3
    try:
        from engine.anomaly import detect_anomalies
        anom_list = detect_anomalies(df)
        if anom_list:
            descs = []
            for a in anom_list[:3]:
                direction = "spike" if a.get("direction") == "spike" else "drop"
                label = a.get("date_label") or a.get("date", "")
                descs.append(f"Revenue {direction} on {label}")
            summary["anomalies"] = descs
        else:
            summary["anomalies"] = "none detected"
    except Exception:
        summary["anomalies"] = "none detected"

    # recent_trend: plain English
    if _has_dates(df):
        try:
            insights = _detect_overview_insights(df, currency=sym)
            wow = insights.get("wow_pct")
            trend = insights.get("trend", "flat")
            slope_pct = abs(insights.get("slope_pct", 0))
            if wow is not None:
                direction = "up" if wow > 0 else "down"
                summary["recent_trend"] = (
                    f"Revenue is {direction} {abs(wow):.0f}% over the last 2 weeks"
                )
            elif trend == "upward":
                summary["recent_trend"] = (
                    f"Revenue is growing at roughly {slope_pct:.1f}% per day"
                )
            elif trend == "downward":
                summary["recent_trend"] = (
                    f"Revenue is falling at roughly {slope_pct:.1f}% per day"
                )
            else:
                summary["recent_trend"] = "Revenue is roughly flat"
        except Exception:
            summary["recent_trend"] = "unknown"
    else:
        summary["recent_trend"] = "unknown (no date data)"

    return summary


def build_advisor_system_prompt(data_summary: dict, profile: dict | None = None, rich_context: str | None = None) -> str:
    """Build the AI advisor system prompt from a data summary dict."""
    profile_block = ""
    _p = profile or {}
    if _p.get("business_name"):
        profile_block += f"\nBusiness name: {_sanitize_for_prompt(_p['business_name'])}"
    if _p.get("industry"):
        profile_block += f"\nIndustry: {_sanitize_for_prompt(_p['industry'])}"

    rich_context_block = f"\n\nFULL BUSINESS DATA:\n{rich_context}" if rich_context else ""

    return f"""You are a sharp retail analyst who has read the actual sales data for this business. You think like an operator, not a consultant.

{MARGIN_CAVEAT}

Your data summary:
- Date range: {data_summary.get('date_range', 'unknown')}
- Total transactions: {data_summary.get('total_transactions', 0)}
- Top 5 products by revenue: {data_summary.get('top_products', [])}
- Biggest revenue day of week: {data_summary.get('best_dow', 'unknown')}
- Any unusual patterns: {data_summary.get('anomalies', 'none detected')}
- Recent trend: {data_summary.get('recent_trend', 'unknown')}
{profile_block}{rich_context_block}

Rules you must follow:
1. Only give advice grounded in the data above. Never give generic business advice not connected to their numbers.
2. If you cannot answer from the data, say exactly: "I don't have enough data to answer that — try asking about your top products, busiest days, or recent trends."
3. Never use these words: elasticity, MAD, cluster, Apriori, coefficient, Z-score, statistical, correlation, regression, confidence interval, p-value, anomaly. Replace with plain business language.
4. Keep answers to 3 sentences maximum unless the user asks for more detail.
5. End every answer with exactly one follow-up question the user should consider, prefixed with "Worth asking:"
6. Speak directly to the owner. Use "you" and "your business" — never "the business" or "the data shows."

SPECIFICITY RULES — every recommendation must be:
- NAMED: Name the product. Name the lever (price delta, bundle partner, channel). Name the mechanism.
  NOT: "Build loyalty around your top item"
  YES: "Set up SMS loyalty with 10% off for 2x/month buyers, targeting your top item"
- DATA-BACKED: Lead with actual numbers (revenue/day, growth %, ranking, units/week).
  NOT: "This product is growing fast"
  YES: "Growing +132% over 25 weeks, $27/day incremental revenue"
- ACTIONABLE: A non-technical owner can execute it in <30 minutes. Include exact timeline.
  NOT: "Consider introducing a loyalty program"
  YES: "Set up SMS loyalty in 30 min, launch Monday"
- QUANTIFIED: Show expected upside ($), downside risk, payback period, decision rule.
  NOT: "Could increase margin significantly"
  YES: "+$57/week if volume holds; revert if >15% volume drop after 14 days"
- TESTABLE: Give a decision rule — when to roll out, revert, or iterate.
  NOT: "Monitor closely"
  YES: "Measure after 14 days. Roll out if revenue > baseline + 5%. Revert if < baseline − 15%."

LANGUAGE RULES:
- Banned: "could," "may," "might," "consider," "potentially," "it's possible"
- Required: "Test," "Measure," "If X then Y," exact dollar amounts, exact timelines

Example good answer:
"Your Oat Milk Latte is your #1 item at $31/day revenue, steady for 3 months. Test raising it $0.50 — at current volume, that's +$45/week pure margin. If volume drops more than 15% in the first week, revert. Worth asking: Do customers who buy it also add food?"

Example bad answer (never do this):
"You might want to consider building loyalty around your top products, as this could potentially increase revenue over time."
"""


def _build_persona_system_prompt(industry: str) -> str:
    """Return an industry-specific persona instruction block."""
    if not industry:
        return ""

    mapping = {
        "café": (
            "This is a café or coffee shop. Use café-appropriate language: "
            "'covers' for customer visits, 'upsell' for add-ons, 'loyalty' for regulars. "
            "Benchmark average ticket at $6–9 for drink-only, $12–16 with food. "
            "Staffing advice should reference morning rush and afternoon lull patterns. "
            "Promotions should focus on loyalty schemes, daily specials, and seasonal drinks."
        ),
        "restaurant": (
            "This is a restaurant or bar. Use restaurant-appropriate language: "
            "'covers' for table turns, 'check average' for AOV, 'comp' for discounts. "
            "Benchmark check average at $18–30 casual, $40+ fine dining. "
            "Flag any items with food cost above 35% as margin risks. "
            "Staffing advice should reference service periods: breakfast, lunch, dinner."
        ),
        "bakery": (
            "This is a bakery or patisserie. "
            "Flag low-margin items (bread, simple pastries) vs high-margin (cakes, tarts). "
            "Waste is a key concern — declining items should be flagged as waste risk. "
            "Promotions should focus on end-of-day markdowns and pre-order bundles."
        ),
        "clothing retail": (
            "This is a clothing or accessories retail store. "
            "Use retail language: 'units sold', 'sell-through rate', 'markdown'. "
            "Slow-moving inventory carries carrying cost — flag items unsold for 60+ days. "
            "Promotions should focus on bundle offers and clearance events."
        ),
        "beauty / salon": (
            "This is a beauty salon or spa. "
            "Services are the primary product. Flag any service with high time cost vs revenue. "
            "Upsell language: 'add-on treatment', 'express service'. "
            "Staffing advice should reference appointment density and peak booking days."
        ),
    }

    return mapping.get(
        industry,
        f"This is a {industry} business. "
        "Tailor all advice to the specific dynamics and language of this industry.",
    )
