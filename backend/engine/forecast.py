"""Forecasting — StatsForecast / Prophet / linear regression extracted from app.py."""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from .safety import _has_dates

try:
    from prophet import Prophet as _Prophet
    _PROPHET_AVAILABLE = True
except Exception:
    _PROPHET_AVAILABLE = False

try:
    from statsforecast import StatsForecast as _StatsForecast
    from statsforecast.models import AutoARIMA as _AutoARIMA, AutoETS as _AutoETS
    _STATSFORECAST_AVAILABLE = True
except Exception:
    _STATSFORECAST_AVAILABLE = False


def _per_product_forecast(df: pd.DataFrame, forecast_weeks: int) -> list | None:
    """Linear trend forecast per top product. Returns list of dicts or None."""
    if not _has_dates(df):
        return None
    top_products = df.groupby("product")["revenue"].sum().nlargest(8).index.tolist()
    _data_min = df["date"].min()
    _data_max = df["date"].max()
    _first_full_week = (_data_min + pd.Timedelta(days=(7 - _data_min.dayofweek) % 7)).normalize()
    _last_full_week_end = (_data_max - pd.Timedelta(days=(_data_max.dayofweek + 1) % 7)).normalize()
    results = []
    for product in top_products:
        prod_df = df[df["product"] == product].copy()
        prod_df["week"] = prod_df["date"].dt.to_period("W").dt.start_time
        weekly = prod_df.groupby("week")["revenue"].sum().reset_index()
        weekly.columns = ["week", "revenue"]
        if len(weekly) > 2:
            weekly = weekly[
                (weekly["week"] >= _first_full_week) &
                (weekly["week"] <= _last_full_week_end)
            ]
        if len(weekly) < 4:
            continue
        weekly["days"] = (weekly["week"] - weekly["week"].min()).dt.days
        x = weekly["days"].values.astype(float)
        y = weekly["revenue"].values.astype(float)
        _hl = max(len(x) / 3, 3)
        _w = np.exp(np.log(2) * (x - x[-1]) / (_hl * 7))
        slope, intercept = np.polyfit(x, y, 1, w=_w)
        avg_weekly = float(y.mean())
        slope_pct = slope / avg_weekly * 100 if avg_weekly > 0 else 0
        direction = "↑ Growing" if slope_pct > 2 else ("↓ Declining" if slope_pct < -2 else "→ Stable")
        current_weekly = float(y[-4:].mean())
        last_day = float(x[-1])
        future_days_arr = last_day + np.arange(1, forecast_weeks + 1) * 7
        projected_weekly_series = np.maximum(slope * future_days_arr + intercept, 0)
        total_projected_change = float(projected_weekly_series.sum() - current_weekly * forecast_weeks)
        confident = abs(slope_pct) > 3 and len(weekly) >= 6
        results.append({
            "product": product,
            "direction": direction,
            "slope_pct_weekly": round(slope_pct, 1),
            "projected_change_dollars": round(total_projected_change, 2) if confident else None,
            "current_weekly_avg": round(current_weekly, 2),
            "n_transactions": len(prod_df),
        })
    return results if results else None


