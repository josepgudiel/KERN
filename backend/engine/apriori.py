"""Apriori association rules (market basket) — extracted from app.py."""
from __future__ import annotations

import io

import pandas as pd

try:
    from mlxtend.frequent_patterns import apriori as _apriori, association_rules as _assoc_rules
    from mlxtend.preprocessing import TransactionEncoder as _TransactionEncoder
    _MLXTEND_AVAILABLE = True
except Exception:
    _MLXTEND_AVAILABLE = False


def _compute_basket_rules(df: pd.DataFrame) -> tuple:
    """Build association rules from session baskets.

    Returns (frequent_itemsets, rules_df, error_str | None, basket_method_str).
    """
    if not _MLXTEND_AVAILABLE:
        return None, None, "mlxtend_missing", ""

    if "date" not in df.columns:
        return None, None, "no_date", ""

    dfc = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(dfc["date"]):
        dfc["date"] = pd.to_datetime(dfc["date"], errors="coerce")
    dfc = dfc.dropna(subset=["date"])

    has_txn_id = (
        "transaction_id" in dfc.columns
        and dfc["transaction_id"].notna().any()
        and (dfc["transaction_id"] != "None").any()
        and (dfc["transaction_id"] != "nan").any()
    )
    if has_txn_id:
        dfc["_session"] = dfc["transaction_id"].astype(str)
        basket_method = "order-level (transaction ID)"
    else:
        loc_col_val = dfc["location"] if "location" in dfc.columns else pd.Series("All", index=dfc.index)
        dfc["_session"] = dfc["date"].dt.date.astype(str) + "_" + loc_col_val.astype(str)
        basket_method = "day × location proxy (no transaction ID found)"

    baskets = dfc.groupby("_session")["product"].apply(list).reset_index()
    n_baskets = len(baskets)

    if n_baskets < 10:
        return None, None, f"insufficient_data ({n_baskets} sessions — need 10+)", basket_method

    # Skip Apriori if most transactions are single-item — bundles can't be inferred
    single_item_count = baskets["product"].apply(lambda items: len(set(items)) == 1).sum()
    single_item_pct = single_item_count / n_baskets if n_baskets > 0 else 0
    if single_item_pct > 0.70:
        return None, None, "single_item_dominated", basket_method

    te = _TransactionEncoder()
    te_array = te.fit_transform(baskets["product"])
    basket_df = pd.DataFrame(te_array, columns=te.columns_)

    min_support = max(0.05, 5 / n_baskets)
    try:
        frequent_itemsets = _apriori(basket_df, min_support=min_support, use_colnames=True, max_len=2)
    except Exception as exc:
        return None, None, str(exc), basket_method

    if frequent_itemsets.empty:
        return None, None, "no_frequent_itemsets", basket_method

    try:
        rules = _assoc_rules(frequent_itemsets, metric="lift", min_threshold=1.05)
    except Exception as exc:
        return None, None, str(exc), basket_method

    if rules.empty:
        return None, None, "no_rules", basket_method

    rules = rules[rules["consequents"].apply(len) == 1].copy()
    if rules.empty:
        return frequent_itemsets, None, "no_single_consequent_rules", basket_method
    rules["antecedent"] = rules["antecedents"].apply(lambda x: ", ".join(sorted(str(i) for i in x)))
    rules["consequent"] = rules["consequents"].apply(lambda x: str(next(iter(x))))
    rules = rules.sort_values("lift", ascending=False).reset_index(drop=True)
    return frequent_itemsets, rules, None, basket_method
