"""CSV/Excel parsing and column detection — extracted from app.py."""
from __future__ import annotations

import io
import re

import numpy as np
import pandas as pd

# ─── Candidate column name lists ────────────────────────────────────────────

PRODUCT_SYNONYMS = [
    "product", "item", "name", "sku", "description", "menu",
    "service", "treatment", "coffee", "drink", "food", "title",
    "product name", "item name", "menu item", "coffee name",
]
QTY_CANDIDATES = [
    "quantity", "qty", "units", "pieces", "volume",
    "qty_sold", "units_sold", "quantity_sold", "sold", "items_sold",
    "item_count", "item count", "num_items", "num items",
    "units_ordered", "units ordered", "items",
    # Additional common variations
    "count", "item_qty", "num_sold", "# items",
]
REVENUE_SYNONYMS = [
    "revenue", "price", "money", "amount", "total", "sale", "sales",
    "gross", "net", "transaction", "charge", "cost", "value",
    "sale amount", "total amount", "gross sales", "net sales",
    "transaction amount", "sale total", "order total", "payment",
    "subtotal", "sub total", "line total", "ext price", "extended price",
]
UNIT_PRICE_CANDIDATES = [
    "unit_price", "unit price", "unitprice", "price_per_unit",
    "selling_price", "sale_price", "retail_price", "list_price", "price",
    "unit_rate", "each_price",
    "item_price", "item price",
    # Common Kaggle columns
    "mrp", "rate", "price_each", "price each",
]
DATE_SYNONYMS = [
    "date", "time", "created", "timestamp", "transaction date",
    "sale date", "order date", "datetime", "when", "day",
]
# Clock-time columns that sit *beside* a date column. Square, Toast, and Clover
# all export the calendar date and the time of day as two separate fields, so a
# single DATE_SYNONYMS match finds the date and silently discards the time.
TIME_OF_DAY_SYNONYMS = [
    "time", "time of day", "order time", "transaction time", "sale time",
    "check in time", "clock time", "receipt time", "sold at",
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
    """Find first column whose name matches any candidate via substring check."""
    for cand in candidates:
        cand_clean = cand.lower().strip().replace("_", " ")
        for col in df.columns:
            if not isinstance(col, str):
                continue
            col_clean = col.lower().strip().replace("_", " ")
            if cand_clean in col_clean or col_clean in cand_clean:
                return col
    return None


# Name fragments that look like a time column but never hold a clock time.
_TIME_COL_EXCLUDE_TOKENS = ("zone", "offset")

# "08:15", "8:15 AM", "20:15:32", "8 PM" — a colon or an am/pm token.
_CLOCK_VALUE_RE = re.compile(r"\d{1,2}\s*:\s*\d{2}|\b[ap]\.?\s?m\.?\b", re.IGNORECASE)

# Share of a candidate column's values that must look like clock times before it
# is accepted as the time-of-day source.
_MIN_CLOCK_VALUE_FRACTION = 0.5

# Share of timestamps that must fall off exact midnight before a date column is
# treated as carrying real time-of-day. See _resolve_hour_of_day.
_MIN_NON_MIDNIGHT_FRACTION = 0.5


def _looks_like_clock_column(series: pd.Series, sample: int = 500) -> bool:
    """True if most non-null values in `series` actually look like clock times.

    Name matching alone is not enough: `_find_col` matches on substrings, so
    "time" also hits duration columns like "Prep Time" or "Lead Time" whose
    values ("12", "4.5") parse into meaningless hours. This checks what the
    column contains rather than what it is called.

    Blanks are excluded from the ratio rather than counted against it. A real
    Time column that is only half filled in is still a Time column; how much of
    it is populated is a coverage question (_has_hour_data), and failing the
    column here would discard the rows that *do* have a usable time.
    """
    vals = series.dropna()
    if len(vals) > sample * 4:          # cap the string work on large uploads
        vals = vals.head(sample * 4)
    vals = vals.astype(str).str.strip()
    vals = vals[~vals.str.lower().isin(_NON_NUMERIC_STRINGS)]
    if vals.empty:
        return False
    if len(vals) > sample:
        vals = vals.head(sample)
    hits = sum(1 for v in vals if _CLOCK_VALUE_RE.search(v))
    return hits >= len(vals) * _MIN_CLOCK_VALUE_FRACTION


def _find_time_of_day_col(df: pd.DataFrame, exclude: str | None = None) -> str | None:
    """Find a separate clock-time column, skipping `exclude` (the date column).

    Guards on both the name (time *zone* / UTC *offset* columns are rejected)
    and the values (duration columns are rejected by _looks_like_clock_column).
    """
    for cand in TIME_OF_DAY_SYNONYMS:
        cand_clean = _normalize_col_name(cand.replace("_", " "))
        for col in df.columns:
            if not isinstance(col, str) or col == exclude:
                continue
            col_clean = _normalize_col_name(col)
            if any(tok in col_clean for tok in _TIME_COL_EXCLUDE_TOKENS):
                continue
            if cand_clean in col_clean or col_clean in cand_clean:
                if _looks_like_clock_column(df[col]):
                    return col
    return None


def _parse_time_of_day(series: pd.Series) -> pd.Series:
    """Parse clock-time strings permissively. Unparseable values become NaT.

    The date part of the result is whatever pandas defaulted to and is
    meaningless — callers must take only the time component.
    """
    s = series.astype(str).str.strip()
    try:
        return pd.to_datetime(s, format="mixed", errors="coerce")
    except (ValueError, TypeError):
        return pd.to_datetime(s, errors="coerce")


def _merge_time_of_day(dates: pd.Series, raw_times: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Merge a separate clock-time column onto date-only timestamps, per row.

    Returns (dates, merged_mask). A row whose time value does not parse keeps
    its date-only value — a handful of bad times must not cost the whole
    column's signal, and no row is ever dropped for having one.
    """
    parsed = _parse_time_of_day(raw_times)
    merged_mask = parsed.notna() & dates.notna()
    if not merged_mask.any():
        return dates, merged_mask
    offset = pd.to_timedelta(
        parsed.dt.hour * 3600 + parsed.dt.minute * 60 + parsed.dt.second,
        unit="s",
    )
    return dates.where(~merged_mask, dates.dt.normalize() + offset), merged_mask


def _resolve_hour_of_day(dates: pd.Series, merged_mask: pd.Series) -> pd.Series:
    """Hour of day per row as nullable Int64 — NA where there is no time signal.

    Rows fed by a separate clock-time column are trusted directly. The rest are
    judged at the *column* level: a date-only column parses to hour 0 for every
    row, which is non-null but carries no signal, so the hour is only taken from
    the date column when at least _MIN_NON_MIDNIGHT_FRACTION of its timestamps
    sit off exact midnight. Once a column clears that bar, every row keeps its
    real hour including genuine 00:xx sales — nulling those individually would
    erase the midnight daypart for precisely the late-operating businesses that
    depend on it.
    """
    hours = pd.Series(np.nan, index=dates.index, dtype="float64")
    hours[merged_mask] = dates[merged_mask].dt.hour

    rest = dates.notna() & ~merged_mask
    if rest.any():
        candidates = dates[rest]
        non_midnight = (
            (candidates.dt.hour != 0)
            | (candidates.dt.minute != 0)
            | (candidates.dt.second != 0)
        )
        if non_midnight.mean() >= _MIN_NON_MIDNIGHT_FRACTION:
            hours[rest] = candidates.dt.hour
    return hours.astype("Int64")


def _detect_columns(df: pd.DataFrame) -> dict:
    """Auto-detect columns for product, quantity, revenue/unit_price, date, time_of_day, location, cost, transaction_id."""
    product_col = _find_col(df, PRODUCT_SYNONYMS)
    if product_col is None:
        name_col = next((c for c in df.columns if c.strip().lower() == "name"), None)
        if name_col and not any("customer" in c.lower() or "client" in c.lower() for c in df.columns):
            product_col = name_col
    mapping = {
        "product": product_col or (df.columns[0] if len(df.columns) > 0 else None),
        "quantity": _find_col(df, QTY_CANDIDATES),
        "revenue": _find_col(df, REVENUE_SYNONYMS),
        "unit_price": _find_col(df, UNIT_PRICE_CANDIDATES),
        "date": _find_col(df, DATE_SYNONYMS),
        "location": _find_col(df, LOCATION_CANDIDATES),
        "cost": _find_col(df, COST_CANDIDATES),
        "transaction_id": _find_col(df, TRANSACTION_CANDIDATES),
    }
    mapping["time_of_day"] = _find_time_of_day_col(df, exclude=mapping["date"])
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


def _has_unnamed_columns(df: pd.DataFrame) -> bool:
    """Check if most columns are 'Unnamed: N' — sign of a missing/offset header."""
    unnamed = sum(1 for c in df.columns if str(c).startswith("Unnamed"))
    return unnamed > len(df.columns) * 0.5


def _try_fix_header(file_bytes: bytes, file_name: str, enc: str, sep: str) -> pd.DataFrame | None:
    """If the first row isn't a real header, try skipping 1–5 rows to find it."""
    for skip in range(1, 6):
        try:
            buf = io.BytesIO(file_bytes)
            df_try = pd.read_csv(buf, encoding=enc, sep=sep, skiprows=skip)
            if len(df_try.columns) >= 2 and not _has_unnamed_columns(df_try):
                return df_try
        except Exception:
            continue
    return None


def _load_raw(file_bytes: bytes, file_name: str, sheet_name: str | None = None) -> pd.DataFrame | None:
    """Load raw file bytes into a DataFrame."""
    buf = io.BytesIO(file_bytes)
    name = (file_name or "").lower()
    try:
        if name.endswith(".xlsx"):
            df = pd.read_excel(buf, engine="openpyxl", sheet_name=sheet_name or 0)
            if df is not None and _has_unnamed_columns(df):
                for skip in range(1, 6):
                    buf = io.BytesIO(file_bytes)
                    df_try = pd.read_excel(buf, engine="openpyxl", sheet_name=sheet_name or 0, skiprows=skip)
                    if not _has_unnamed_columns(df_try) and len(df_try.columns) >= 2:
                        return df_try
            return df
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
                        if _has_unnamed_columns(df_try):
                            fixed = _try_fix_header(file_bytes, name, enc, sep)
                            if fixed is not None:
                                return fixed
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
        cols_preview = ", ".join(list(raw_df.columns)[:8])
        return None, f"No product column detected. Your columns: {cols_preview}. Rename one to 'product'."

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
        cols_preview = ", ".join(list(raw_df.columns)[:8])
        return None, f"We couldn't detect a sales/revenue column. Your columns: {cols_preview}. Please rename your revenue column to 'revenue' or 'total'."

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

    # Time of day. POS exports from Square/Toast/Clover split the calendar date
    # and the clock time into two columns; merge the second onto the first so
    # daypart analysis has an hour to work with. Runs after the future-date
    # strip above so that adding a time component can never change which rows
    # that strip drops.
    _merged_mask = pd.Series(False, index=raw_df.index)
    tod_col = mapping.get("time_of_day")
    if (
        tod_col
        and tod_col in raw_df.columns
        and tod_col != date_col
        and needed["date"].notna().any()
    ):
        needed["date"], _merged_mask = _merge_time_of_day(needed["date"], raw_df[tod_col])
    needed["hour"] = _resolve_hour_of_day(needed["date"], _merged_mask)

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
            rev_col_name = rev_col or up_col or "unknown"
            parts.append(f"{n_no_revenue} rows had zero or negative revenue (column: '{rev_col_name}'). This column may not be actual revenue — check if it contains costs, discounts, or returns.")
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
