"""FastAPI backend for Analytic — all routes."""
from __future__ import annotations

import datetime
import io
import json
import os
import uuid

import numpy as np
import pandas as pd
import redis
from dotenv import load_dotenv
from session_utils import serialize_session, deserialize_session
from fastapi import FastAPI, File, UploadFile, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

load_dotenv()

from db import init_db, is_db_available, get_db_session, Upload, DBSession, Dismissal

from engine.data_loader import prepare_data, _load_raw, _detect_columns
from engine.clusters import _get_product_clusters
from engine.insights import (
    _detect_overview_insights, _find_rising_stars,
    _find_declining_products, _derive_period_label,
)
from engine.action_center import _growth_actions
from engine.recommendations import build_recommendations
from engine.forecast import compute_revenue_forecast, _per_product_forecast
from engine.anomaly import detect_anomalies
from engine.apriori import _compute_basket_rules
from engine.pricing import _get_price_recommendations
from engine.safety import _has_dates, _build_data_confidence_badge
from engine.pricing import _get_price_recommendations
from engine.insights import _compare_periods, _derive_period_label
from engine.demo import _generate_demo_df, _generate_retail_demo_df
from ai.groq import (
    _generate_health_brief, generate_advisor_reply, _generate_narrative_report,
)
from models.schemas import (
    UploadResponse, ActionCenterResponse, MetricsBlock, HealthBrief,
    Recommendation, WhatsSellingResponse, ClusterGroup, RisingStar,
    DecliningProduct, BasketRule, WhenToStaffResponse, DayOfWeekEntry,
    ForecastResponse, ForecastPoint, PerProductForecast,
    AnomaliesResponse, AnomalyEntry, AdvisorRequest, AdvisorResponse,
    HealthResponse, ErrorResponse,
    PricingResponse, PriceRec,
    OverviewResponse, PeriodComparison,
    ReportRequest, ReportResponse,
    DismissRequest,
)


# ─── App setup ──────────────────────────────────────────────────────────────

app = FastAPI(title="Analytic API", version="1.0.0")

# Initialize PostgreSQL (graceful if unavailable)
init_db()

