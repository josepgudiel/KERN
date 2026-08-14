"""Margin resolution — real cost data must beat the 0.65 guess.

The bug this file exists to prevent: gross margin was resolved in four
disconnected places. `/upload` detected cost data and ignored it, `/demo` never
detected it at all (so every demo session silently used the 0.65 fallback even
though both demo datasets carry real per-product costs), and `action_center.py`
kept its own unrelated 0.65 literal.

A fourth defect made the first two unfixable on their own: `has_cost_data` was
derived by scanning the *prepared* frame's column names for "cost", but
`prepare_data` always creates a `cost` column (NaN-filled when nothing was
detected). The scan therefore matched every dataset ever uploaded, so
`has_cost_data` was unconditionally True and `cost_column_name` was
unconditionally "cost". `test_no_cost_column_*` are the regression tests for
that; they fail against the old column-name scan.
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import pytest

from backend.engine.data_loader import prepare_data
from backend.engine.demo import _generate_demo_df, _generate_retail_demo_df
from backend.engine.margin import (
    DEFAULT_ESTIMATED_MARGIN,
    MARGIN_MAX,
    MARGIN_MIN,
    MIN_COST_COVERAGE_FOR_MARGIN,
    resolve_margin,
)


# ─── Helpers ────────────────────────────────────────────────────────────────

def _prepared(raw_df: pd.DataFrame) -> pd.DataFrame:
    """Run a raw frame through the real loader, as both endpoints do."""
    df, err = prepare_data(raw_df)
    assert df is not None, f"prepare_data rejected the fixture: {err}"
    return df


def _synthetic_raw(
    n: int = 40,
    revenue: float = 100.0,
    cost: float | None = 40.0,
    cost_coverage: float = 1.0,
    include_cost_col: bool = True,
) -> pd.DataFrame:
    """Build a minimal well-formed sales file.

    Args:
        cost_coverage: Fraction of rows that carry a non-null cost. Rows are
            uniform in revenue, so this is also the revenue-weighted coverage.
        include_cost_col: When False, no cost column exists at all — the
            "genuinely no cost data" case.
    """
    dates = pd.date_range("2026-01-01", periods=n, freq="D")
    raw = pd.DataFrame({
        "order_id": [f"o{i}" for i in range(n)],
        "product": ["Widget", "Gadget"] * (n // 2),
        "quantity": [1] * n,
        "unit_price": [revenue] * n,
        "revenue": [revenue] * n,
        "date": dates,
    })
    if include_cost_col:
        costs: list[float | None] = [cost] * n
        n_null = n - int(round(n * cost_coverage))
        for i in range(n_null):
            costs[i] = None
        raw["cost"] = costs
    return raw


# ─── Precedence step 2: calculated from real cost data ──────────────────────

@pytest.mark.parametrize(
    "generator, expected_margin, label",
    [
        (_generate_demo_df, 0.6454, "coffee"),
        (_generate_retail_demo_df, 0.5366, "retail"),
    ],
)
def test_demo_datasets_resolve_to_calculated(generator, expected_margin, label):
    """Both demo datasets carry real cost data and must use it, not the guess.

    Expected values are derived by hand from the cost_pct columns in
    engine/demo.py. Coffee lands within half a point of the 0.65 fallback —
    that is a property of the fixture, not evidence the calculation was skipped,
    which is why margin_source is asserted separately from the value.
    """
    raw = generator()
    df = _prepared(raw)

    gross_margin, source, has_cost, cost_col = resolve_margin(df, raw)

    assert source == "calculated", f"{label} should calculate from its cost data"
    assert has_cost is True
    assert cost_col == "cost"
    assert gross_margin == pytest.approx(expected_margin, abs=1e-3)


def test_retail_margin_actually_differs_from_the_old_guess():
    """The retail dataset is where this fix changes real output.

    Guards against a regression that silently reverts to 0.65: coffee alone
    would not catch it, since its true margin is ~0.645.
    """
    raw = _generate_retail_demo_df()
    gross_margin, source, _, _ = resolve_margin(_prepared(raw), raw)

    assert source == "calculated"
    assert abs(gross_margin - DEFAULT_ESTIMATED_MARGIN) > 0.10


def test_calculated_margin_matches_manual_computation():
    """Independent recomputation over cost-non-null rows only."""
    raw = _synthetic_raw(n=40, revenue=100.0, cost=25.0)
    df = _prepared(raw)

    gross_margin, source, _, _ = resolve_margin(df, raw)

    cost_rows = df[df["cost"].notna()]
    expected = 1 - (cost_rows["cost"].sum() / cost_rows["revenue"].sum())
    assert source == "calculated"
    assert gross_margin == pytest.approx(expected)
    assert gross_margin == pytest.approx(0.75)


# ─── Precedence step 1: explicit margin wins ────────────────────────────────

def test_explicit_margin_beats_real_cost_data():
    """An owner-entered margin outranks anything derivable from the file."""
    raw = _generate_demo_df()
    df = _prepared(raw)

    gross_margin, source, has_cost, cost_col = resolve_margin(df, raw, explicit_margin=0.42)

    assert source == "provided"
    assert gross_margin == pytest.approx(0.42)
    # Cost data is still reported even though it lost the precedence contest.
    assert has_cost is True
    assert cost_col == "cost"


@pytest.mark.parametrize("bad_margin", [0.0, 0.04, 0.995, 1.0, 1.5, -0.2])
def test_out_of_range_explicit_margin_raises(bad_margin):
    """Rejected at the boundary — the HTTP layer turns this into a 400."""
    raw = _synthetic_raw()
    with pytest.raises(ValueError, match="Margin must be between"):
        resolve_margin(_prepared(raw), raw, explicit_margin=bad_margin)


@pytest.mark.parametrize("ok_margin", [MARGIN_MIN, 0.5, MARGIN_MAX])
def test_in_range_explicit_margin_accepted(ok_margin):
    raw = _synthetic_raw()
    gross_margin, source, _, _ = resolve_margin(_prepared(raw), raw, explicit_margin=ok_margin)
    assert source == "provided"
    assert gross_margin == pytest.approx(ok_margin)


# ─── Precedence step 3: fallback paths ──────────────────────────────────────

def test_insufficient_coverage_falls_through_to_estimated(caplog):
    """Cost on 30% of revenue is not a portfolio margin — don't pretend it is."""
    raw = _synthetic_raw(n=40, revenue=100.0, cost=10.0, cost_coverage=0.3)
    df = _prepared(raw)

    coverage = df[df["cost"].notna()]["revenue"].sum() / df["revenue"].sum()
    assert coverage < MIN_COST_COVERAGE_FOR_MARGIN, "fixture must under-cover"

    with caplog.at_level(logging.INFO, logger="backend.engine.margin"):
        gross_margin, source, has_cost, _ = resolve_margin(df, raw)

    assert source == "estimated"
    assert gross_margin == pytest.approx(DEFAULT_ESTIMATED_MARGIN)
    # Distinguishable from "no cost column at all".
    assert has_cost is True
    assert "covers only" in caplog.text


