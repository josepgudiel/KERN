"""Tests for backend.engine.clusters — _get_product_clusters.

The engine uses KMeans with automatic k-selection (silhouette-guided, range 2–4).
Tests parametrize on dataset configurations that expose different behaviour;
k cannot be passed directly to the public API.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from backend.engine.clusters import _get_product_clusters


# ─── Helpers ────────────────────────────────────────────────────────────────


def _make_cluster_df(n_products: int = 6, txn_per_product: int = 10) -> pd.DataFrame:
    """Build a sales DataFrame with clearly separated quantity/revenue tiers.

    Products are spread across three magnitude levels so the silhouette
    criterion has something to distinguish: low (~10 units), medium (~100),
    and high (~1000).  This mimics realistic long-tail sales distributions.
    """
    tiers = [10, 100, 1000]
    rows: list[dict] = []
    for i in range(n_products):
        base_qty = tiers[i % len(tiers)] + i  # small jitter so rows aren't identical
        base_rev = base_qty * 2.5
        for _ in range(txn_per_product):
            rows.append({
                "product": f"Product_{chr(65 + i)}",
                "quantity": base_qty,
                "revenue": base_rev,
            })
    return pd.DataFrame(rows)


# ─── Normal-path tests ──────────────────────────────────────────────────────


def test_returns_dataframe_with_cluster_column() -> None:
    """Result must be a DataFrame that includes cluster and category columns."""
    df = _make_cluster_df(n_products=6)
    result = _get_product_clusters(df)

    assert result is not None
    assert isinstance(result, pd.DataFrame)
    assert "cluster" in result.columns
    assert "category" in result.columns


def test_cluster_values_are_valid_integers() -> None:
    """Cluster labels must be non-negative integers with no NaN."""
    df = _make_cluster_df(n_products=6)
    result = _get_product_clusters(df)

    assert result is not None
    assert result["cluster"].notna().all()
    assert (result["cluster"] >= 0).all()


def test_n_clusters_matches_attribute() -> None:
    """The _n_clusters metadata column must agree with unique cluster count."""
    df = _make_cluster_df(n_products=6)
    result = _get_product_clusters(df)

    assert result is not None
    n_unique = result["cluster"].nunique()
    assert result["_n_clusters"].iloc[0] == n_unique


def test_category_labels_are_recognised_strings() -> None:
    """Categories should be drawn from the fixed label set defined in the engine."""
    known_labels = {"Stars", "Low Activity", "Cash Cows", "Hidden Gems"}
    df = _make_cluster_df(n_products=6)
    result = _get_product_clusters(df)

    assert result is not None
    for cat in result["category"]:
        assert cat in known_labels, f"Unexpected category: {cat!r}"


@pytest.mark.parametrize("n_products", [5, 7, 10])
def test_clustering_works_for_various_product_counts(n_products: int) -> None:
    """Clustering should succeed and return valid results across different catalogue sizes."""
    df = _make_cluster_df(n_products=n_products)
    result = _get_product_clusters(df)

    assert result is not None
    assert len(result) == n_products
    assert result["cluster"].notna().all()


# ─── Stability test ─────────────────────────────────────────────────────────


def test_cluster_assignments_are_deterministic() -> None:
    """Same input must produce identical cluster assignments (random_state=42)."""
    df = _make_cluster_df(n_products=6)
    result_a = _get_product_clusters(df)
    result_b = _get_product_clusters(df)

    assert result_a is not None and result_b is not None
    a_sorted = result_a.sort_values("product")["cluster"].values
    b_sorted = result_b.sort_values("product")["cluster"].values
    np.testing.assert_array_equal(a_sorted, b_sorted)


# ─── Log-transformation edge cases ──────────────────────────────────────────


def test_zero_quantity_rows_do_not_crash() -> None:
    """Rows with quantity=0 should be handled via clip(min=0) + log1p without error."""
    df = _make_cluster_df(n_products=6)
    # Introduce zero-quantity rows for every product
    df.loc[df.index[::10], "quantity"] = 0
    result = _get_product_clusters(df)
    # Should either succeed or return None — must not raise
    if result is not None:
        assert result["cluster"].notna().all()


def test_negative_quantity_rows_do_not_crash() -> None:
    """Negative quantities are clipped to 0 before log1p — no crash expected."""
    df = _make_cluster_df(n_products=6)
    df.loc[df.index[::10], "quantity"] = -5
    result = _get_product_clusters(df)
    if result is not None:
        assert result["cluster"].notna().all()


# ─── Minimum-product guard ───────────────────────────────────────────────────


def test_fewer_than_four_products_returns_none() -> None:
    """The engine requires ≥ 4 distinct products; below that it returns None."""
    df = _make_cluster_df(n_products=3)
    result = _get_product_clusters(df)
    assert result is None