# M7: CORS restricted for production
_frontend_origin = os.environ.get("FRONTEND_ORIGIN", "")
_allow_origins = (
    [_frontend_origin]
    if _frontend_origin
    else ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Redis session manager ───────────────────────────────────────────────────

class RedisSessionManager:
    def __init__(self, redis_url: str, ttl_hours: int = 2):
        self._ttl = ttl_hours * 3600
        self._client = redis.from_url(redis_url, decode_responses=False)

    def _key(self, session_id: str) -> str:
        return f"session:{session_id}"

    def _pack(self, data: dict) -> bytes:
        return serialize_session(data)

    def _unpack(self, raw: bytes) -> dict:
        return deserialize_session(raw)

    def store_session(self, session_id: str, data: dict) -> None:
        self._client.setex(self._key(session_id), self._ttl, self._pack(data))

    def get_session(self, session_id: str) -> dict:
        raw = self._client.get(self._key(session_id))
        if raw is None:
            raise KeyError(session_id)
        session = self._unpack(raw)
        session["last_accessed"] = pd.Timestamp.now().isoformat()
        self._client.setex(self._key(session_id), self._ttl, self._pack(session))
        return session

    def delete_session(self, session_id: str) -> None:
        self._client.delete(self._key(session_id))

    def session_exists(self, session_id: str) -> bool:
        return bool(self._client.exists(self._key(session_id)))


_REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

import logging as _logging
logger = _logging.getLogger(__name__)

try:
    manager = RedisSessionManager(_REDIS_URL)
    manager._client.ping()
    logger.info(f"Redis connected at {_REDIS_URL}")
except (redis.ConnectionError, redis.TimeoutError, OSError) as _e:
    logger.warning(f"Redis unavailable at {_REDIS_URL}. Using in-memory sessions (data will be lost on restart). Error: {_e}")

    class InMemorySessionManager:
        def __init__(self):
            self.sessions = {}
            self.max_sessions = 1000

        def get_session(self, session_id: str) -> dict:
            if session_id not in self.sessions:
                raise KeyError(session_id)
            return self.sessions[session_id]

        def store_session(self, session_id: str, data: dict) -> None:
            if len(self.sessions) > self.max_sessions:
                oldest = next(iter(self.sessions))
                del self.sessions[oldest]
            self.sessions[session_id] = data

        def delete_session(self, session_id: str) -> None:
            self.sessions.pop(session_id, None)

        def session_exists(self, session_id: str) -> bool:
            return session_id in self.sessions

    manager = InMemorySessionManager()


@app.exception_handler(redis.ConnectionError)
async def _redis_connection_error_handler(request, exc):
    return JSONResponse(status_code=503, content={"error": "Session store unavailable"})


# ─── Serialization helper ───────────────────────────────────────────────────

def _py(val):
    """Convert numpy/pandas types to native Python for JSON serialization."""
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        return float(val)
    if isinstance(val, (np.bool_,)):
        return bool(val)
    if isinstance(val, (pd.Timestamp,)):
        return val.isoformat()
    if isinstance(val, (np.ndarray,)):
        return val.tolist()
    return val


def _get_session(session_id: str) -> dict:
    """Retrieve session or raise 404. Updates last_accessed timestamp."""
    try:
        return manager.get_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Session not found. Upload a file first.")


# ─── Routes ─────────────────────────────────────────────────────────────────

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse()


@app.post("/upload", response_model=UploadResponse)
async def upload(
    file: UploadFile = File(...),
    margin: float | None = Query(None, description="Gross margin as decimal (0.40 = 40%). If omitted, defaults to 0.65."),
):
    file_bytes = await file.read()
    file_name = file.filename or "upload.csv"

    # H1: File size limit: 50MB
    MAX_UPLOAD_BYTES = 50 * 1024 * 1024
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=400,
            detail="File too large. Maximum file size is 50MB."
        )

    raw_df = _load_raw(file_bytes, file_name)
    if raw_df is None or raw_df.empty:
        raise HTTPException(status_code=400, detail="Could not read the file. Try CSV or XLSX format.")

    df, warning = prepare_data(raw_df)
    if df is None:
        raise HTTPException(status_code=400, detail=warning or "No valid data after processing.")

    # H1: Row count limit: 200,000
    MAX_ROWS = 200_000
    if len(df) > MAX_ROWS:
        raise HTTPException(
            status_code=400,
            detail=f"Too many rows ({len(df):,}). Maximum is 200,000 rows. Try filtering your export to a recent date range."
        )

    session_id = str(uuid.uuid4())

    # Detect cost columns
    _cost_keywords = ("cost", "cogs", "expense", "unit_cost", "cost_per_unit")
    cost_cols = [c for c in df.columns if any(k in c.lower() for k in _cost_keywords)]
    has_cost_data = len(cost_cols) > 0
    cost_column_name = cost_cols[0] if cost_cols else None

    # Resolve margin
    if margin is not None:
        if not (0.05 <= margin <= 0.99):
            raise HTTPException(status_code=400, detail="Margin must be between 5% and 99% (e.g., 0.40 for 40%).")
        gross_margin = margin
        margin_source = "provided"
    else:
        gross_margin = 0.65
        margin_source = "estimated"

    # Log upload to PostgreSQL for persistence + audit trail
    db_session = get_db_session()
    if db_session:
        try:
            import hashlib
            from datetime import timedelta
            data_hash = hashlib.sha256(file_bytes[:1000]).hexdigest()  # Hash first 1KB

            upload_record = Upload(
                id=session_id,
                session_id=session_id,
                file_name=file_name,
                row_count=len(df),
                product_count=len(df["product"].unique()) if "product" in df.columns else 0,
                date_range_start=df["date"].min() if "date" in df.columns and len(df) > 0 else None,
                date_range_end=df["date"].max() if "date" in df.columns and len(df) > 0 else None,
                has_dates=_has_dates(df),
                data_hash=data_hash,
                expires_at=pd.Timestamp.utcnow() + pd.Timedelta(hours=2),
                gross_margin=gross_margin,
                margin_source=margin_source,
                has_cost_data=has_cost_data,
                cost_column_name=cost_column_name,
            )
            db_session.add(upload_record)
            db_session.commit()
            logger.info(f"Logged upload {session_id} to PostgreSQL")
        except Exception as e:
            logger.warning(f"Failed to log upload to DB: {e}")
            db_session.rollback()
        finally:
            db_session.close()

    columns_detected = _detect_columns(raw_df)
    has_dates = _has_dates(df)

    # Detect currency from raw data
    currency = "$"
    for col_name in raw_df.columns:
        sample = raw_df[col_name].dropna().astype(str).head(20)
        for val in sample:
            if "€" in val:
                currency = "€"
                break
            if "£" in val:
                currency = "£"
                break

    manager.store_session(session_id, {
        "df": df,
        "raw_cols": raw_df.columns.tolist(),
        "currency": currency,
        "gross_margin": gross_margin,
        "margin_source": margin_source,
        "has_cost_data": has_cost_data,
        "cost_column_name": cost_column_name,
        "uploaded_at": pd.Timestamp.now().isoformat(),
        "last_accessed": pd.Timestamp.now().isoformat(),
    })

    date_range = None
    if has_dates:
        date_range = {
            "min": str(df["date"].min().date()),
            "max": str(df["date"].max().date()),
        }

    return UploadResponse(
        ok=True,
        rows=len(df),
        date_range=date_range,
        products=sorted(df["product"].unique().tolist()),
        columns_detected={k: v for k, v in columns_detected.items()},
        has_dates=bool(has_dates),
        has_quantity=bool("quantity" in df.columns and (df["quantity"] != 1).any()),
        has_price=bool(columns_detected.get("unit_price") is not None),
        currency=currency,
        session_id=session_id,
        filename=file_name,
        warning=warning,
        gross_margin=gross_margin,
        margin_source=margin_source,
        has_cost_data=has_cost_data,
        cost_column_name=cost_column_name,
    )


