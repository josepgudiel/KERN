"""Pydantic request/response models for all endpoints."""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any


class UploadResponse(BaseModel):
    ok: bool
    rows: int
    date_range: dict | None = None
    products: list[str]
    columns_detected: dict[str, str | None]
    has_dates: bool
    has_quantity: bool
    has_price: bool
    currency: str = "$"
    session_id: str
    filename: str | None = None
    warning: str | None = None
    gross_margin: float = 0.65
    margin_source: str = "estimated"  # "estimated" or "provided"
    has_cost_data: bool = False
    cost_column_name: str | None = None


class MetricsBlock(BaseModel):
    total_revenue: float
    total_orders: int
    avg_order_value: float
    wow_pct: float | None = None
    unique_products: int
    wow_stale_note: str | None = None


class HealthBrief(BaseModel):
    paragraph_1: str = ""
    paragraph_2: str = ""


class ProofKeyMetric(BaseModel):
    name: str
    value: float | None = None
    interpretation: str | None = None


class ProofDateRange(BaseModel):
    start: str | None = None
    end: str | None = None
    display: str = ""


class ProofConfidence(BaseModel):
    tier: str  # "high" | "moderate" | "low"
    color: str  # "green" | "amber" | "red"


class Proof(BaseModel):
    sample_size: int = 0
    date_range: ProofDateRange = ProofDateRange()
    key_metric: ProofKeyMetric = ProofKeyMetric(name="")
    confidence: ProofConfidence = ProofConfidence(tier="moderate", color="amber")


class Recommendation(BaseModel):
    id: str
    rec_type: str
    urgency_label: str
    urgency_score: int
    title: str
    body: str
    see_why: str
    confidence: str  # "high" | "moderate"
    transaction_count: int
    product: str
    product_b: str | None = None
    generated_at: str
    impact_estimate: float | None = None
    margin_pct: float | None = None      # Margin used in impact calculation
    margin_source: str | None = None     # "estimated" or "provided"
    proof: Proof | None = None


class ActionCenterResponse(BaseModel):
    metrics: MetricsBlock
    health_brief: HealthBrief | None = None
    recommendations: list[Recommendation] = []
    data_confidence_badge: str = ""


class ClusterGroup(BaseModel):
    label: str
    products: list[str]
    avg_revenue: float
    avg_quantity: float
    action: str


class RisingStar(BaseModel):
    product: str
    growth_pct: float
    recent_revenue: float


class DecliningProduct(BaseModel):
    product: str
    decline_pct: float
    recent_revenue: float


class BasketRule(BaseModel):
    antecedent: str
    consequent: str
    support_pct: float
    confidence_pct: float
    lift: float


class WhatsSellingResponse(BaseModel):
    clusters: list[ClusterGroup] = []
    rising_stars: list[RisingStar] = []
    declining_products: list[DecliningProduct] = []
    basket_rules: list[BasketRule] = []
    basket_info: str | None = None
    warning: str | None = None


class DayOfWeekEntry(BaseModel):
    day: str
    avg_revenue: float
    avg_orders: float


class WhenToStaffResponse(BaseModel):
    has_dates: bool
    day_of_week: list[DayOfWeekEntry] = []
    peak_day: str | None = None
    slowest_day: str | None = None
    staffing_recommendation: str | None = None
    warning: str | None = None


class ForecastPoint(BaseModel):
    date: str
    predicted: float
    lower: float
    upper: float


class PerProductForecast(BaseModel):
    product: str
    trend: str
    predicted_weekly: float


class ForecastResponse(BaseModel):
    trend: str
    forecast_points: list[ForecastPoint] = []
    growth_actions: list[str] = []
    per_product_forecast: list[PerProductForecast] = []
    data_quality_flag: str | None = None
    warning: str | None = None


class AnomalyEntry(BaseModel):
    date: str
    date_label: str
    direction: str
    revenue: float
    z_score: float
    pct_above: float
    top_product: str
    auto_label: str


class AnomaliesResponse(BaseModel):
    anomalies: list[AnomalyEntry] = []
    warning: str | None = None


class AdvisorRequest(BaseModel):
    session_id: str
    message: str
    conversation_history: list[dict] = []
    business_profile: dict | None = None


class AdvisorResponse(BaseModel):
    reply: str


class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    error: str


# ── Pricing ──────────────────────────────────────────────────────────────────

class PriceRec(BaseModel):
    product: str
    action: str
    current_price: float
    suggested_price: float
    n_transactions: int
    reason: str
    elasticity_confidence: str | None = None
    reliability: str | None = None
    sensitivity_label: str | None = None


class PricingResponse(BaseModel):
    recommendations: list[PriceRec] = []
    has_data: bool = False
    warning: str | None = None


# ── Overview / Period Comparison ─────────────────────────────────────────────

class PeriodComparison(BaseModel):
    revenue_delta_pct: float
    orders_delta_pct: float
    aov_delta_pct: float
    top_risers: list[dict] = []
    top_fallers: list[dict] = []
    new_products: list[str] = []
    dropped_products: list[str] = []
    label_a: str
    label_b: str
    rev_a: float
    rev_b: float


class OverviewResponse(BaseModel):
    has_dates: bool
    wow_pct: float | None = None
    trend: str = "flat"
    insights: list[str] = []
    period_comparison: PeriodComparison | None = None
    anomalies: list[AnomalyEntry] = []
    warning: str | None = None


# ── Monthly Report ───────────────────────────────────────────────────────────

class ReportRequest(BaseModel):
    session_id: str
    business_profile: dict | None = None


class ReportResponse(BaseModel):
    report: str
    period_label: str


# ── Dismiss ───────────────────────────────────────────────────────────────────

class DismissRequest(BaseModel):
    session_id: str
    rec_id: str
