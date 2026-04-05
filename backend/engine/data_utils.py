"""Utilities for extracting proof data from raw transaction data."""
from __future__ import annotations

from datetime import datetime

import pandas as pd


def get_product_date_range(
    df: pd.DataFrame, product: str, date_col: str = "date"
) -> tuple[str | None, str | None]:
    """Get first and last transaction date for a product as 'YYYY-MM-DD' strings."""
    if date_col not in df.columns:
        return None, None
    product_txns = df[df["product"] == product]
    if product_txns.empty:
        return None, None
    dates = product_txns[date_col].dropna()
    if dates.empty:
        return None, None
    return dates.min().strftime("%Y-%m-%d"), dates.max().strftime("%Y-%m-%d")


def format_date_range(start: str | None, end: str | None) -> str:
    """Format 'YYYY-MM-DD' pair into a human-friendly display string."""
    if not start or not end:
        return "Insufficient data"
    try:
        s = datetime.strptime(start, "%Y-%m-%d")
        e = datetime.strptime(end, "%Y-%m-%d")
        if s.month == e.month and s.year == e.year:
            return f"{s.strftime('%b %d')} – {e.day}"
        if s.year == e.year:
            return f"{s.strftime('%b %d')} – {e.strftime('%b %d')}"
        return f"{s.strftime('%b %d %y')} – {e.strftime('%b %d %y')}"
    except Exception:
        return f"{start} – {end}"


def build_proof(
    *,
    sample_size: int,
    date_start: str | None,
    date_end: str | None,
    metric_name: str,
    metric_value: float | None,
    metric_interpretation: str | None = None,
    confidence_tier: str,
) -> dict:
    """Build a standardised proof dict for a recommendation."""
    display = format_date_range(date_start, date_end)

    if confidence_tier == "high":
        color = "green"
    elif confidence_tier == "moderate":
        color = "amber"
    else:
        color = "red"

    return {
        "sample_size": sample_size,
        "date_range": {
            "start": date_start,
            "end": date_end,
            "display": display,
        },
        "key_metric": {
            "name": metric_name,
            "value": round(metric_value, 3) if metric_value is not None else None,
            "interpretation": metric_interpretation,
        },
        "confidence": {
            "tier": confidence_tier,
            "color": color,
        },
    }
