import type {
  UploadResponse,
  ActionCenterResponse,
  WhatsSelling,
  StaffingResponse,
  ForecastResponse,
  AnomaliesResponse,
  AdvisorRequest,
  AdvisorResponse,
  PricingResponse,
  OverviewResponse,
  ReportResponse,
  DataSummaryResponse,
} from "@/types";

const BASE = "/api";

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const text = await res.text().catch(() => "Unknown error");
    throw new Error(`API error ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export async function uploadFile(file: File, margin?: number): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const url = margin != null
    ? `${BASE}/upload?margin=${margin}`
    : `${BASE}/upload`;
  return request<UploadResponse>(url, {
    method: "POST",
    body: form,
  });
}

export async function getActionCenter(sessionId: string): Promise<ActionCenterResponse> {
  return request<ActionCenterResponse>(`${BASE}/action-center?session_id=${sessionId}`);
}

export async function getWhatsSelling(sessionId: string): Promise<WhatsSelling> {
  return request<WhatsSelling>(`${BASE}/whats-selling?session_id=${sessionId}`);
}

export async function getWhenToStaff(sessionId: string): Promise<StaffingResponse> {
  return request<StaffingResponse>(`${BASE}/when-to-staff?session_id=${sessionId}`);
}

export async function getForecast(sessionId: string, weeks = 8): Promise<ForecastResponse> {
  return request<ForecastResponse>(`${BASE}/forecast?session_id=${sessionId}&weeks=${weeks}`);
}

export async function getAnomalies(sessionId: string): Promise<AnomaliesResponse> {
  return request<AnomaliesResponse>(`${BASE}/anomalies?session_id=${sessionId}`);
}

export async function postAdvisor(req: AdvisorRequest): Promise<AdvisorResponse> {
  return request<AdvisorResponse>(`${BASE}/advisor`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  });
}

export async function getDemo(dataset: 'coffee_shop' | 'retail'): Promise<UploadResponse> {
  const res = await fetch(`${BASE}/demo?dataset=${dataset}`);
  if (!res.ok) throw new Error('Failed to load demo data');
  return res.json();
}

export async function getPricing(sessionId: string): Promise<PricingResponse> {
  return request<PricingResponse>(`${BASE}/pricing?session_id=${sessionId}`);
}

export async function getOverview(sessionId: string): Promise<OverviewResponse> {
  return request<OverviewResponse>(`${BASE}/overview?session_id=${sessionId}`);
}

export async function postReport(sessionId: string, businessProfile?: Record<string, string>): Promise<ReportResponse> {
  return request<ReportResponse>(`${BASE}/report`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, business_profile: businessProfile ?? null }),
  });
}

export async function getDataSummary(sessionId: string): Promise<DataSummaryResponse> {
  return request<DataSummaryResponse>(`${BASE}/data-summary?session_id=${sessionId}`);
}

export async function dismissRecommendation(sessionId: string, recId: string): Promise<{ ok: boolean }> {
  return request<{ ok: boolean }>(`${BASE}/dismiss`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId, rec_id: recId }),
  });
}

export async function getDismissed(sessionId: string): Promise<{ dismissed: string[] }> {
  return request<{ dismissed: string[] }>(`${BASE}/dismissed?session_id=${sessionId}`);
}
