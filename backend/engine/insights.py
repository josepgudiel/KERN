"""Overview insights, WoW, period comparison — extracted from app.py."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .safety import (
    _has_dates, _MAD_ANOMALY_Z, _MIN_PRODUCT_TXN_FOR_PERIOD,
)


def _detect_overview_insights(df: pd.DataFrame, currency: str = "$") -> dict:
    """Detect revenue trends and anomalies; return insights + recommendations."""
    out: dict = {"has_dates": False, "insights": [], "anomalies": [], "recommendations": [], "trend": "flat"}
    if not _has_dates(df):
        return out
    out["has_dates"] = True
    dfc = df.copy()
    dfc["date_only"] = dfc["date"].dt.date
    _daily_raw = dfc.groupby("date_only")["revenue"].sum().sort_index()
    _full_idx = pd.date_range(_daily_raw.index.min(), _daily_raw.index.max(), freq="D").date
    daily = _daily_raw.reindex(_full_idx, fill_value=0.0)
    n = len(daily)

    # Week-over-week
    if n >= 14:
        last7 = daily.tail(7).sum()
        prev7 = daily.tail(14).head(7).sum()
        wow = (last7 - prev7) / prev7 * 100 if prev7 > 0 else 0
        out["wow_pct"] = round(wow, 1)
        dollar_delta = last7 - prev7
        delta_str = f"{currency}{abs(dollar_delta):,.0f} {'more' if dollar_delta >= 0 else 'less'} than last week"
        if wow > 10:
            out["insights"].append(f"Revenue is up **{wow:+.1f}%** this week vs last ({delta_str}) — strong momentum.")
            out["recommendations"].append(
                f"Momentum is on your side (+{delta_str}) — run a limited-time upsell on your top item this week to amplify the surge while customers are engaged."
            )
        elif wow < -10:
            out["insights"].append(f"Revenue is down **{wow:+.1f}%** vs last week ({delta_str}) — needs attention.")
            out["recommendations"].append(
                f"Revenue slipped {delta_str}. A quick 'bring a friend' deal or 3-day flash sale on your best seller can interrupt the slide. Act this week while it's recoverable."
            )
        else:
            out["insights"].append(f"Revenue is steady — this week vs last week: **{wow:+.1f}%** ({delta_str}).")
            out["recommendations"].append(
                "Steady is safe, not growing. Try a daily special this week — even small lifts in average order value compound meaningfully over time."
            )

    # Anomaly detection (robust MAD-based)
    if n >= 14:
        _daily_txn_counts = dfc.groupby("date_only").size()
        _daily_txn_counts = _daily_txn_counts.reindex(_full_idx, fill_value=0)
        _MIN_TXN_PER_DAY_FOR_ANOMALY = 3
        _sufficient_days = _daily_txn_counts >= _MIN_TXN_PER_DAY_FOR_ANOMALY
        daily_for_anomaly = daily[_sufficient_days]
        if len(daily_for_anomaly) >= 10:
            median_r = daily_for_anomaly.median()
            mad_r = np.median(np.abs(daily_for_anomaly - median_r))
            mad_scaled = mad_r * 1.4826
            if mad_scaled > 0:
                robust_z = (daily_for_anomaly - median_r) / mad_scaled
                for date, z_val in robust_z[np.abs(robust_z) > _MAD_ANOMALY_Z].items():
                    rev = daily_for_anomaly[date]
                    direction = "spike" if rev > median_r else "dip"
                    out["anomalies"].append({
                        "date": str(date),
                        "revenue": rev,
                        "direction": direction,
                        "z_score": round(float(abs(z_val)), 1),
                    })

    # Overall trend (linear slope)
    if n >= 7:
        x = np.arange(n)
        slope, _ = np.polyfit(x, daily.values, 1)
        avg = daily.mean()
        slope_pct = slope / avg * 100 if avg > 0 else 0
        out["slope_pct"] = round(slope_pct, 2)
        out["trend"] = "upward" if slope_pct > 0.5 else ("downward" if slope_pct < -0.5 else "flat")

    return out


def _find_rising_stars(
    df: pd.DataFrame,
    n: int = 5,
    min_revenue: float = 0.0,
    min_units: float = 0.0,
) -> pd.DataFrame | None:
    """Products with the highest revenue momentum over last 30 days vs prior period."""
    if not _has_dates(df):
        return None
    dfc = df.copy()
    dfc["date_only"] = pd.to_datetime(dfc["date"].dt.date)
    max_date = dfc["date_only"].max()
    recent_start = max_date - pd.Timedelta(days=29)
    prior_end = max_date - pd.Timedelta(days=30)
    prior_start = max_date - pd.Timedelta(days=59)
    if dfc["date_only"].min() > prior_start:
        return None
    recent_df = dfc[dfc["date_only"] >= recent_start]
    prior_df = dfc[(dfc["date_only"] >= prior_start) & (dfc["date_only"] <= prior_end)]
    recent = recent_df.groupby("product")["revenue"].sum()
    recent_qty = recent_df.groupby("product")["quantity"].sum()
    older = prior_df.groupby("product")["revenue"].sum()
    both = recent.index.intersection(older.index)
    if both.empty:
        return None
    eligible = both[
        (recent[both] >= min_revenue) &
        (recent_qty.reindex(both, fill_value=0) >= min_units)
    ]
    if eligible.empty:
        return None
    older_vals = older[eligible].values
    if len(older_vals) >= 10:
        older_floor = max(float(np.percentile(older_vals, 10)), 1.0)
    else:
        older_floor = 1.0
    eligible = eligible[older[eligible] >= older_floor]
    if eligible.empty:
        return None
    growth_pct = (recent[eligible] - older[eligible]) / older[eligible].clip(lower=1.0) * 100
    velocity_score = growth_pct * np.log1p(recent[eligible])
    growth = velocity_score.sort_values(ascending=False)

    rising = growth[growth > 0].head(n).reset_index()
    rising.columns = ["product", "velocity_score"]
    rising["growth_pct"] = growth_pct[rising["product"]].values
    rising["recent_rev"] = rising["product"].map(recent).values
    rising["recent_units"] = rising["product"].map(recent_qty).values
    return rising if not rising.empty else None


def _decline_history_insufficient(df: pd.DataFrame) -> bool:
    """True if the dataset spans less than 60 days."""
    if not _has_dates(df):
        return False
    dfc = df.copy()
    dfc["date_only"] = pd.to_datetime(dfc["date"].dt.date)
    max_date = dfc["date_only"].max()
    prior_start = max_date - pd.Timedelta(days=59)
    return bool(dfc["date_only"].min() > prior_start)


def _find_declining_products(df: pd.DataFrame, threshold_pct: float = 20) -> list:
    """Products whose revenue declined by threshold_pct% or more."""
    if not _has_dates(df):
        return []
    dfc = df.copy()
    dfc["date_only"] = pd.to_datetime(dfc["date"].dt.date)
    max_date = dfc["date_only"].max()
    recent_start = max_date - pd.Timedelta(days=29)
    prior_end    = max_date - pd.Timedelta(days=30)
    prior_start  = max_date - pd.Timedelta(days=59)
    if dfc["date_only"].min() > prior_start:
        return []

    recent_df = dfc[dfc["date_only"] >= recent_start]
    prior_df  = dfc[(dfc["date_only"] >= prior_start) & (dfc["date_only"] <= prior_end)]

    MIN_TXN_PER_WINDOW = 5
    recent_counts = recent_df.groupby("product")["revenue"].count()
    prior_counts  = prior_df.groupby("product")["revenue"].count()

    def _dow_normalized_revenue(sub_df: pd.DataFrame) -> pd.Series:
        sub = sub_df.copy()
        sub["dow"] = pd.to_datetime(sub["date"]).dt.dayofweek
        n_days_per_dow = sub.groupby("dow")["date"].apply(lambda x: x.dt.date.nunique())
        prod_dow = sub.groupby(["product", "dow"])["revenue"].sum()
        result = {}
        for product in sub["product"].unique():
            total = 0.0
            for dow in range(7):
                if dow in n_days_per_dow.index:
                    days = n_days_per_dow[dow]
                    rev = prod_dow.get((product, dow), 0.0)
                    total += (rev / max(days, 1)) * 4.3
            result[product] = total
        return pd.Series(result)

    recent = _dow_normalized_revenue(recent_df)
    older  = _dow_normalized_revenue(prior_df)

    older_total  = older.sum()
    recent_total = recent.sum()
    overall_pct  = (recent_total - older_total) / max(older_total, 0.01) * 100

    both = older.index.intersection(recent.index)
    if both.empty:
        return []

    results = []
    for product in both:
        if recent_counts.get(product, 0) < MIN_TXN_PER_WINDOW:
            continue
        if prior_counts.get(product, 0) < MIN_TXN_PER_WINDOW:
            continue
        old_rev = older[product]
        new_rev = recent[product]
        if old_rev <= 0:
            continue
        change_pct = (new_rev - old_rev) / old_rev * 100
        if change_pct > -threshold_pct:
            continue
        severity = abs(change_pct) / max(abs(overall_pct), 5.0)
        if severity < 1.5 and overall_pct < -5:
            seasonality = "possibly_seasonal"
        elif overall_pct >= 0 or severity >= 3.0:
            seasonality = "structural"
        else:
            seasonality = "uncertain"
        results.append({
            "product":     product,
            "decline_pct": round(abs(change_pct), 1),
            "older_rev":   old_rev,
            "recent_rev":  new_rev,
            "seasonality": seasonality,
            "overall_pct": round(overall_pct, 1),
        })

    results.sort(key=lambda x: x["decline_pct"], reverse=True)
    return results


def _compare_periods(df_a: pd.DataFrame, df_b: pd.DataFrame, label_a: str, label_b: str):
    """Compare two period DataFrames and return a structured diff dict."""
    if len(df_a) < 30 or len(df_b) < 30:
        return None

    def _agg(df):
        return (
            df.groupby("product")
            .agg(revenue=("revenue", "sum"), transactions=("revenue", "count"))
            .reset_index()
        )

    agg_a = _agg(df_a)
    agg_b = _agg(df_b)

    rev_a = df_a["revenue"].sum()
    rev_b = df_b["revenue"].sum()
    orders_a = len(df_a)
    orders_b = len(df_b)
    aov_a = rev_a / orders_a if orders_a else 0.0
    aov_b = rev_b / orders_b if orders_b else 0.0

    def _safe_pct(a, b):
        return (b - a) / abs(a) * 100 if a != 0 else 0.0

    merged = pd.merge(
        agg_a[["product", "revenue", "transactions"]],
        agg_b[["product", "revenue", "transactions"]],
        on="product", how="outer", suffixes=("_a", "_b"),
    ).fillna(0)

    both = merged[
        (merged["transactions_a"] >= _MIN_PRODUCT_TXN_FOR_PERIOD) &
        (merged["transactions_b"] >= _MIN_PRODUCT_TXN_FOR_PERIOD)
    ].copy()

    both["delta_pct"] = both.apply(
        lambda r: _safe_pct(r["revenue_a"], r["revenue_b"]), axis=1
    )

    def _to_item(r):
        return {"product": r["product"], "delta_pct": r["delta_pct"], "rev_b": r["revenue_b"]}

    top_risers  = both.nlargest(3, "delta_pct").apply(_to_item, axis=1).tolist()
    top_fallers = both.nsmallest(3, "delta_pct").apply(_to_item, axis=1).tolist()

    products_a = set(agg_a["product"].tolist())
    products_b = set(agg_b["product"].tolist())

    return {
        "revenue_delta_pct":  _safe_pct(rev_a, rev_b),
        "orders_delta_pct":   _safe_pct(orders_a, orders_b),
        "aov_delta_pct":      _safe_pct(aov_a, aov_b),
        "top_risers":         top_risers,
        "top_fallers":        top_fallers,
        "new_products":       sorted(products_b - products_a),
        "dropped_products":   sorted(products_a - products_b),
        "label_a":            label_a,
        "label_b":            label_b,
        "rev_a":              rev_a,
        "rev_b":              rev_b,
    }


def _derive_period_label(df: pd.DataFrame) -> str:
    """Derive a human-readable period label from df's date range."""
    if not _has_dates(df):
        return "Current Period"
    date_min = df["date"].min()
    date_max = df["date"].max()
    if date_min.year == date_max.year and date_min.month == date_max.month:
        return date_min.strftime("%B %Y")
    start_str = _safe_day_format(date_min, "%b %-d", "%b %d")
    if date_min.year == date_max.year:
        return f"{start_str} – {_safe_day_format(date_max, '%b %-d, %Y', '%b %d, %Y')}"
    return f"{start_str}, {date_min.year} – {_safe_day_format(date_max, '%b %-d, %Y', '%b %d, %Y')}"


def _safe_day_format(ts: "pd.Timestamp", fmt_with_day: str, fmt_fallback: str) -> str:
    """Format a timestamp, falling back on Windows where %-d is unsupported."""
    try:
        return ts.strftime(fmt_with_day)
    except ValueError:
        return ts.strftime(fmt_fallback).replace(" 0", " ")