# C4: Demo data endpoint
@app.get("/demo")
async def get_demo_data(dataset: str = "coffee_shop"):
    """Generate built-in demo data and return a session_id, same as /upload."""
    try:
        if dataset == "retail":
            raw_df = _generate_retail_demo_df()
            filename = "demo_retail_store.csv"
        else:
            raw_df = _generate_demo_df()
            filename = "demo_coffee_shop.csv"

        df, error = prepare_data(raw_df)
        if df is None:
            raise HTTPException(status_code=500, detail=f"Demo data preparation failed: {error}")

        session_id = str(uuid.uuid4())
        manager.store_session(session_id, {
            "df": df,
            "raw_df": raw_df,
            "raw_cols": raw_df.columns.tolist(),
            "currency": "$",
            "filename": filename,
            "uploaded_at": pd.Timestamp.now().isoformat(),
            "last_accessed": pd.Timestamp.now().isoformat(),
        })

        return {
            "ok": True,
            "session_id": session_id,
            "rows": len(df),
            "date_range": {
                "min": str(df["date"].min().date()),
                "max": str(df["date"].max().date()),
            } if "date" in df.columns else None,
            "products": df["product"].unique().tolist()[:50],
            "columns_detected": {},
            "has_dates": "date" in df.columns,
            "has_quantity": "quantity" in df.columns,
            "has_price": "unit_price" in df.columns,
            "currency": "$",
            "filename": filename,
            "warning": None,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/demo-data/{business_type}")
async def get_demo_csv(business_type: str):
    """Return demo data as a downloadable CSV so the frontend can upload it via the normal /upload flow."""
    if business_type == "retail":
        df = _generate_retail_demo_df()
        filename = "demo_retail_store.csv"
    else:
        df = _generate_demo_df()
        filename = "demo_coffee_shop.csv"
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    return StreamingResponse(
        io.BytesIO(csv_bytes),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/action-center")
def action_center(session_id: str = Query(...)):
    session = _get_session(session_id)
    df = session["df"]
    cur = session.get("currency", "$")

    # H4: Cache product clusters in session
    if "product_clusters" not in session:
        session["product_clusters"] = _get_product_clusters(df)
        manager.store_session(session_id, session)
    product_clusters = session["product_clusters"]

    # Metrics
    total_revenue = float(df["revenue"].sum())
    total_orders = len(df)
    avg_order = total_revenue / total_orders if total_orders else 0
    insights = _detect_overview_insights(df, currency=cur)
    wow = insights.get("wow_pct")

    # Suppress WoW if data is older than 30 days — the signal is not current
    _days_stale = (
        (pd.Timestamp.now() - df["date"].max()).days
        if "date" in df.columns and not df["date"].isna().all()
        else None
    )
    if _days_stale is not None and _days_stale > 30:
        wow = None
        wow_stale_note = f"Data is {_days_stale} days old — week-over-week unavailable"
    else:
        wow_stale_note = None

    metrics = {
        "total_revenue": round(total_revenue, 2),
        "total_orders": total_orders,
        "avg_order_value": round(avg_order, 2),
        "wow_pct": _py(wow) if wow is not None else None,
        "unique_products": int(df["product"].nunique()),
        "wow_stale_note": wow_stale_note,
    }

    # Health brief
    health_brief = _generate_health_brief(df, product_clusters, currency=cur)

    # Rebuilt recommendation engine — statistical foundation
    margin = float(session.get("gross_margin", 0.65))
    margin_source = session.get("margin_source", "estimated")
    recommendations = build_recommendations(df, currency=cur, margin=margin, margin_source=margin_source)

    badge = _build_data_confidence_badge(df)

    return {
        "metrics": metrics,
        "health_brief": health_brief,
        "recommendations": recommendations,
        "data_confidence_badge": badge,
    }


@app.get("/whats-selling")
def whats_selling(session_id: str = Query(...)):
    session = _get_session(session_id)
    df = session["df"]
    cur = session.get("currency", "$")

    # H4: Cache product clusters in session
    if "product_clusters" not in session:
        session["product_clusters"] = _get_product_clusters(df)
        manager.store_session(session_id, session)
    product_clusters = session["product_clusters"]

    clusters_out = []
    if product_clusters is not None:
        advice = {
            "Stars": "Protect and promote these — they carry your revenue.",
            "Cash Cows": "Try bundling with a pricier item to lift order value.",
            "Hidden Gems": "Promote these — try a daily special or staff recommendation.",
            "Low Activity": "Review before cutting — check availability and visibility.",
        }
        for cat in ["Stars", "Cash Cows", "Hidden Gems", "Low Activity"]:
            sub = product_clusters[product_clusters["category"] == cat]
            if sub.empty:
                continue
            clusters_out.append({
                "label": cat,
                "products": sub["product"].tolist(),
                "avg_revenue": round(float(sub["revenue"].mean()), 2),
                "avg_quantity": round(float(sub["quantity"].mean()), 2),
                "action": advice.get(cat, ""),
            })

    # Rising stars
    rising_out = []
    rising = _find_rising_stars(df)
    if rising is not None:
        for _, row in rising.iterrows():
            rising_out.append({
                "product": row["product"],
                "growth_pct": round(float(row["growth_pct"]), 1),
                "recent_revenue": round(float(row["recent_rev"]), 2),
            })

    # Declining
    declining_out = []
    declining = _find_declining_products(df)
    for item in declining[:5]:
        declining_out.append({
            "product": item["product"],
            "decline_pct": round(float(-item["decline_pct"]), 1),
            "recent_revenue": round(float(item["recent_rev"]), 2),
        })

    # Basket rules
    basket_out = []
    basket_info = None
    _, rules, err, _ = _compute_basket_rules(df)
    if err == "single_item_dominated":
        basket_info = "Bundle suggestions aren't available yet — they work best when customers regularly buy multiple items together."
    elif rules is not None and not rules.empty:
        for _, rule in rules.head(10).iterrows():
            basket_out.append({
                "antecedent": rule["antecedent"],
                "consequent": rule["consequent"],
                "support_pct": round(float(rule["support"]) * 100, 1),
                "confidence_pct": round(float(rule["confidence"]) * 100, 1),
                "lift": round(float(rule["lift"]), 2),
            })

    return {
        "clusters": clusters_out,
        "rising_stars": rising_out,
        "declining_products": declining_out,
        "basket_rules": basket_out,
        "basket_info": basket_info,
    }


@app.get("/when-to-staff")
def when_to_staff(session_id: str = Query(...)):
    session = _get_session(session_id)
    df = session["df"]

    if not _has_dates(df):
        return {
            "has_dates": False,
            "day_of_week": [],
            "peak_day": None,
            "slowest_day": None,
            "staffing_recommendation": None,
            "warning": "No date column found in the data.",
        }

    dfc = df.copy()
    dfc["day_name"] = dfc["date"].dt.day_name()
    dfc["dow"] = dfc["date"].dt.dayofweek

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    by_day = dfc.groupby("day_name").agg(
        total_revenue=("revenue", "sum"),
        total_orders=("revenue", "count"),
    )

    n_weeks = max((dfc["date"].max() - dfc["date"].min()).days / 7, 1)

    day_of_week = []
    for day in day_order:
        if day in by_day.index:
            day_of_week.append({
                "day": day,
                "avg_revenue": round(float(by_day.loc[day, "total_revenue"] / n_weeks), 2),
                "avg_orders": round(float(by_day.loc[day, "total_orders"] / n_weeks), 1),
            })

    peak_day = by_day["total_revenue"].idxmax() if not by_day.empty else None
    slowest_day = by_day["total_revenue"].idxmin() if not by_day.empty else None

    staffing_rec = None
    if peak_day and slowest_day and peak_day != slowest_day:
        staffing_rec = (
            f"{peak_day} is your peak — schedule your strongest staff. "
            f"{slowest_day} is your slowest — consider reduced hours or a targeted promotion."
        )

    return {
        "has_dates": True,
        "day_of_week": day_of_week,
        "peak_day": peak_day,
        "slowest_day": slowest_day,
        "staffing_recommendation": staffing_rec,
    }


@app.get("/forecast")
def forecast(session_id: str = Query(...), weeks: int = Query(default=4, ge=1, le=12)):
    session = _get_session(session_id)
    df = session["df"]
    cur = session.get("currency", "$")

    if not _has_dates(df):
        return {
            "trend": "unknown",
            "forecast_points": [],
            "growth_actions": [],
            "per_product_forecast": [],
            "warning": "No date column found.",
        }

    result = compute_revenue_forecast(df, forecast_weeks=weeks)
    if result.get("status") == "insufficient_data" or "error" in result:
        return {
            "trend": "unknown",
            "forecast_points": [],
            "growth_actions": [],
            "per_product_forecast": [],
            "data_quality_flag": "insufficient_data" if result.get("status") == "insufficient_data" else None,
            "warning": result.get("warning", result.get("error")),
        }

    # M6: Cache forecast result in session for advisor context
    session["cached_forecast"] = {
        "trend": result["trend"],
        "growth_actions": [],
    }

    # Growth actions
    insights = _detect_overview_insights(df, currency=cur)
    avg_daily = result.get("avg_daily", 0)
    growth_pct = abs(result.get("slope_pct", 0))
    wow = insights.get("wow_pct")
    actions = _growth_actions(
        trend=result["trend"],
        df=df,
        growth_pct=growth_pct,
        avg_daily=avg_daily,
        forecast_weeks=weeks,
        wow=wow,
        currency=cur,
    )

    # Update cached forecast with growth actions
    session["cached_forecast"]["growth_actions"] = actions
    manager.store_session(session_id, session)

    # Per-product forecast
    pp = _per_product_forecast(df, weeks)
    pp_out = []
    if pp:
        for item in pp:
            pp_out.append({
                "product": item["product"],
                "trend": item["direction"],
                "predicted_weekly": _py(item["current_weekly_avg"]),
            })

    return {
        "trend": result["trend"],
        "forecast_points": result["forecast_points"],
        "growth_actions": actions,
        "per_product_forecast": pp_out,
        "data_quality_flag": result.get("data_quality_flag"),
    }


@app.get("/anomalies")
def anomalies(session_id: str = Query(...)):
    session = _get_session(session_id)
    df = session["df"]

    if not _has_dates(df):
        return {"anomalies": [], "warning": "No date column found."}

    result = detect_anomalies(df)
    return {"anomalies": result}


@app.post("/advisor")
def advisor(req: AdvisorRequest):
    session = _get_session(req.session_id)
    df = session["df"]
    cur = session.get("currency", "$")

    # H4: Cache product clusters in session
    if "product_clusters" not in session:
        session["product_clusters"] = _get_product_clusters(df)
        manager.store_session(req.session_id, session)
    product_clusters = session["product_clusters"]

    reply = generate_advisor_reply(
        df=df,
        product_clusters=product_clusters,
        message=req.message,
        conversation_history=req.conversation_history,
        business_profile=req.business_profile,
        currency=cur,
    )

    return {"reply": reply}


@app.get("/pricing")
def pricing(session_id: str = Query(...)):
    session = _get_session(session_id)
    df = session["df"]
    cur = session.get("currency", "$")

    recs = _get_price_recommendations(df, currency=cur)

    if not recs:
        return PricingResponse(
            has_data=False,
            warning="Not enough data to generate pricing recommendations. Need at least 15 transactions per product.",
        )

    out = []
    for r in recs:
        out.append(PriceRec(
            product=r["product"],
            action=r["action"],
            current_price=round(float(r["current"]), 2),
            suggested_price=round(float(r["suggested"]), 2),
            n_transactions=int(r["n_txn"]),
            reason=r["reason"],
            elasticity_confidence=r.get("elasticity_confidence"),
            reliability=r.get("reliability"),
            sensitivity_label=r.get("sensitivity_label"),
        ))

    return PricingResponse(recommendations=out, has_data=True)


@app.get("/overview")
def overview(session_id: str = Query(...)):
    session = _get_session(session_id)
    df = session["df"]
    cur = session.get("currency", "$")

    from engine.insights import _detect_overview_insights
    from engine.anomaly import detect_anomalies

    insights_data = _detect_overview_insights(df, currency=cur)
    has_dates = bool(insights_data.get("has_dates"))
    warning = None

    # Period comparison — last 30 days vs prior 30 days from same dataset
    period_comparison = None
    if has_dates:
        max_date = df["date"].max()
        last30_start = max_date - pd.Timedelta(days=29)
        prior30_end  = max_date - pd.Timedelta(days=30)
        prior30_start = max_date - pd.Timedelta(days=59)

        df_last30 = df[df["date"] >= last30_start]
        df_prior30 = df[(df["date"] >= prior30_start) & (df["date"] <= prior30_end)]

        if len(df_last30) >= 30 and len(df_prior30) >= 30:
            cmp = _compare_periods(df_prior30, df_last30, "Prior 30 days", "Last 30 days")
            if cmp:
                period_comparison = PeriodComparison(
                    revenue_delta_pct=round(float(cmp["revenue_delta_pct"]), 1),
                    orders_delta_pct=round(float(cmp["orders_delta_pct"]), 1),
                    aov_delta_pct=round(float(cmp["aov_delta_pct"]), 1),
                    top_risers=[{"product": r["product"], "delta_pct": round(float(r["delta_pct"]), 1), "rev_b": round(float(r["rev_b"]), 2)} for r in cmp["top_risers"]],
                    top_fallers=[{"product": r["product"], "delta_pct": round(float(r["delta_pct"]), 1), "rev_b": round(float(r["rev_b"]), 2)} for r in cmp["top_fallers"]],
                    new_products=cmp["new_products"],
                    dropped_products=cmp["dropped_products"],
                    label_a=cmp["label_a"],
                    label_b=cmp["label_b"],
                    rev_a=round(float(cmp["rev_a"]), 2),
                    rev_b=round(float(cmp["rev_b"]), 2),
                )
        else:
            warning = "Need at least 60 days of data for period comparison."

    # Anomalies
    anomaly_entries = []
    if has_dates:
        raw_anomalies = detect_anomalies(df)
        for a in raw_anomalies:
            anomaly_entries.append(AnomalyEntry(
                date=a["date"],
                date_label=a.get("date_label", a["date"]),
                direction=a["direction"],
                revenue=round(float(a["revenue"]), 2),
                z_score=round(float(a["z_score"]), 1),
                pct_above=round(float(a.get("pct_above", 0)), 1),
                top_product=a.get("top_product", ""),
                auto_label=a.get("auto_label", ""),
            ))

    return OverviewResponse(
        has_dates=has_dates,
        wow_pct=_py(insights_data.get("wow_pct")),
        trend=insights_data.get("trend", "flat"),
        insights=insights_data.get("insights", []),
        period_comparison=period_comparison,
        anomalies=anomaly_entries,
        warning=warning,
    )


@app.post("/report")
def report(req: ReportRequest):
    session = _get_session(req.session_id)
    df = session["df"]
    cur = session.get("currency", "$")

    if "product_clusters" not in session:
        session["product_clusters"] = _get_product_clusters(df)
        manager.store_session(req.session_id, session)
    product_clusters = session["product_clusters"]

    period_label = _derive_period_label(df)

    text = _generate_narrative_report(
        df=df,
        product_clusters=product_clusters,
        period_label=period_label,
        currency=cur,
        business_profile=req.business_profile,
    )

    if not text:
        raise HTTPException(status_code=503, detail="AI report unavailable — check that GROQ_API_KEY is set.")

    return ReportResponse(report=text, period_label=period_label)


@app.get("/data-summary")
def data_summary(session_id: str = Query(...)):
    session = _get_session(session_id)
    df = session["df"]
    cur = session.get("currency", "$")
    from ai.prompts import build_data_summary
    summary = build_data_summary(df, currency=cur)
    return summary


@app.post("/dismiss")
def dismiss_recommendation(req: DismissRequest):
    session = _get_session(req.session_id)
    if "dismissed_recs" not in session:
        session["dismissed_recs"] = set()
    session["dismissed_recs"].add(req.rec_id)
    manager.store_session(req.session_id, session)

    # Log dismissal to PostgreSQL for feedback loop
    db_session = get_db_session()
    if db_session:
        try:
            dismissal = Dismissal(
                id=str(uuid.uuid4()),
                session_id=req.session_id,
                upload_id=req.session_id,  # In this case, upload_id == session_id
                rec_id=req.rec_id,
                rec_type=req.rec_id.split("_")[0] if "_" in req.rec_id else None,
            )
            db_session.add(dismissal)
            db_session.commit()
            logger.info(f"Logged dismissal {req.rec_id} to PostgreSQL")
        except Exception as e:
            logger.warning(f"Failed to log dismissal to DB: {e}")
            db_session.rollback()
        finally:
            db_session.close()

    return {"ok": True}


@app.get("/dismissed")
def get_dismissed(session_id: str = Query(...)):
    session = _get_session(session_id)
    return {"dismissed": list(session.get("dismissed_recs", set()))}
