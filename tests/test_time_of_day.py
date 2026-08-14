"""Time-of-day ingestion: separate Date + Time columns must survive into `hour`.

The bug this file exists to prevent: `_detect_columns` called `_find_col` once
for DATE_SYNONYMS and returned the first hit, so a Square/Toast/Clover export
shaped `Date, Time, Time Zone, ...` matched `Date` and silently discarded the
clock time. There was no hour-of-day signal anywhere in the pipeline for the
most common POS export shape.

Two traps are covered explicitly because a naive fix walks into both:

  * `_find_col` matches substrings bidirectionally, so "time" also matches
    "Time Zone", "Prep Time", "Lead Time" — the first is guarded by name, the
    duration columns by inspecting what the values look like.
  * A date-only column parses to hour 0 for every row, which is non-null but
    carries no signal. `hour` must be NA there, which makes the combined-column
    case a column-level judgement rather than a per-row one.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backend.engine.data_loader import _detect_columns, prepare_data
from backend.engine.demo import _generate_demo_df, _generate_retail_demo_df
from backend.engine.safety import _has_dates, _has_hour_data


# ─── Fixtures ────────────────────────────────────────────────────────────────

def _square_shape(df: pd.DataFrame) -> pd.DataFrame:
    """Re-shape a demo frame into a Square-style export: Date + Time + Time Zone.

    Derived from the demo generator rather than hand-written so the expected
    hour distribution is known-correct ground truth we can round-trip against.
    """
    out = pd.DataFrame({
        "Date":      df["date"].dt.strftime("%Y-%m-%d"),
        "Time":      df["date"].dt.strftime("%I:%M:%S %p"),
        "Time Zone": "Eastern Time (US & Canada)",
        "Category":  "Food & Drink",
        "Item":      df["product"],
        "Qty":       df["quantity"],
        "Gross Sales": df["revenue"],
    })
    return out


@pytest.fixture(scope="module")
def coffee_demo() -> pd.DataFrame:
    return _generate_demo_df()


# ─── 1. Separate Date + Time columns ─────────────────────────────────────────

def test_separate_date_and_time_columns_populate_hour(coffee_demo):
    """A Square-shaped export recovers the exact hours it was built from."""
    raw = _square_shape(coffee_demo)

    mapping = _detect_columns(raw)
    assert mapping["date"] == "Date"
    assert mapping["time_of_day"] == "Time"

    df, _ = prepare_data(raw)
    assert df is not None
    assert _has_hour_data(df)
    assert df["hour"].notna().all()
    assert df["hour"].between(0, 23).all()

    # Round-trip: the recovered hour histogram matches the generator's own.
    expected = coffee_demo["date"].dt.hour.value_counts().sort_index()
    actual = df["hour"].astype(int).value_counts().sort_index()
    pd.testing.assert_series_equal(
        expected, actual, check_names=False, check_index_type=False, check_dtype=False
    )


def test_separate_time_column_merges_into_the_date_timestamp(coffee_demo):
    """The merged time lands on `date` itself, not only in `hour`."""
    raw = _square_shape(coffee_demo)
    df, _ = prepare_data(raw)

    assert (df["date"].dt.hour == df["hour"]).all()
    assert df["date"].dt.hour.nunique() > 2


def test_retail_demo_also_survives_the_split(  ):
    """Second demo dataset, same round-trip — 9am-8pm retail hours."""
    retail = _generate_retail_demo_df()
    df, _ = prepare_data(_square_shape(retail))

    assert _has_hour_data(df)
    expected = set(retail["date"].dt.hour.unique())
    assert set(df["hour"].dropna().astype(int).unique()) == expected


# ─── 2. Time Zone must never be the time source ──────────────────────────────

def test_time_zone_is_never_selected_as_time_of_day(coffee_demo):
    """Same export shape minus the literal Time column: no false positive."""
    raw = _square_shape(coffee_demo).drop(columns=["Time"])

    mapping = _detect_columns(raw)
    assert mapping["date"] == "Date"
    assert mapping["time_of_day"] is None

    df, _ = prepare_data(raw)
    assert df is not None
    assert not _has_hour_data(df)
    assert df["hour"].isna().all()


@pytest.mark.parametrize("col_name", ["Prep Time", "Lead Time", "Time to Ready"])
def test_duration_columns_are_rejected_as_time_of_day(coffee_demo, col_name):
    """Name matching alone would grab these; their values are not clock times."""
    raw = _square_shape(coffee_demo).drop(columns=["Time"])
    raw[col_name] = np.resize([4, 12, 7, 3], len(raw))

    mapping = _detect_columns(raw)
    assert mapping["time_of_day"] is None

    df, _ = prepare_data(raw)
    assert not _has_hour_data(df)


# ─── 3. Single combined datetime column keeps working ────────────────────────

def test_combined_datetime_column_needs_no_separate_time_column(coffee_demo):
    """The already-working path: one Timestamp column carrying real times."""
    raw = pd.DataFrame({
        "Timestamp": coffee_demo["date"],
        "Item":      coffee_demo["product"],
        "Qty":       coffee_demo["quantity"],
        "Total":     coffee_demo["revenue"],
    })

    mapping = _detect_columns(raw)
    assert mapping["time_of_day"] is None

    df, _ = prepare_data(raw)
    assert _has_hour_data(df)
    assert (df["hour"] == df["date"].dt.hour).all()


def test_demo_datasets_pass_through_prepare_data_with_hours(coffee_demo):
    """Both demo generators feed prepare_data directly in main.py."""
    for demo in (coffee_demo, _generate_retail_demo_df()):
        df, _ = prepare_data(demo)
        assert _has_hour_data(df)
        assert df["hour"].notna().all()


def test_genuine_midnight_sales_keep_their_hour():
    """A late-operating venue must not lose its 00:xx daypart.

    This is the reason the combined-column rule is column-level: nulling every
    exact-midnight row individually would delete the midnight hour for exactly
    the businesses that trade in it.
    """
    base = pd.Timestamp("2024-03-01")
    stamps = [base + pd.Timedelta(days=d, hours=h)
              for d in range(20) for h in (0, 19, 21, 23)]
    raw = pd.DataFrame({
        "Timestamp": stamps,
        "Item":      "late night burger",
        "Total":     12.0,
    })

    df, _ = prepare_data(raw)
    assert _has_hour_data(df)
    assert (df["hour"] == 0).sum() == 20
    assert df["hour"].notna().all()


# ─── 4. Date-only files must not regress ─────────────────────────────────────

def test_date_only_file_reports_no_hour_data(coffee_demo):
    """The common retail-export case: no time signal anywhere."""
    raw = pd.DataFrame({
        "Date":    coffee_demo["date"].dt.strftime("%Y-%m-%d"),
        "Product": coffee_demo["product"],
        "Revenue": coffee_demo["revenue"],
    })

    df, _ = prepare_data(raw)
    assert _has_dates(df)
    assert not _has_hour_data(df)
    assert df["hour"].isna().all()


def test_date_only_parsing_behavior_is_unchanged(coffee_demo):
    """Row count, dates, and warnings for a date-only file are untouched."""
    raw = pd.DataFrame({
        "Date":    coffee_demo["date"].dt.strftime("%Y-%m-%d"),
        "Product": coffee_demo["product"],
        "Revenue": coffee_demo["revenue"],
    })

    df, warning = prepare_data(raw)
    assert warning is None
    assert len(df) == len(coffee_demo)
    assert (df["date"] == coffee_demo["date"].dt.normalize()).all()


def test_no_date_column_at_all_is_hour_free():
    """Snapshot data with no dates: hour exists as a column but is all NA."""
    raw = pd.DataFrame({
        "Product": ["latte", "mocha", "drip"],
        "Revenue": [5.5, 6.0, 2.4],
    })

    df, _ = prepare_data(raw)
    assert not _has_dates(df)
    assert not _has_hour_data(df)
    assert "hour" in df.columns
    assert df["hour"].isna().all()


# ─── 5. Partial / malformed time values ──────────────────────────────────────

def test_unparseable_times_null_only_their_own_rows():
    """Garbage in a few cells must not cost the column, or drop the rows."""
    raw = pd.DataFrame({
        "Date":  ["2024-03-01"] * 6,
        "Time":  ["08:15 AM", "garbage", "", "13:45", "9:05 PM", None],
        "Item":  ["latte", "mocha", "drip", "scone", "bagel", "tea"],
        "Total": [5.5, 6.0, 2.4, 3.5, 5.0, 3.0],
    })

    mapping = _detect_columns(raw)
    assert mapping["time_of_day"] == "Time"

    df, _ = prepare_data(raw)
    assert len(df) == 6                       # nothing dropped
    assert df["hour"].notna().sum() == 3      # only the parseable ones
    assert sorted(df["hour"].dropna().astype(int)) == [8, 13, 21]

    # Rows without a time keep their date-only value rather than being lost.
    no_time = df[df["hour"].isna()]
    assert (no_time["date"] == pd.Timestamp("2024-03-01")).all()


def test_mixed_clock_formats_all_parse():
    """12h, 24h, with and without seconds, with and without a leading zero."""
    raw = pd.DataFrame({
        "Date":  ["2024-03-01"] * 4,
        "Time":  ["08:15:32 AM", "20:15", "8:15 AM", "11:59 PM"],
        "Item":  ["a", "b", "c", "d"],
        "Total": [1.0, 2.0, 3.0, 4.0],
    })

    df, _ = prepare_data(raw)
    assert sorted(df["hour"].astype(int)) == [8, 8, 20, 23]


# ─── 6. Coverage threshold, not mere existence ───────────────────────────────

def test_sub_threshold_time_coverage_reports_no_hour_data():
    """40% coverage from a separate time column is not daypart coverage."""
    n = 100
    times = ["08:15 AM"] * 40 + [""] * 60
    raw = pd.DataFrame({
        "Date":  ["2024-03-01"] * n,
        "Time":  times,
        "Item":  ["latte"] * n,
        "Total": [5.5] * n,
    })

    df, _ = prepare_data(raw)
    assert df["hour"].notna().sum() == 40      # the real values are kept
    assert not _has_hour_data(df)              # but coverage is insufficient


def test_at_threshold_time_coverage_reports_hour_data():
    """Exactly 50% clears the bar — the threshold is inclusive."""
    n = 100
    raw = pd.DataFrame({
        "Date":  ["2024-03-01"] * n,
        "Time":  ["08:15 AM"] * 50 + [""] * 50,
        "Item":  ["latte"] * n,
        "Total": [5.5] * n,
    })

    df, _ = prepare_data(raw)
    assert _has_hour_data(df)


def test_stray_times_in_a_combined_column_do_not_claim_coverage():
    """Mostly-midnight datetime column: a few stray times are not a daypart."""
    stamps = [pd.Timestamp("2024-03-01") + pd.Timedelta(days=i) for i in range(90)]
    stamps += [pd.Timestamp("2024-06-01") + pd.Timedelta(days=i, hours=14) for i in range(10)]
    raw = pd.DataFrame({
        "Timestamp": stamps,
        "Item":      ["latte"] * 100,
        "Total":     [5.5] * 100,
    })

    df, _ = prepare_data(raw)
    assert not _has_hour_data(df)
    assert df["hour"].isna().all()


# ─── 7. Storage round-trip ───────────────────────────────────────────────────

def test_hour_column_survives_session_serialization(coffee_demo):
    """Sessions round-trip through Parquet; the nullable Int64 must survive."""
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
    from session_utils import deserialize_session, serialize_session

    raw = _square_shape(coffee_demo.head(200))
    df, _ = prepare_data(raw)
    df.loc[df.index[:5], "hour"] = pd.NA      # force NA into the column

    restored = deserialize_session(serialize_session({"df": df}))["df"]
    assert str(restored["hour"].dtype) == "Int64"
    assert _has_hour_data(restored)
    pd.testing.assert_series_equal(df["hour"], restored["hour"])


def test_has_hour_data_is_false_for_legacy_sessions_without_the_column(coffee_demo):
    """Sessions stored before this change have no hour column at all."""
    df, _ = prepare_data(coffee_demo)
    legacy = df.drop(columns=["hour"])
    assert not _has_hour_data(legacy)
