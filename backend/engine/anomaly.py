"""MAD-based anomaly detection — extracted from app.py."""
from __future__ import annotations

import hashlib
import re

import numpy as np
import pandas as pd

from .safety import _has_dates, _MAD_ANOMALY_Z


def _suggest_anomaly_label(date_str: str, direction: str, z_score: float, top_product: str) -> str:
    """Return a short plain-English auto-label for an anomaly (max 60 chars)."""
    try:
        date = pd.Timestamp(date_str)
        month, day = date.month, date.day
        weekday = date.day_name()

        def _tp(template: str) -> str:
            if top_product:
                result = template.replace("{top_product}", top_product)
            else:
                result = (
                    template
                    .replace("{top_product} spike — ", "Spike — ")
                    .replace(" — {top_product}", "")
                    .replace("{top_product} ", "")
                    .replace("{top_product}", "")
                )
            return result[:60]

        def _easter_sunday(year: int) -> pd.Timestamp:
            a = year % 19
            b = year // 100
            c = year % 100
            d = b // 4
            e = b % 4
            f = (b + 8) // 25
            g = (b - f + 1) // 3
            h = (19 * a + b - d - g + 15) % 30
            i = c // 4
            k = c % 4
            l = (32 + 2 * e + 2 * i - h - k) % 7
            m = (a + 11 * h + 22 * l) // 451
            month_e = (h + l - 7 * m + 114) // 31
            day_e = ((h + l - 7 * m + 114) % 31) + 1
            return pd.Timestamp(year, month_e, day_e)

        def _nth_weekday(year: int, mnth: int, weekday_n: int, n: int) -> pd.Timestamp:
            import calendar
            first_day, _ = calendar.monthrange(year, mnth)
            first_wd = (weekday_n - first_day) % 7
            day_n = first_wd + 1 + (n - 1) * 7
            return pd.Timestamp(year, mnth, day_n)

        def _last_thursday(year: int, mnth: int) -> pd.Timestamp:
            import calendar
            _, num_days = calendar.monthrange(year, mnth)
            for d in range(num_days, 0, -1):
                if pd.Timestamp(year, mnth, d).day_name() == "Thursday":
                    return pd.Timestamp(year, mnth, d)
            return pd.Timestamp(year, mnth, 1)

        if direction == "spike":
            if month == 2 and day == 14:
                return _tp("{top_product} spike — Valentine's Day effect?")
            if month == 12 and day in (24, 25):
                return "Holiday rush — Christmas effect?"
            if (month == 12 and day == 31) or (month == 1 and day == 1):
                return "New Year's spike?"
            if month == 11:
                last_thu = _last_thursday(date.year, 11)
                black_fri = last_thu + pd.Timedelta(days=1)
                if date.date() in (last_thu.date(), black_fri.date()):
                    return "Thanksgiving / Black Friday effect?"
            if month == 10 and day == 31:
                return "Halloween spike?"
            if month in (3, 4):
                easter = _easter_sunday(date.year)
                if abs((date - easter).days) <= 3:
                    return "Easter effect?"
            if month == 5:
                mothers = _nth_weekday(date.year, 5, 6, 2)
                if date.date() == mothers.date():
                    return "Mother's Day spike?"
            if month == 6:
                fathers = _nth_weekday(date.year, 6, 6, 3)
                if date.date() == fathers.date():
                    return "Father's Day spike?"
            if weekday in ("Friday", "Saturday"):
                return _tp("Weekend spike — {top_product}?")
            if z_score > 4:
                return "Major spike — special event or promotion?"
            return "Above-normal day — promotion or event?"
        else:
            if weekday == "Monday":
                return "Monday dip — normal for your pattern?"
            if month == 1 and 1 <= day <= 7:
                return "Post-holiday slowdown?"
            if z_score > 4:
                return "Major dip — closure or supply issue?"
            return "Quiet day — check for a pattern?"
    except Exception:
        return "Unusual day — worth investigating?"


