export interface UploadResponse {
  ok: boolean;
  session_id: string;
  rows: number;
  date_range: { min: string; max: string } | null;
  products: string[];
  columns_detected: Record<string, string>;
  has_dates: boolean;
  has_quantity: boolean;
  has_price: boolean;
  currency: string;
  filename?: string;
  warning?: string | null;
  gross_margin: number;
  margin_source: 'estimated' | 'provided';
  has_cost_data: boolean;
  cost_column_name?: string | null;
}

export interface ActionCenterResponse {
  metrics: {
    total_revenue: number;
    total_orders: number;
    avg_order_value: number;
    wow_pct: number | null;
    unique_products: number;
    wow_stale_note?: string | null;
  };
  health_brief: { paragraph_1: string; paragraph_2: string } | null;
  recommendations: Recommendation[];
  data_confidence_badge: string;
}

export interface ProofData {
  sample_size: number;
  date_range: {
    start: string | null;
    end: string | null;
    display: string;
  };
  key_metric: {
    name: string;
    value: number | null;
    interpretation?: string | null;
  };
  confidence: {
    tier: 'high' | 'moderate' | 'low';
    color: 'green' | 'amber' | 'red';
  };
}

export interface Recommendation {
  id: string;
  rec_type:
    | "pricing"
    | "declining"
    | "bundle"
    | "rising"
    | "dead_product"
    | "dow_opportunity"
    | "underpriced_rising";
  urgency_label: string;
  urgency_score: number;
  title: string;
  body: string;
  see_why: string;
  confidence: "high" | "moderate";
  transaction_count: number;
  product: string;
  product_b?: string;
  generated_at: string;
  impact_estimate?: number | null;
  margin_pct?: number | null;
  margin_source?: 'estimated' | 'provided' | null;
  proof?: ProofData | null;
}

export interface WhatsSelling {
  clusters: Cluster[];
  rising_stars: { product: string; growth_pct: number; recent_revenue: number }[];
  declining_products: { product: string; decline_pct: number; recent_revenue: number }[];
  basket_rules: BasketRule[];
  basket_info?: string | null;
}

export interface Cluster {
  label: string;
  products: string[];
  avg_revenue: number;
  avg_quantity: number;
  action: string;
}

export interface BasketRule {
  antecedent: string;
  consequent: string;
  support_pct: number;
  confidence_pct: number;
  lift: number;
}

export interface StaffingResponse {
  has_dates: boolean;
  day_of_week: { day: string; avg_revenue: number; avg_orders: number }[];
  peak_day: string | null;
  slowest_day: string | null;
  staffing_recommendation: string | null;
}

export interface ForecastResponse {
  trend: "upward" | "downward" | "flat";
  forecast_points: { date: string; predicted: number; lower: number; upper: number }[];
  growth_actions: string[];
  per_product_forecast: { product: string; trend: string; predicted_weekly: number }[];
  data_quality_flag?: string | null;
}

export interface AnomaliesResponse {
  anomalies: {
    date: string;
    date_label: string;
    direction: "spike" | "dip";
    revenue: number;
    z_score: number;
    pct_above: number;
    top_product: string;
    auto_label: string;
  }[];
}

export interface AdvisorRequest {
  session_id: string;
  message: string;
  conversation_history: { role: string; content: string }[];
  business_profile: Record<string, string>;
}

export interface AdvisorResponse {
  reply: string;
}

export interface PriceRec {
  product: string;
  action: string;
  current_price: number;
  suggested_price: number;
  n_transactions: number;
  reason: string;
  elasticity_confidence?: string | null;
  reliability?: string | null;
  sensitivity_label?: string | null;
}

export interface PricingResponse {
  recommendations: PriceRec[];
  has_data: boolean;
  warning?: string | null;
}

export interface PeriodComparison {
  revenue_delta_pct: number;
  orders_delta_pct: number;
  aov_delta_pct: number;
  top_risers: { product: string; delta_pct: number; rev_b: number }[];
  top_fallers: { product: string; delta_pct: number; rev_b: number }[];
  new_products: string[];
  dropped_products: string[];
  label_a: string;
  label_b: string;
  rev_a: number;
  rev_b: number;
}

export interface OverviewResponse {
  has_dates: boolean;
  wow_pct: number | null;
  trend: 'upward' | 'downward' | 'flat';
  insights: string[];
  period_comparison: PeriodComparison | null;
  anomalies: AnomaliesResponse['anomalies'];
  warning?: string | null;
}

export interface ReportResponse {
  report: string;
  period_label: string;
}

export interface DataSummaryResponse {
  date_range: string;
  total_transactions: number;
  top_products: string[];
  best_dow: string;
  anomalies: string[] | string;
  recent_trend: string;
}