def test_coverage_at_threshold_is_trusted():
    """>= 50% passes — the boundary is inclusive."""
    raw = _synthetic_raw(n=40, revenue=100.0, cost=40.0, cost_coverage=0.5)
    df = _prepared(raw)

    coverage = df[df["cost"].notna()]["revenue"].sum() / df["revenue"].sum()
    assert coverage == pytest.approx(MIN_COST_COVERAGE_FOR_MARGIN)

    _, source, _, _ = resolve_margin(df, raw)
    assert source == "calculated"


def test_out_of_range_computed_margin_falls_through_with_value_logged(caplog):
    """Cost > revenue (refunds, discounts, a misdetected column) → negative margin.

    Must fall through rather than clip to 0.05, and must log the computed value
    so a real customer file is debuggable after the fact.
    """
    raw = _synthetic_raw(n=40, revenue=100.0, cost=150.0)
    df = _prepared(raw)

    with caplog.at_level(logging.WARNING, logger="backend.engine.margin"):
        gross_margin, source, has_cost, _ = resolve_margin(df, raw)

    assert source == "estimated"
    assert gross_margin == pytest.approx(DEFAULT_ESTIMATED_MARGIN)
    assert has_cost is True
    # Not silently clamped to the bound.
    assert gross_margin != pytest.approx(MARGIN_MIN)
    assert "outside" in caplog.text
    assert "-0.5000" in caplog.text, "the computed value itself must be in the log line"