def detect_anomalies(df: pd.DataFrame) -> list[dict]:
    """Run MAD anomaly detection on daily revenue and return annotated anomaly list.

    Uses day-of-week normalization: each day is compared to the baseline for that
    weekday (e.g., Mondays vs Mondays). Falls back to global MAD if fewer than 4
    observations exist for a given weekday.
    """
    if not _has_dates(df):
        return []

    dfc = df.copy()
    dfc["date_only"] = dfc["date"].dt.date
    _daily_raw = dfc.groupby("date_only")["revenue"].sum().sort_index()
    _full_idx = pd.date_range(_daily_raw.index.min(), _daily_raw.index.max(), freq="D").date
    daily = _daily_raw.reindex(_full_idx, fill_value=0.0)
    n = len(daily)

    if n < 14:
        return []

    _daily_txn_counts = dfc.groupby("date_only").size()
    _daily_txn_counts = _daily_txn_counts.reindex(_full_idx, fill_value=0)
    _MIN_TXN_PER_DAY_FOR_ANOMALY = 3
    _sufficient_days = _daily_txn_counts >= _MIN_TXN_PER_DAY_FOR_ANOMALY
    daily_for_anomaly = daily[_sufficient_days]

    if len(daily_for_anomaly) < 10:
        return []

    # Global MAD as fallback
    global_median = daily_for_anomaly.median()
    global_mad = np.median(np.abs(daily_for_anomaly - global_median))
    global_mad_scaled = global_mad * 1.4826

    if global_mad_scaled <= 0:
        return []

    # Build per-weekday baselines (key: weekday int 0=Mon..6=Sun -> (median, mad_scaled))
    dow_baselines: dict[int, tuple[float, float]] = {}
    for dow in range(7):
        dow_dates = [d for d in daily_for_anomaly.index if pd.Timestamp(str(d)).dayofweek == dow]
        if len(dow_dates) >= 4:
            vals = daily_for_anomaly[dow_dates]
            m = float(vals.median())
            mad = float(np.median(np.abs(vals - m))) * 1.4826
            if mad > 0:
                dow_baselines[dow] = (m, mad)

    # Compute robust z-scores using day-of-week baseline where available
    robust_z_dict: dict = {}
    for date, rev in daily_for_anomaly.items():
        dow = pd.Timestamp(str(date)).dayofweek
        if dow in dow_baselines:
            m, mad_s = dow_baselines[dow]
        else:
            m, mad_s = global_median, global_mad_scaled
        robust_z_dict[date] = (float(rev) - m) / mad_s

    daily_rev = dfc.groupby(dfc["date"].dt.date)["revenue"].sum()
    median_daily = float(daily_rev.median()) if not daily_rev.empty else 0.0

    anomalies = []
    for date, z_val in robust_z_dict.items():
        if abs(z_val) <= _MAD_ANOMALY_Z:
            continue
        rev = float(daily_for_anomaly[date])

        # Use day-of-week median as "normal" reference for direction
        dow = pd.Timestamp(str(date)).dayofweek
        if dow in dow_baselines:
            ref_median = dow_baselines[dow][0]
        else:
            ref_median = global_median

        direction = "spike" if rev > ref_median else "dip"

        # Find top product for this day
        top_product = ""
        try:
            day_mask = dfc["date"].dt.date == pd.Timestamp(str(date)).date()
            if day_mask.any():
                top_product = dfc[day_mask].groupby("product")["revenue"].sum().idxmax()
        except Exception:
            top_product = ""

        pct_above = 0.0
        if median_daily != 0:
            pct_above = ((rev - median_daily) / median_daily) * 100

        auto_label = _suggest_anomaly_label(str(date), direction, float(abs(z_val)), top_product)

        try:
            date_label = pd.Timestamp(str(date)).strftime("%b %-d, %Y")
        except ValueError:
            date_label = pd.Timestamp(str(date)).strftime("%b %d, %Y").replace(" 0", " ")

        anomalies.append({
            "date": str(date),
            "date_label": date_label,
            "direction": direction,
            "revenue": rev,
            "z_score": round(float(abs(z_val)), 1),
            "pct_above": round(float(pct_above), 1),
            "top_product": str(top_product),
            "auto_label": auto_label,
        })

    return anomalies
