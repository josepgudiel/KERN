"""CSV/Excel parsing and column detection — extracted from app.py."""
from __future__ import annotations

import io
import re

import numpy as np
import pandas as pd

# ─── Candidate column name lists ────────────────────────────────────────────

PRODUCT_CANDIDATES = [
    "product", "item", "product_name", "item_name", "sku", "description",
    "beverage", "drink", "menu_item", "line_item", "product_desc", "item_desc",
    "article", "service",
    "product_code", "item_code", "item_number", "part_number", "product_title",
    "title", "label", "variant", "option",
    "lineitem_name", "lineitem name", "lineitem",
    "item_description", "product_description",
    "menu_item_name", "menu item", "menu item name",
    "item name", "product name",
    "variant_name", "variant name",
    # Services / beauty / wellness
    "treatment", "treatment name", "treatment_name",
    "service name", "service_name", "service_type",
]
QTY_CANDIDATES = [
    "quantity", "qty", "units", "pieces", "volume",
    "qty_sold", "units_sold", "quantity_sold", "sold", "items_sold",
    "item_count", "item count", "num_items", "num items",
    "units_ordered", "units ordered", "items",
    # Additional common variations
    "count", "item_qty", "num_sold", "# items",
]
REVENUE_CANDIDATES = [
    "revenue", "extended_price", "line_total",
    "subtotal", "price_total", "gross_sales", "revenue_total", "sale_amount",
    "extended", "line_amount", "net_sales", "net_amount", "sale_total",
    "total_price", "total_revenue", "net_revenue",
    "invoice_total", "line_value", "amount_paid", "total_amount",
    "gross_amount",
    "net_total", "total_retail_price",
    "order_total_amount",
    "item_total", "item total", "check_amount", "check amount",
    "transaction_amount", "transaction amount",
    "ticket_total", "ticket total",
    "sales_amount", "sales amount", "total_sales", "total sales",
    "final_price", "final price",
    # Clover, Lightspeed, and generic POS exports
    "total", "lineitem price", "line item price",
    "total incl tax", "total incl. tax", "total including tax",
]
UNIT_PRICE_CANDIDATES = [
    "unit_price", "unit price", "unitprice", "price_per_unit",
    "selling_price", "sale_price", "retail_price", "list_price", "price",
    "unit_rate", "each_price",
    "item_price", "item price",
]
DATE_CANDIDATES = [
    "date", "timestamp", "datetime", "order_date", "transaction_date",
    "sale_date", "created_at", "order_time", "transaction_time",
    "invoice_date", "purchase_date", "sold_at", "completed_at",
    "business_date", "business date",
    "receipt_date", "receipt date",
    "created_date", "created date", "closed_date", "closed date",
    "check_date", "check date",
    "paid_at", "paid at",
    "date_time", "date time",
    "payment_date", "payment date",
]
LOCATION_CANDIDATES = [
    "location", "store", "outlet", "branch", "place", "site", "shop", "venue",
    "store_name", "store name", "warehouse", "region", "territory",
    "restaurant", "revenue_center", "revenue center",
    "dining_room", "dining room",
    "register", "location_name", "location name",
    "establishment",
]
COST_CANDIDATES = [
    "cost", "cogs", "unit_cost", "cost_price", "cost_of_goods", "purchase_price",
    "buying_price", "wholesale", "cost_per_unit", "item_cost", "direct_cost",
    "variable_cost", "product_cost",
    "cost of goods", "cogs_amount", "cogs amount",
]
TRANSACTION_CANDIDATES = [
    "transaction_id", "transaction id", "order_id", "order id",
    "check_id", "check id", "check_number", "check number", "check#",
    "check_num", "check_no",
    "order_number", "order number", "receipt_id", "receipt id",
    "invoice_id", "invoice id", "ticket_id", "ticket id",
    "sale_id", "sale id", "visit_id", "visit id",
    "ticket_number", "ticket number", "ticket_num", "ticket num",
    "pos_id", "pos id",
    "check num",
    "tab_id", "tab id",
    "payment_id", "payment id", "transaction_reference", "transaction reference",
    "transaction_number", "transaction number",
]

