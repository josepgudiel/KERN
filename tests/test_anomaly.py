"""Tests for backend.engine.anomaly — detect_anomalies (MAD-based).

MAD (Median Absolute Deviation) is robust to extreme outliers because the
median is not distorted by a single huge value, unlike the mean used in
Z-score.  These tests verify both detection power and false-positive control.

Thresholds (from backend.engine.safety):
  _MAD_ANOMALY_Z        = 2.5   (modified Z-score threshold)
  _MIN_TXN_PER_DAY_FOR_ANOMALY = 3  (daily transaction floor for a day to count)
  minimum qualifying days = 10
  minimum calendar span   = 14 days
"""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from backend.engine.anomaly import detect_anomalies


# ─── Helpers ────────────────────────────────────────────────────────────────

_START = "2025-01-01"
_TXN_PER_DAY = 4          # comfortably above the 3-transaction floor
_NORMAL_REVENUE = 75.0    # per-day total; each transaction carries 75/4 = ~18.75


def _make_anomaly_df(
    n_normal_days: int = 35,
    outlier_indices: list[int] | None = None,
    outlier_multiplier: float = 10.0,
) -> pd.DataFrame:
    """Build a daily sales DataFrame for anomaly-detection tests.

    Parameters
    ----------
    n_normal_days:
        Total number of days in the series (all normal unless overridden).
    outlier_indices:
        Day indices (0-based) that should have inflated revenue.
    outlier_multiplier:
        How many times the normal revenue the outlier days should carry.
    """
    if outlier_indices is None:
        outlier_indices = []

    np.random.seed(55)
    baseline = 100
    variance = 20
    revenue = np.random.normal(baseline, variance, n_normal_days).clip(min=10)

    dates = pd.date_range(_START, periods=n_normal_days, freq="D")
    rows: list[dict] = []
    for i, d in enumerate(dates):
        multiplier = outlier_multiplier if i in outlier_indices else 1.0
        per_txn = revenue[i] * multiplier / _TXN_PER_DAY
        for j in range(_TXN_PER_DAY):
            rows.append({
                "date": d,
                "product": f"Product_{j % 3}",
                "revenue": per_txn,
            })
    return pd.DataFrame(rows)


def _anomaly_dates(anomalies: list[dict]) -> set[str]:
    """Return the set of flagged date strings from detect_anomalies output."""
    return {a["date"] for a in anomalies}


# ─── Normal-path: clear outlier detection ───────────────────────────────────


@pytest.mark.parametrize("multiplier", [5.0, 10.0, 50.0])
def test_clear_spike_is_flagged(multiplier: float) -> None:
    """A single revenue spike of N× normal must be detected as an anomaly.

    MAD is robust to extreme outliers: a spike that would inflate the mean
    (breaking Z-score) does NOT shift the median, so MAD-based detection
    remains reliable at all multiplier levels.
    """
    outlier_idx = 17  # mid-series; away from any warm-up boundary
    df = _make_anomaly_df(n_normal_days=35, outlier_indices=[outlier_idx], outlier_multiplier=multiplier)

    anomalies = detect_anomalies(df)
    flagged = _anomaly_dates(anomalies)

    expected_date = str(pd.Timestamp(_START) + pd.Timedelta(days=outlier_idx))[:10]
    assert expected_date in flagged, (
        f"Spike at {multiplier}× normal on {expected_date} was not flagged. "
        f"Flagged dates: {flagged}"
    )


def test_spike_direction_is_correct() -> None:
    """A positive outlier must have direction='spike', not 'dip'."""
    df = _make_anomaly_df(n_normal_days=35, outlier_indices=[20], outlier_multiplier=10.0)
    anomalies = detect_anomalies(df)

    spike_date = str(pd.Timestamp(_START) + pd.Timedelta(days=20))[:10]
    matching = [a for a in anomalies if a["date"] == spike_date]

    assert matching, f"Expected spike on {spike_date} not found in anomalies."
    assert matching[0]["direction"] == "spike"


