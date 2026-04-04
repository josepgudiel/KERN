"""Safety thresholds, confidence helpers, and recommendation quality gates."""
from __future__ import annotations

import pandas as pd

# ─── Centralized thresholds ──────────────────────────────────────────────────
_MIN_TXN_FOR_TREND    = 14   # minimum daily observations needed for trend insights
_MIN_TXN_FOR_CLUSTER  = 20   # minimum total transactions before clustering is reported
_MIN_TXN_FOR_PRICING  = 10   # minimum per-product transactions for any pricing signal
_MIN_TXN_FOR_ANOMALY  = 14   # minimum days of daily revenue for anomaly detection
_MIN_DATE_SPAN_DAYS   = 14   # minimum calendar span for time-based analyses

# Percentile split for demand/price tier classification in pricing recommendations.
_QUANTILE_LOW        = 0.35
_QUANTILE_HIGH       = 0.65

# MAD-based anomaly detection threshold.
_MAD_ANOMALY_Z       = 2.5

# Fallback price-elasticity when no product-level OLS estimate is available.
_DEFAULT_ELASTICITY  = 0.65

# Minimum transactions per product in each period for period-comparison noise filtering.
_MIN_PRODUCT_TXN_FOR_PERIOD = 3


def _has_dates(df: pd.DataFrame) -> bool:
    """True if the date column is datetime-typed AND has at least one non-null value."""
    return pd.api.types.is_datetime64_any_dtype(df["date"]) and df["date"].notna().any()


def _build_data_confidence_badge(df: pd.DataFrame) -> str:
    """Return a short plain-English data quality statement."""
    n_rows = len(df)
    if n_rows == 0:
        return "*Based on 0 transactions*"

    has_dates = _has_dates(df)

    if has_dates:
        span_days = (df["date"].max() - df["date"].min()).days
        weeks = round(span_days / 7)
        if weeks < 1:
            time_part = f"{span_days} day{'s' if span_days != 1 else ''} of data"
        elif weeks < 8:
            time_part = f"{weeks} week{'s' if weeks != 1 else ''} of data"
        else:
            months = round(span_days / 30)
            time_part = f"{months} month{'s' if months != 1 else ''} of data"
    else:
        time_part = "snapshot data (no dates)"

    n_products = df["product"].nunique()

    return (
        f"*Based on {n_rows:,} transactions · {n_products} products · {time_part}*"
    )


def _confidence_label(n: int) -> str:
    """Return a data quality indicator based on transaction count."""
    if n < 15:
        level = "Need more data"
    elif n < 100:
        level = "Worth testing"
    else:
        level = "Strong signal — act on this"
    return f"Based on your last {n:,} sales — {level}"


def _confidence_tier(tier: str) -> tuple:
    """Return (label, emoji) for a signal confidence tier."""
    return {
        "high":         ("Strong signal — act on this", "🟢"),
        "directional":  ("Worth testing",               "🟡"),
        "insufficient": ("Need more data",              "🔴"),
    }.get(tier, ("Worth testing", "🟡"))


def _recommendation_safety_check(df: pd.DataFrame) -> dict:
    """Evaluate dataset quality and return safety flags for each analysis module."""
    n_txn = len(df)
    has_dates = _has_dates(df)
    n_days = df["date"].dt.date.nunique() if has_dates else 0
    date_span = (df["date"].max() - df["date"].min()).days if has_dates and n_txn > 0 else 0
    n_products = df["product"].nunique()
    has_variance = df.groupby("product")["revenue"].std().fillna(0).gt(0).any()

    checks = {
        "trend": (
            has_dates and n_days >= _MIN_TXN_FOR_TREND and date_span >= _MIN_DATE_SPAN_DAYS,
            f"need {_MIN_TXN_FOR_TREND}+ days of data (have {n_days})" if not has_dates or n_days < _MIN_TXN_FOR_TREND
            else f"need {_MIN_DATE_SPAN_DAYS}+ day span (have {date_span})"
        ),
        "anomaly": (
            has_dates and n_days >= _MIN_TXN_FOR_ANOMALY,
            f"need {_MIN_TXN_FOR_ANOMALY}+ daily observations (have {n_days})"
        ),
        "clustering": (
            n_products >= 4 and n_txn >= _MIN_TXN_FOR_CLUSTER,
            f"need 4+ products and {_MIN_TXN_FOR_CLUSTER}+ transactions"
        ),
        "pricing": (
            n_txn >= _MIN_TXN_FOR_PRICING and has_variance,
            "need price variation and sufficient transaction volume per product"
        ),
        "basket": (
            has_dates and n_txn >= 50,
            "need dates and 50+ transactions for basket analysis"
        ),
    }
    return checks
