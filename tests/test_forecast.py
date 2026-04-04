"""Tests for backend.engine.forecast — compute_revenue_forecast."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backend.engine.forecast import compute_revenue_forecast


# ─── Helpers ────────────────────────────────────────────────────────────────


def _make_df(n_days: int = 35, daily_revenue: float = 100.0, constant: bool = False) -> pd.DataFrame:
    """Build a minimal sales DataFrame suitable for forecast tests.

    Two products per day so the function's product-grouping code is exercised.
    Revenue is either a gentle upward slope (default) or flat (constant=True).
    """
    dates = pd.date_range("2025-01-01", periods=n_days, freq="D")
    rows = []
    for i, d in enumerate(dates):
        trend = 0 if constant else i * 0.5
        rows.append({"date": d, "product": "Widget A", "revenue": daily_revenue * 0.6 + trend})
        rows.append({"date": d, "product": "Widget B", "revenue": daily_revenue * 0.4 + trend})
    return pd.DataFrame(rows)


# ─── Normal-path tests ──────────────────────────────────────────────────────


@pytest.mark.parametrize("forecast_weeks", [1, 2, 4])
def test_returns_correct_number_of_forecast_points(forecast_weeks: int) -> None:
    """forecast_points should contain exactly forecast_weeks * 7 entries."""
    df = _make_df(n_days=35)
    result = compute_revenue_forecast(df, forecast_weeks=forecast_weeks)

    assert "error" not in result, f"Unexpected error: {result.get('error')}"
    assert "forecast_points" in result

    points = result["forecast_points"]
    assert len(points) == forecast_weeks * 7


def test_forecast_point_structure() -> None:
    """Each forecast point must carry date, predicted, lower, upper keys."""
    df = _make_df(n_days=35)
    result = compute_revenue_forecast(df, forecast_weeks=1)

    for point in result["forecast_points"]:
        assert "date" in point
        assert "predicted" in point
        assert "lower" in point
        assert "upper" in point


def test_forecast_values_are_numeric_and_non_negative() -> None:
    """Predicted values must be finite and non-negative (clipped at 0 in source)."""
    df = _make_df(n_days=35)
    result = compute_revenue_forecast(df, forecast_weeks=2)

    for point in result["forecast_points"]:
        assert np.isfinite(point["predicted"])
        assert point["predicted"] >= 0
        assert point["lower"] >= 0
        assert point["upper"] >= point["lower"]


def test_trend_key_present_and_valid() -> None:
    """Result must include a trend field with a recognised value."""
    df = _make_df(n_days=35)
    result = compute_revenue_forecast(df)

    assert result.get("trend") in {"upward", "downward", "flat"}


def test_constant_revenue_returns_flat_or_stable_trend() -> None:
    """With perfectly flat revenue the model should report a flat or near-zero slope."""
    df = _make_df(n_days=35, daily_revenue=100.0, constant=True)
    result = compute_revenue_forecast(df, forecast_weeks=1)

    assert "error" not in result
    # All predicted values should be close to the historical average
    avg = result["avg_daily"]
    for point in result["forecast_points"]:
        assert abs(point["predicted"] - avg) < avg * 0.5, (
            f"Predicted {point['predicted']} is too far from avg {avg}"
        )


# ─── Edge-case / guard-rail tests ───────────────────────────────────────────


def test_insufficient_data_returns_error_key() -> None:
    """Fewer than 28 days of history must return an insufficient_data status."""
    df = _make_df(n_days=5)
    result = compute_revenue_forecast(df, forecast_weeks=1)

    assert result.get("status") == "insufficient_data" or result.get("error") == "insufficient_data"


def test_single_row_returns_insufficient_data() -> None:
    """A single-row DataFrame should not crash and must signal insufficient data."""
    df = _make_df(n_days=1)
    result = compute_revenue_forecast(df)

    assert "error" in result or result.get("status") == "insufficient_data"


def test_empty_dataframe_returns_no_dates_error() -> None:
    """An empty DataFrame (no rows) has no valid dates — expect no_dates error."""
    df = pd.DataFrame(columns=["date", "product", "revenue"])
    # Ensure the date column is datetime-typed even when empty
    df["date"] = pd.to_datetime(df["date"])
    result = compute_revenue_forecast(df)

    assert "error" in result


def test_non_datetime_date_column_returns_error() -> None:
    """If the date column is a plain string rather than datetime64, expect no_dates."""
    df = _make_df(n_days=35)
    df["date"] = df["date"].astype(str)  # strip datetime dtype
    result = compute_revenue_forecast(df)

    assert result.get("error") == "no_dates"