def test_near_zero_cost_margin_above_max_falls_through(caplog):
    """The upper bound is enforced too — a ~0 cost column reads as 100% margin."""
    raw = _synthetic_raw(n=40, revenue=100.0, cost=0.5)
    df = _prepared(raw)

    with caplog.at_level(logging.WARNING, logger="backend.engine.margin"):
        gross_margin, source, _, _ = resolve_margin(df, raw)

    assert 0.995 > MARGIN_MAX
    assert source == "estimated"
    assert gross_margin == pytest.approx(DEFAULT_ESTIMATED_MARGIN)


def test_zero_total_revenue_does_not_raise(caplog):
    """prepare_data does not guarantee positive revenue; coverage divides by it."""
    df = pd.DataFrame({
        "product": ["Widget", "Gadget"],
        "quantity": [1, 1],
        "revenue": [0.0, 0.0],
        "cost": [5.0, 5.0],
        "unit_price": [0.0, 0.0],
        "date": pd.to_datetime(["2026-01-01", "2026-01-02"]),
        "location": ["All", "All"],
    })
    raw = df.copy()

    with caplog.at_level(logging.WARNING, logger="backend.engine.margin"):
        gross_margin, source, has_cost, _ = resolve_margin(df, raw)

    assert source == "estimated"
    assert gross_margin == pytest.approx(DEFAULT_ESTIMATED_MARGIN)
    assert has_cost is True
    assert "total revenue" in caplog.text


# ─── Root cause 3 regression: has_cost_data must be honest ──────────────────

def test_no_cost_column_reports_has_cost_data_false():
    """A file with genuinely no cost column must not claim to have cost data.

    Fails against the old implementation, which scanned the prepared frame's
    column names for "cost" and therefore always matched.
    """
    raw = _synthetic_raw(n=30, include_cost_col=False)
    df = _prepared(raw)

    # The prepared frame still has a NaN-filled `cost` column — that is exactly
    # what made the old column-name scan wrong.
    assert "cost" in df.columns
    assert df["cost"].isna().all()

    gross_margin, source, has_cost, cost_col = resolve_margin(df, raw)

    assert has_cost is False
    assert cost_col is None
    assert source == "estimated"
    assert gross_margin == pytest.approx(DEFAULT_ESTIMATED_MARGIN)


def test_no_cost_column_with_explicit_margin_still_reports_no_cost_data():
    """has_cost_data is independent of which precedence branch won."""
    raw = _synthetic_raw(n=30, include_cost_col=False)
    _, source, has_cost, cost_col = resolve_margin(_prepared(raw), raw, explicit_margin=0.5)

    assert source == "provided"
    assert has_cost is False
    assert cost_col is None


def test_cost_column_name_is_the_real_source_column():
    """The old scan always returned the literal "cost", never the source name."""
    raw = _synthetic_raw(n=30, cost=40.0).rename(columns={"cost": "COGS Amount"})
    df = _prepared(raw)

    _, source, has_cost, cost_col = resolve_margin(df, raw)

    assert has_cost is True
    assert cost_col == "COGS Amount"
    assert source == "calculated"


def test_all_null_cost_column_reports_no_cost_data():
    """A cost column present in the file but empty carries no information."""
    raw = _synthetic_raw(n=30, cost=None, cost_coverage=0.0)
    raw["cost"] = np.nan
    df = _prepared(raw)

    _, source, has_cost, _ = resolve_margin(df, raw)

    assert has_cost is False
    assert source == "estimated"


# ─── action_center threading (root cause 4) ─────────────────────────────────

def test_build_action_center_accepts_resolved_margin():
    """The price path must use the caller's margin, not a local 0.65 literal.

    Note: `_build_action_center` has no live callers today — `/action-center`
    builds recommendations via `recommendations.build_recommendations`. This
    test pins the signature so the fallback cannot silently re-diverge if the
    function is wired back up.
    """
    import inspect

    from backend.engine.action_center import _build_action_center

    sig = inspect.signature(_build_action_center)
    assert "gross_margin" in sig.parameters
    assert sig.parameters["gross_margin"].default == DEFAULT_ESTIMATED_MARGIN

    src = inspect.getsource(_build_action_center)
    assert "gross_margin_fallback" not in src, "the disconnected 0.65 literal is back"
    assert "0.65" not in src, "a hardcoded margin literal is back in the price path"