AGGREGATE_ROW_NAMES = {
    "total", "subtotal", "sub-total", "sub total",
    "grand total", "grand-total",
    "tax", "sales tax", "vat", "gst", "hst",
    "discount", "discount total",
    "shipping", "shipping & handling", "shipping and handling",
    "freight", "delivery",
    "tip", "gratuity",
    "refund", "return",
    "adjustment", "misc", "miscellaneous",
    "service charge", "service fee",
    "surcharge", "fee",
}

_NON_NUMERIC_STRINGS = frozenset(
    ["n/a", "#n/a", "#value!", "#ref!", "#div/0!", "#name?", "#null!", "#num!", "na", "nan", "none", "null", "-", ""]
)


# ─── Helper functions ───────────────────────────────────────────────────────

def _normalize_col_name(s: str) -> str:
    """Normalize a column name for word-set matching."""
    s = s.lower().strip()
    s = s.replace("/", " ").replace("\\", " ")
    s = s.replace("#", " num ").replace("№", " num ")
    s = s.replace("-", " ").replace(".", " ")
    return " ".join(s.split())


def _find_col(df: pd.DataFrame, candidates: list) -> str | None:
    """Find first column whose name (lowercase) contains any candidate."""
    cols_lower = {c.lower().strip(): c for c in df.columns if isinstance(c, str)}
    cols_normalized = {k: _normalize_col_name(k) for k in cols_lower}
    for cand in candidates:
        cand_norm = cand.replace("_", " ")
        for k, v in cols_lower.items():
            k_norm = k.replace(" ", "_")
            k_clean = cols_normalized[k]
            cand_words = set(cand_norm.split())
            k_words = set(k.split())
            k_norm_words = set(k_norm.split("_"))
            k_clean_words = set(k_clean.split())
            if (
                cand_words.issubset(k_words)
                or cand_words.issubset(k_norm_words)
                or cand_words.issubset(k_clean_words)
                or (len(k) >= 4 and len(k_words) >= 2 and k_words.issubset(cand_words))
                or (len(k_norm) >= 4 and len(k_norm_words) >= 2 and k_norm_words.issubset(cand_words))
                or (len(k_clean) >= 4 and len(k_clean_words) >= 2 and k_clean_words.issubset(cand_words))
            ):
                return v
    return None


def _detect_columns(df: pd.DataFrame) -> dict:
    """Auto-detect columns for product, quantity, revenue/unit_price, date, location, cost, transaction_id."""
    product_col = _find_col(df, PRODUCT_CANDIDATES)
    if product_col is None:
        name_col = next((c for c in df.columns if c.strip().lower() == "name"), None)
        if name_col and not any("customer" in c.lower() or "client" in c.lower() for c in df.columns):
            product_col = name_col
    mapping = {
        "product": product_col or (df.columns[0] if len(df.columns) > 0 else None),
        "quantity": _find_col(df, QTY_CANDIDATES),
        "revenue": _find_col(df, REVENUE_CANDIDATES),
        "unit_price": _find_col(df, UNIT_PRICE_CANDIDATES),
        "date": _find_col(df, DATE_CANDIDATES),
        "location": _find_col(df, LOCATION_CANDIDATES),
        "cost": _find_col(df, COST_CANDIDATES),
        "transaction_id": _find_col(df, TRANSACTION_CANDIDATES),
    }
    if mapping["revenue"] and mapping["unit_price"] and mapping["revenue"] == mapping["unit_price"]:
        mapping["revenue"] = None
    if mapping["cost"] and mapping["cost"] in (mapping["revenue"], mapping["unit_price"]):
        mapping["cost"] = None
    return mapping


def _parse_numeric(series: pd.Series) -> pd.Series:
    """Parse numeric values, stripping currency symbols, commas, and accounting parentheses."""
    def clean(x):
        if pd.isna(x):
            return np.nan
        s = str(x).strip()
        if s.lower() in _NON_NUMERIC_STRINGS:
            return np.nan
        negative = s.startswith("(") and s.endswith(")")
        s = s.replace("(", "").replace(")", "")
        s = s.replace("\u2212", "-")
        s = s.replace("\u00a0", "").replace(" ", "")
        for sym in ("R$", "A$", "C$", "NZ$", "HK$", "S$", "kr", "CHF", "Fr"):
            s = s.replace(sym, "")
        s = s.replace("$", "").replace("€", "").replace("£", "").replace("₹", "") \
             .replace("¥", "").replace("₩", "").replace("₱", "").replace("₺", "") \
             .replace("₿", "").replace("฿", "").replace("%", "")
        if "," in s and "." in s:
            last_comma = s.rfind(",")
            last_period = s.rfind(".")
            if last_comma > last_period:
                s = s.replace(".", "").replace(",", ".")
            else:
                s = s.replace(",", "")
        elif "," in s:
            parts = s.split(",")
            if len(parts) == 2 and len(parts[1]) == 3:
                s = s.replace(",", "")
            elif len(parts) == 2 and len(parts[1]) <= 2:
                s = parts[0] + "." + parts[1]
            else:
                s = s.replace(",", "")
        try:
            val = float(s)
            return -val if negative else val
        except ValueError:
            return np.nan
    return series.apply(clean)


