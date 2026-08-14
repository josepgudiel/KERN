"""Gross-margin resolution — the single source of truth for every endpoint.

Margin used to be resolved in four disconnected places (two endpoints plus two
hardcoded 0.65 literals), which meant /upload and /demo could — and did — drift
apart. Everything that needs a margin now goes through `resolve_margin`.
"""
from __future__ import annotations

import logging

import pandas as pd

from .data_loader import _detect_columns

logger = logging.getLogger(__name__)

# Cost data must cover at least this share of total revenue before we trust a
# margin calculated from it. A cost column populated for a handful of cheap SKUs
# would otherwise produce a portfolio margin that is not representative.
MIN_COST_COVERAGE_FOR_MARGIN = 0.5

# A resolved margin outside this range is treated as unreliable rather than
# clipped — out-of-range almost always means a misdetected column, and silently
# clamping it to a bound would present a wrong number as a confident one.
MARGIN_MIN = 0.05
MARGIN_MAX = 0.99

# Used when there is no explicit margin and no usable cost data.
DEFAULT_ESTIMATED_MARGIN = 0.65


def resolve_margin(
    df: pd.DataFrame,
    raw_df: pd.DataFrame,
    explicit_margin: float | None = None,
    mapping: dict | None = None,
) -> tuple[float, str, bool, str | None]:
    """Resolve the gross margin for a dataset.

    Precedence:
      1. `explicit_margin` (only /upload can supply one) -> "provided"
      2. Calculated from real cost data, if coverage and sanity checks pass
         -> "calculated"
      3. `DEFAULT_ESTIMATED_MARGIN` -> "estimated"

    Args:
        df: The prepared frame from `prepare_data` (always carries a `cost`
            column, NaN-filled when no cost column was detected).
        raw_df: The original uploaded frame — used only to recover the real
            source column name for cost.
        explicit_margin: Margin supplied by the caller as a decimal (0.40 = 40%).
        mapping: Optional precomputed `_detect_columns(raw_df)` result, so
            callers that already have one don't pay for it twice.

    Returns:
        (gross_margin, margin_source, has_cost_data, cost_column_name)

    Raises:
        ValueError: If `explicit_margin` is outside [MARGIN_MIN, MARGIN_MAX].
            Callers at the HTTP boundary translate this into a 400.
    """
    # A column-name scan cannot answer this: `prepare_data` always creates a
    # `cost` column, so scanning for the substring "cost" matched every dataset
    # ever uploaded. Whether any value actually survived parsing is the only
    # honest signal.
    has_cost_data = bool("cost" in df.columns and df["cost"].notna().any())

    cost_column_name = None
    if has_cost_data:
        if mapping is None:
            mapping = _detect_columns(raw_df)
        cost_column_name = mapping.get("cost")

    # 1. Explicit margin from the caller always wins.
    if explicit_margin is not None:
        if not (MARGIN_MIN <= explicit_margin <= MARGIN_MAX):
            raise ValueError(
                f"Margin must be between {MARGIN_MIN:.0%} and {MARGIN_MAX:.0%} "
                f"(e.g., 0.40 for 40%)."
            )
        return float(explicit_margin), "provided", has_cost_data, cost_column_name

    # 2. Calculate from real cost data when there is enough of it to trust.
    if has_cost_data:
        cost_rows = df[df["cost"].notna()]
        total_revenue = float(df["revenue"].sum())
        covered_revenue = float(cost_rows["revenue"].sum())

        # prepare_data does not guarantee positive total revenue, and coverage
        # is a ratio against it.
        if total_revenue <= 0:
            logger.warning(
                "Cost data present (column '%s') but total revenue is %.2f — "
                "cannot compute a margin, falling back to the %.0f%% estimate.",
                cost_column_name, total_revenue, DEFAULT_ESTIMATED_MARGIN * 100,
            )
        else:
            coverage = covered_revenue / total_revenue
            if coverage < MIN_COST_COVERAGE_FOR_MARGIN:
                logger.info(
                    "Cost data present (column '%s') but covers only %.1f%% of revenue "
                    "(need >= %.0f%%) — falling back to the %.0f%% estimate.",
                    cost_column_name, coverage * 100,
                    MIN_COST_COVERAGE_FOR_MARGIN * 100, DEFAULT_ESTIMATED_MARGIN * 100,
                )
            else:
                computed = 1 - (float(cost_rows["cost"].sum()) / covered_revenue)
                if MARGIN_MIN <= computed <= MARGIN_MAX:
                    logger.info(
                        "Calculated gross margin %.4f from cost column '%s' "
                        "(%.1f%% revenue coverage).",
                        computed, cost_column_name, coverage * 100,
                    )
                    return computed, "calculated", has_cost_data, cost_column_name

                logger.warning(
                    "Calculated gross margin %.4f from cost column '%s' is outside "
                    "[%.2f, %.2f] (%.1f%% revenue coverage) — likely a misdetected "
                    "column, or cost exceeds revenue on refund/discount rows. "
                    "Falling back to the %.0f%% estimate.",
                    computed, cost_column_name, MARGIN_MIN, MARGIN_MAX,
                    coverage * 100, DEFAULT_ESTIMATED_MARGIN * 100,
                )

    # 3. No explicit margin, no usable cost data.
    return DEFAULT_ESTIMATED_MARGIN, "estimated", has_cost_data, cost_column_name
