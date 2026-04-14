# What Recommendation Data is Already Available?

Audit performed 2026-04-05.

## Pricing Recommendations
- [x] Elasticity coefficient (Path A only, via log-log OLS)
- [x] R-squared and p-value
- [x] Sample size (transaction_count)
- [x] Date range (computed from product transactions)
- [x] Confidence tier (high if R² > 0.3, else moderate)
- [x] Price variation (n_price_points, min/max price)
- Path B (portfolio comparison): no elasticity — uses portfolio avg percentile instead

## Bundle Recommendations
- [x] Apriori lift
- [x] Apriori support (% of transactions)
- [x] Apriori confidence (attach rate)
- [x] Gap transactions (bought A without B)
- [x] Sample size
- [x] Date range (combined across both products)

## Declining Product Recommendations
- [x] Trend slope, R-squared, p-value
- [x] Percent change from peak
- [x] Consecutive declining weeks
- [x] Projected weeks to zero
- [x] Sample size
- [x] Date range

## Rising Product Recommendations
- [x] Trend slope, R-squared, p-value
- [x] Percent change
- [x] Rank movement (before → now)
- [x] Action type (underpriced / bundle / momentum)
- [x] Sample size
- [x] Date range

## Dead Product Recommendations
- [x] Sales previous 30 days vs last 30 days
- [x] Percent drop
- [x] Days since last sale
- [x] Sample size
- [x] Date range

## Day-of-Week Opportunity Recommendations
- [x] Peak day multiplier
- [x] Consistency percentage
- [x] Peak day name
- [x] Sample size
- [x] Date range

## What Was NOT Captured Before This Change?
- Date range per product (first/last transaction) — now computed via `data_utils.get_product_date_range`
- Structured `proof` object — all `_statistical_detail` fields were computed but stripped before sending to frontend

## Implementation Summary
All data was already computed in `_statistical_detail` dicts inside each rec builder.
The fix: `_build_proof_for_rec()` maps `_statistical_detail` into a standardised `proof` object
before the strip step, and includes it in the public response.

### Files Changed
- `backend/engine/data_utils.py` — NEW: date range helpers + `build_proof()` factory
- `backend/engine/recommendations.py` — Added `_build_proof_for_rec()`, included `proof` in output
- `backend/models/schemas.py` — Added `Proof`, `ProofKeyMetric`, `ProofDateRange`, `ProofConfidence` models
- `frontend/types/index.ts` — Added `ProofData` interface, `proof` field on `Recommendation`
- `frontend/components/RecommendationCard.tsx` — Collapsible proof layer with data grid