def _excel_sheet_names(file_bytes: bytes, file_name: str) -> list[str]:
    """Return sheet names for an Excel file."""
    buf = io.BytesIO(file_bytes)
    try:
        engine = "openpyxl" if file_name.lower().endswith(".xlsx") else None
        xl = pd.ExcelFile(buf, engine=engine)
        return xl.sheet_names
    except Exception:
        return []


def _load_raw(file_bytes: bytes, file_name: str, sheet_name: str | None = None) -> pd.DataFrame | None:
    """Load raw file bytes into a DataFrame."""
    buf = io.BytesIO(file_bytes)
    name = (file_name or "").lower()
    try:
        if name.endswith(".xlsx"):
            return pd.read_excel(buf, engine="openpyxl", sheet_name=sheet_name or 0)
        if name.endswith(".xls"):
            try:
                return pd.read_excel(buf, sheet_name=sheet_name or 0)
            except ImportError:
                return None
        for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
            for sep in (",", ";", "\t"):
                try:
                    buf.seek(0)
                    df_try = pd.read_csv(buf, encoding=enc, sep=sep)
                    if len(df_try.columns) >= 2:
                        return df_try
                except Exception:
                    continue
        return None
    except Exception:
        return None


def _prepare_data_impl(raw_df: pd.DataFrame, mapping_override: dict | None = None) -> tuple[pd.DataFrame | None, str | None]:
    """Inner logic for data prep. Returns (df, None) on success, (None, error_msg) on failure."""
    auto_mapping = _detect_columns(raw_df)
    mapping = {**auto_mapping, **(mapping_override or {})}

    product_col = mapping.get("product")
    if not product_col or product_col not in raw_df.columns:
        return None, "No product column detected."

    needed = {"product": raw_df[product_col].astype(str).str.strip().str.lower().str.replace(r"\s+", " ", regex=True)}

    qty_col = mapping.get("quantity")
    if qty_col and qty_col in raw_df.columns:
        needed["quantity"] = _parse_numeric(raw_df[qty_col]).fillna(1).clip(lower=0)
    else:
        needed["quantity"] = pd.Series(1, index=raw_df.index)

    rev_col = mapping.get("revenue")
    up_col = mapping.get("unit_price")
    if rev_col and rev_col in raw_df.columns:
        needed["revenue"] = _parse_numeric(raw_df[rev_col]).fillna(0)
    elif up_col and up_col in raw_df.columns:
        unit_price = _parse_numeric(raw_df[up_col]).fillna(0)
        needed["revenue"] = unit_price * needed["quantity"]
    else:
        return None, "No revenue or unit price column detected."

    _date_dayfirst_detected = False
    date_col = mapping.get("date")
    if date_col and date_col in raw_df.columns:
        raw_date_series = raw_df[date_col]
        _parsed_mf = pd.to_datetime(raw_date_series, errors="coerce", dayfirst=False)
        _parsed_df = pd.to_datetime(raw_date_series, errors="coerce", dayfirst=True)
        n_mf = _parsed_mf.notna().sum()
        n_df = _parsed_df.notna().sum()
        both_valid = _parsed_mf.notna() & _parsed_df.notna()
        n_disagree = (both_valid & (_parsed_mf != _parsed_df)).sum()
        if n_disagree > 0 and n_df > n_mf:
            _parsed = _parsed_df
            _date_dayfirst_detected = True
        elif n_disagree > 0 and n_mf >= n_df:
            _parsed = _parsed_mf
        else:
            _parsed = _parsed_mf if n_mf >= n_df else _parsed_df
        if getattr(_parsed.dt, "tz", None) is not None:
            _parsed = _parsed.dt.tz_convert("UTC").dt.tz_localize(None)
        needed["date"] = _parsed
    else:
        needed["date"] = pd.Series(pd.NaT, index=raw_df.index)

    n_future_stripped = 0
    if date_col and needed["date"].notna().any():
        _tomorrow = pd.Timestamp.now().normalize() + pd.Timedelta(days=1)
        _future_mask = needed["date"] > _tomorrow
        n_future_stripped = int(_future_mask.sum())
        if n_future_stripped > 0:
            needed["date"] = needed["date"].where(~_future_mask, pd.NaT)

    loc_col = mapping.get("location")
    if loc_col and loc_col in raw_df.columns:
        needed["location"] = raw_df[loc_col].astype(str)
    else:
        needed["location"] = pd.Series("All", index=raw_df.index)

    cost_col = mapping.get("cost")
    if cost_col and cost_col in raw_df.columns:
        needed["cost"] = _parse_numeric(raw_df[cost_col]).fillna(np.nan).clip(lower=0)
    else:
        needed["cost"] = pd.Series(np.nan, index=raw_df.index)

    txn_col = mapping.get("transaction_id")
    if txn_col and txn_col in raw_df.columns:
        needed["transaction_id"] = raw_df[txn_col].astype(str).str.strip()
    else:
        needed["transaction_id"] = pd.Series(None, index=raw_df.index, dtype=object)

    out = pd.DataFrame(needed)
    n_date_dropped = 0
    n_parsed = 0
    if date_col:
        n_parsed = out["date"].notna().sum()
        if n_parsed > 0:
            n_date_dropped = out["date"].isna().sum()
            out = out[out["date"].notna()]
        else:
            out["date"] = pd.NaT

    n_before = len(out)
    _BAD_PRODUCTS = {
        "nan", "none", "null", "n/a", "#n/a", "#value!", "#ref!", "#div/0!",
        "#name?", "#null!", "#num!", "undefined", "-", "na",
    }
    out = out[~out["product"].str.strip().str.lower().isin(_BAD_PRODUCTS)]
    out = out[out["product"].str.strip().str.len() > 0]
    n_no_product = n_before - len(out)
    n_before2 = len(out)
    out = out[~out["product"].str.strip().str.lower().isin(AGGREGATE_ROW_NAMES)]
    n_aggregate = n_before2 - len(out)
    n_before2 = len(out)
    out = out[out["revenue"].notna() & np.isfinite(out["revenue"]) & (out["revenue"] > 0)]
    n_no_revenue = n_before2 - len(out)

    if out.empty:
        parts = ["No valid rows after filtering."]
        if date_col and n_parsed == 0:
            parts.append(f"Date column '{date_col}' was detected but 0 values could be parsed.")
        if n_no_product:
            parts.append(f"{n_no_product} rows had empty/null product names.")
        if n_aggregate:
            parts.append(f"{n_aggregate} summary/aggregate rows were excluded.")
        if n_no_revenue:
            parts.append(f"{n_no_revenue} rows had zero or negative revenue.")
        return None, " ".join(parts)

    warning_parts = []
    if n_future_stripped > 0:
        warning_parts.append(f"{n_future_stripped} row(s) had dates in the future and were excluded.")
    if _date_dayfirst_detected:
        warning_parts.append(f"Dates in column '{date_col}' appear to use dd/mm/yyyy format.")
    if n_date_dropped > 0:
        warning_parts.append(f"{n_date_dropped} rows had unparseable dates and were excluded.")
    if n_no_product:
        warning_parts.append(f"{n_no_product} rows with empty/null product names were excluded.")
    if n_aggregate:
        warning_parts.append(f"{n_aggregate} summary rows were excluded.")
    if n_no_revenue:
        warning_parts.append(f"{n_no_revenue} rows with zero or negative revenue were excluded.")

    return out, " ".join(warning_parts) if warning_parts else None


def prepare_data(raw_df: pd.DataFrame, mapping_override: dict | None = None) -> tuple[pd.DataFrame | None, str | None]:
    """Prepare raw DataFrame for analysis. Returns (df, warning_or_error_msg)."""
    return _prepare_data_impl(raw_df, mapping_override)