def compute_revenue_forecast(df: pd.DataFrame, forecast_weeks: int = 4) -> dict:
    """Compute main revenue forecast. Returns structured dict."""
    if not _has_dates(df):
        return {"error": "no_dates", "warning": "No date column found."}

    dfc = df.copy()
    dfc["date_only"] = dfc["date"].dt.date

    daily = dfc.groupby("date_only")["revenue"].sum().sort_index().reset_index()
    daily["date_only"] = pd.to_datetime(daily["date_only"])
    full_idx = pd.date_range(daily["date_only"].min(), daily["date_only"].max(), freq="D")
    daily = (daily.set_index("date_only")
                  .reindex(full_idx, fill_value=0.0)
                  .rename_axis("date_only")
                  .reset_index())
    daily["days_since_start"] = (daily["date_only"] - daily["date_only"].min()).dt.days

    n_history_days = len(daily)
    if n_history_days < 28:
        return {
            "status": "insufficient_data",
            "error": "insufficient_data",
            "min_days_needed": 28,
            "days_provided": n_history_days,
            "warning": (
                f"Need at least 28 days of sales history for a reliable forecast. "
                f"You have {n_history_days} days."
            ),
        }

    data_quality_flag = "early_estimate" if n_history_days < 60 else None

    forecast_days = forecast_weeks * 7
    daily["rolling_7"] = daily["revenue"].rolling(7, min_periods=1).mean()
    last_date = daily["date_only"].max()
    avg_daily = daily["revenue"].mean()
    slope = 0

    # statsforecast path — requires 60+ days for reliable seasonal decomposition
    use_statsforecast = False
    if _STATSFORECAST_AVAILABLE and n_history_days >= 60:
        try:
            sf_df = daily[["date_only", "revenue"]].rename(
                columns={"date_only": "ds", "revenue": "y"}
            ).copy()
            sf_df.insert(0, "unique_id", "total")
            sf = _StatsForecast(models=[_AutoARIMA(), _AutoETS()], freq="D", n_jobs=1)
            sf.fit(sf_df)
            fcast = sf.predict(h=forecast_days, level=[80])
            future_dates = pd.DatetimeIndex(fcast["ds"])
            mid_cols = [c for c in fcast.columns if c not in ("unique_id", "ds") and "-lo-" not in c and "-hi-" not in c]
            lo_cols  = [c for c in fcast.columns if "-lo-80" in c]
            hi_cols  = [c for c in fcast.columns if "-hi-80" in c]
            fcst_mid   = np.maximum(fcast[mid_cols].mean(axis=1).values, 0)
            fcst_lower = np.maximum(fcast[lo_cols].min(axis=1).values, 0) if lo_cols else fcst_mid * 0.85
            fcst_upper = np.maximum(fcast[hi_cols].max(axis=1).values, 0) if hi_cols else fcst_mid * 1.15
            if fcst_mid.sum() == 0 and daily["revenue"].sum() > 0:
                use_statsforecast = False
            else:
                _n_history_days = len(daily)
                if _n_history_days < 60:
                    _ci_multiplier = max(1.0, 60 / _n_history_days)
                    _ci_center = fcst_mid
                    fcst_lower = np.maximum(_ci_center - (_ci_center - fcst_lower) * _ci_multiplier, 0)
                    fcst_upper = _ci_center + (fcst_upper - _ci_center) * _ci_multiplier
                slope = float((fcst_mid[-1] - fcst_mid[0]) / max(len(fcst_mid) - 1, 1)) if len(fcst_mid) >= 2 else 0.0
                use_statsforecast = True
        except Exception:
            use_statsforecast = False

    # Prophet path — requires 60+ days for reliable seasonality fitting
    use_prophet = not use_statsforecast and _PROPHET_AVAILABLE and n_history_days >= 60
    if use_prophet:
        logging.getLogger("prophet").setLevel(logging.WARNING)
        logging.getLogger("cmdstanpy").setLevel(logging.WARNING)
        prophet_df = daily[["date_only", "revenue"]].rename(
            columns={"date_only": "ds", "revenue": "y"}
        ).copy()
        date_span = (last_date - daily["date_only"].min()).days
        q01 = prophet_df["y"].quantile(0.01)
        q99 = prophet_df["y"].quantile(0.99)
        prophet_df["y"] = prophet_df["y"].clip(lower=q01, upper=q99)
        try:
            m = _Prophet(
                weekly_seasonality=True,
                yearly_seasonality=date_span >= 365,
                daily_seasonality=False,
                interval_width=0.8,
                uncertainty_samples=500,
                changepoint_prior_scale=0.15 if date_span < 30 else (0.20 if date_span < 60 else 0.25),
                seasonality_prior_scale=10,
            )
            m.add_seasonality(name="monthly", period=30.5, fourier_order=5)
            m.fit(prophet_df)
            future = m.make_future_dataframe(periods=forecast_days)
            forecast = m.predict(future)
            future_fc = forecast[forecast["ds"] > last_date].copy()
            future_dates = pd.DatetimeIndex(future_fc["ds"])
            fcst_mid    = np.maximum(future_fc["yhat"].values, 0)
            fcst_upper  = np.maximum(future_fc["yhat_upper"].values, 0)
            fcst_lower  = np.maximum(future_fc["yhat_lower"].values, 0)
            _n_history_days = len(daily)
            if _n_history_days < 60:
                _ci_multiplier = max(1.0, 60 / _n_history_days)
                _ci_center = fcst_mid
                fcst_lower = np.maximum(_ci_center - (_ci_center - fcst_lower) * _ci_multiplier, 0)
                fcst_upper = _ci_center + (fcst_upper - _ci_center) * _ci_multiplier
            hist_fc = forecast[forecast["ds"] <= last_date]
            if len(hist_fc) >= 2:
                slope = (hist_fc["trend"].iloc[-1] - hist_fc["trend"].iloc[0]) / max(len(hist_fc) - 1, 1)
            else:
                slope = 0.0
        except Exception:
            use_prophet = False

    # Linear + day-of-week seasonal fallback
    if not use_prophet and not use_statsforecast:
        try:
            _days = daily["days_since_start"].values.astype(float)
            _rev  = daily["revenue"].values.astype(float)
            _half_life = max(len(_days) / 3, 7)
            _weights = np.exp(np.log(2) * (_days - _days[-1]) / _half_life)
            slope, intercept = np.polyfit(_days, _rev, 1, w=_weights)
        except Exception:
            slope, intercept = 0.0, float(daily["revenue"].mean())
        trend_vals = slope * daily["days_since_start"].values + intercept
        std_resid  = (daily["revenue"].values - trend_vals).std()

        daily["dow"] = daily["date_only"].dt.dayofweek
        dow_factors = (
            daily.groupby("dow")["revenue"].mean() / avg_daily
            if avg_daily > 0 else pd.Series(1.0, index=range(7))
        ).reindex(range(7), fill_value=1.0)

        last_day = daily["days_since_start"].max()
        future_days_arr = np.arange(last_day + 1, last_day + forecast_days + 1)
        future_dates    = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=forecast_days)

        seasonal   = np.array([dow_factors.iloc[d.dayofweek] if d.dayofweek in dow_factors.index else 1.0 for d in future_dates])
        fcst_mid   = np.maximum(slope * future_days_arr + intercept, 0) * seasonal
        n_hist = max(len(daily), 1)
        raw_scale = np.sqrt(np.arange(1, forecast_days + 1) / n_hist)
        horizon_scale = raw_scale - raw_scale[0]
        fcst_upper = fcst_mid + std_resid * (1 + horizon_scale)
        fcst_lower = np.maximum(fcst_mid - std_resid * (1 + horizon_scale), 0)

        _n_history_days = len(daily)
        if _n_history_days < 60:
            _ci_multiplier = max(1.0, 60 / _n_history_days)
            _ci_center = fcst_mid
            fcst_lower = np.maximum(_ci_center - (_ci_center - fcst_lower) * _ci_multiplier, 0)
            fcst_upper = _ci_center + (fcst_upper - _ci_center) * _ci_multiplier

    # Determine trend
    slope_pct = slope / avg_daily * 100 if avg_daily > 0 else 0
    trend = "upward" if slope_pct > 0.5 else ("downward" if slope_pct < -0.5 else "flat")

    # Build forecast points
    forecast_points = []
    for i in range(len(future_dates)):
        forecast_points.append({
            "date": str(future_dates[i].date()),
            "predicted": round(float(fcst_mid[i]), 2),
            "lower": round(float(fcst_lower[i]), 2),
            "upper": round(float(fcst_upper[i]), 2),
        })

    return {
        "trend": trend,
        "forecast_points": forecast_points,
        "avg_daily": round(float(avg_daily), 2),
        "slope_pct": round(float(slope_pct), 2),
        "data_quality_flag": data_quality_flag,
    }
