"""K-Means product clustering — extracted from app.py."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score


def _label_clusters(centers_df: pd.DataFrame) -> dict:
    """Label clusters uniquely — no two clusters can share a name."""
    df = centers_df.copy()
    q_range = df["quantity"].max() - df["quantity"].min() + 1e-9
    r_range = df["revenue"].max() - df["revenue"].min() + 1e-9
    df["q_n"] = (df["quantity"] - df["quantity"].min()) / q_range
    df["r_n"] = (df["revenue"] - df["revenue"].min()) / r_range

    score_map = {
        "Stars":        df["q_n"] + df["r_n"],
        "Low Activity": -(df["q_n"] + df["r_n"]),
        "Cash Cows":    df["r_n"] - df["q_n"],
        "Hidden Gems":  df["q_n"] - df["r_n"],
    }

    labels = {}
    used = set()
    for label in ["Stars", "Low Activity", "Cash Cows", "Hidden Gems"]:
        scores = score_map[label]
        for idx in scores.sort_values(ascending=False).index:
            if idx not in used:
                labels[idx] = label
                used.add(idx)
                break
    return labels


def _get_product_clusters(df: pd.DataFrame) -> pd.DataFrame | None:
    """Run K-Means and return product-level aggregates with cluster labels."""
    agg = df.groupby("product").agg(
        quantity=("quantity", "sum"),
        revenue=("revenue", "sum")
    ).reset_index()
    if len(agg) < 4:
        return None

    agg["avg_txn"] = agg["revenue"] / agg["quantity"].clip(lower=1)

    X_raw = agg[["quantity", "revenue"]].values.clip(min=0)
    X_log = np.log1p(X_raw)
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_log)
    _used_scaler = not np.isnan(X_scaled).any()
    if not _used_scaler:
        X_scaled = X_log

    best_k, best_sil = 2, None
    max_k = min(4, len(agg) - 1)
    for k in range(2, max_k + 1):
        km = KMeans(n_clusters=k, random_state=42, n_init=10)
        lbls = km.fit_predict(X_scaled)
        if len(set(lbls)) < 2:
            continue
        try:
            sil = silhouette_score(X_scaled, lbls)
        except ValueError:
            continue
        if best_sil is None or sil > best_sil:
            best_sil, best_k = sil, k

    kmeans = KMeans(n_clusters=best_k, random_state=42, n_init=10)
    agg["cluster"] = kmeans.fit_predict(X_scaled)
    if _used_scaler:
        centers_raw = np.expm1(scaler.inverse_transform(kmeans.cluster_centers_))
    else:
        centers_raw = np.expm1(kmeans.cluster_centers_)
    centers = pd.DataFrame(centers_raw, columns=["quantity", "revenue"])
    cluster_labels = _label_clusters(centers)
    agg["category"] = agg["cluster"].map(cluster_labels)
    _sil_val = round(best_sil, 3) if best_sil is not None else None
    agg.attrs["silhouette_score"] = _sil_val
    agg.attrs["n_clusters"] = best_k
    agg["_sil_score"] = _sil_val
    agg["_n_clusters"] = best_k
    return agg