def test_multiple_outliers_all_flagged() -> None:
    """When three outlier days are injected, all three should appear in results."""
    outlier_indices = [10, 20, 30]
    df = _make_anomaly_df(n_normal_days=35, outlier_indices=outlier_indices, outlier_multiplier=10.0)

    anomalies = detect_anomalies(df)
    flagged = _anomaly_dates(anomalies)

    for idx in outlier_indices:
        expected = str(pd.Timestamp(_START) + pd.Timedelta(days=idx))[:10]
        assert expected in flagged, f"Outlier on day {idx} ({expected}) was not flagged."


def test_anomaly_dict_has_required_keys() -> None:
    """Each anomaly record must carry all expected fields."""
    required_keys = {"date", "date_label", "direction", "revenue", "z_score", "pct_above", "top_product", "auto_label"}
    df = _make_anomaly_df(n_normal_days=35, outlier_indices=[15], outlier_multiplier=10.0)

    anomalies = detect_anomalies(df)
    assert anomalies, "Expected at least one anomaly but got none."

    for rec in anomalies:
        missing = required_keys - rec.keys()
        assert not missing, f"Anomaly record missing keys: {missing}"


def test_z_score_is_positive_float() -> None:
    """z_score values must be positive finite numbers."""
    df = _make_anomaly_df(n_normal_days=35, outlier_indices=[15], outlier_multiplier=10.0)
    anomalies = detect_anomalies(df)

    for rec in anomalies:
        assert rec["z_score"] > 0
        assert isinstance(rec["z_score"], float)


# ─── False-positive control ──────────────────────────────────────────────────


def test_no_outliers_returns_empty_or_few_anomalies() -> None:
    """Uniform normal data should produce no anomalies (or very few false positives)."""
    # Perfectly flat revenue — no genuine outliers exist
    df = _make_anomaly_df(n_normal_days=35)
    anomalies = detect_anomalies(df)

    # MAD of a constant series is 0, so global_mad_scaled == 0 → returns [] (guard in source)
    # For near-constant series, false-positive rate should be very low
    assert len(anomalies) == 0, (
        f"Expected 0 anomalies in flat data but got {len(anomalies)}: "
        f"{[a['date'] for a in anomalies]}"
    )


# ─── Guard-rail / minimum-data tests ────────────────────────────────────────


def test_fewer_than_14_days_returns_empty_list() -> None:
    """detect_anomalies requires ≥ 14 calendar days; shorter series → empty list."""
    df = _make_anomaly_df(n_normal_days=10)
    assert detect_anomalies(df) == []


def test_non_datetime_date_column_returns_empty_list() -> None:
    """String-typed date column fails _has_dates check → empty list."""
    df = _make_anomaly_df(n_normal_days=35)
    df["date"] = df["date"].astype(str)
    assert detect_anomalies(df) == []


def test_empty_dataframe_returns_empty_list() -> None:
    """An empty DataFrame has no dates; should return [] not raise."""
    df = pd.DataFrame(columns=["date", "product", "revenue"])
    df["date"] = pd.to_datetime(df["date"])
    assert detect_anomalies(df) == []


# ─── MAD robustness vs Z-score note ─────────────────────────────────────────


def test_mad_robustness_against_extreme_outlier() -> None:
    """MAD is robust to extreme outliers that would distort Z-score.

    A single 50× spike would massively inflate the mean and std, making
    Z-score unreliable for the rest of the series.  MAD uses the median,
    which is unaffected, so only the true outlier is flagged.
    """
    outlier_idx = 20
    extreme_multiplier = 50.0
    df = _make_anomaly_df(
        n_normal_days=35,
        outlier_indices=[outlier_idx],
        outlier_multiplier=extreme_multiplier,
    )

    anomalies = detect_anomalies(df)
    flagged = _anomaly_dates(anomalies)

    expected = str(pd.Timestamp(_START) + pd.Timedelta(days=outlier_idx))[:10]
    # MAD detects the outlier …
    assert expected in flagged, "50× spike was not flagged — MAD robustness test failed."
    # … and does not flag the entire normal portion of the series as anomalous
    normal_flagged = [d for d in flagged if d != expected]
    assert len(normal_flagged) == 0, (
        f"MAD incorrectly flagged normal days: {normal_flagged}. "
        "Z-score would inflate std and might do the same — MAD should not."
    )
