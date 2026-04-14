# Model Confidence & Transparency Audit

> Based on full source code review of `backend/engine/`: pricing.py, forecast.py, clusters.py, anomaly.py, action_center.py, insights.py, safety.py

---

## Recommendation Filtering

| Signal | Gate | What happens if below threshold |
|--------|------|--------------------------------|
| Price recommendations | ≥ 20 txns/product (raise: 25) | Product silently excluded from recommendations |
| Forecast | ≥ 28 days history | Returns `insufficient_data` error; shown to user |
| Clustering | ≥ 4 products AND ≥ 20 total txns | Module returns `None`; page shows "Not enough data" |
| Anomaly detection | ≥ 14 days AND ≥ 10 days with 3+ txns | Returns empty list; no anomalies shown |
| Basket analysis | ≥ 50 txns with dates | Blocked entirely |
| Rising stars | Requires 60+ day history (prior_start needs to exist) | Returns `None`; no rising stars in Action Center |
| Declining products | Requires 60+ day history | Returns empty list; no "watch outs" for declines |

**Filtering quality**: Generally good — gates prevent noise-based recommendations. But the gates are **silent** for most modules: if pricing filtering removes 8 out of 18 products, the user sees 10 recommendations and has no idea that 8 were suppressed.

**User sees why filtered?**
- Forecast: ✅ Explicit "need 28+ days" message shown
- Pricing: ❌ Products below threshold are silently omitted
- Clustering: ✅ "Not enough data" message shown
- Rising stars: ❌ Silently absent if history < 60 days
- Declining products: ❌ Silently absent if history < 60 days

---

## Confidence Transparency

### Price Elasticity
- **P-value shown to user**: ❌ Hidden (only used internally as gate)
- **R² shown to user**: ❌ Hidden
- **n_transactions shown**: ⚠️ Shown in Pricing page card (`n_txn` field), not in Action Center
- **Confidence label shown**: ✅ "Strong signal" / "Worth testing" / "Not enough data yet" shown on Pricing page
- **Confidence in Action Center**: ✅ `confidence` field passed through; label displayed on cards

### Forecast
- **Model selection shown to user**: ❌ Hidden — user never knows if they got AutoARIMA, Prophet, or linear fallback
- **`data_quality_flag`**: ✅ "early_estimate" flag returned when < 60 days, but whether the frontend surfaces this is unclear
- **Confidence bands (lower/upper)**: ✅ Included in `forecast_points` — frontend should show these
- **"early_estimate" means**: CI bands are widened by factor of `60/n_history_days` — undisclosed to user

### Clustering
- **Silhouette score**: ✅ Computed and stored in `agg.attrs["silhouette_score"]` — but NOT returned in API response visible to user
- **K (number of clusters)**: ✅ `n_clusters` stored but not surfaced on frontend
- **Cluster stability note**: ❌ No instability warning shown if silhouette score is low

### Anomaly Detection
- **MAD threshold (z=2.5)**: ❌ Not shown to user; non-adjustable from UI
- **Per-weekday vs. global baseline**: ❌ Not disclosed; user doesn't know if comparison is weekday-adjusted
- **Sensitivity level**: ❌ Not shown

### Staffing / Peak Hours
- **Data sufficiency indicator**: ⚠️ Not explicitly audited, but no safety gate visible in code

---

## Overfitting Risk Assessment

| Model | Min Data Threshold | Risk if Below | Current Handling |
|-------|-------------------|--------------|-----------------|
| Price elasticity (OLS) | 10 txns, 5 days, CV > 3%, 5+ price bins | High bias in coefficient | Returns `None`, defaults to "insufficient" confidence ✅ |
| Raise/Lower decision | 20–25 txns/product | Medium (percentile logic still works with small N) | Proceeds with "low reliability" label |
| Revenue forecast | 28 days (floor), 60 days (quality) | High variance (<60 days) | `early_estimate` flag set, CI bands widened ✅ |
| Per-product forecast | 4+ weekly observations, 6+ for "confident" label | Trend direction unreliable | Silently omits products with < 4 weekly obs |
| Clustering | 4+ products, 20+ txns | Unstable assignments, arbitrary clusters | Returns `None` ✅ |
| Anomaly detection | 14+ days, 10+ days with ≥3 txns | High false positives | Returns empty list ✅ |
| Rising stars | 60+ days (requires prior period) | Missing signal entirely | Returns `None`, silently omitted |
| Declining products | 60+ days | Missing signal entirely | Returns empty list, silently omitted |

**Biggest risk**: Products with exactly 25 transactions getting a RAISE recommendation. That's a small sample for percentile-based logic when there are only 5 products total — the 65th percentile of 5 products is just "one of the top 2."

---

## Hardcoded Assumptions (NOT Data-Driven)

These are embedded in the code and **never disclosed to the user**:

| Assumption | Location | Value | Risk |
|-----------|----------|-------|------|
| Fallback gross margin | `action_center.py:218` | **65%** | HIGH — all impact calculations assume this if cost data absent |
| Price raise amount | `pricing.py:178` | **+5%** | MEDIUM — same for every product regardless of elasticity |
| Price lower amount | `pricing.py:229` | **−5%** | MEDIUM |
| Bundle attach rate | `action_center.py:299` | **10%** | MEDIUM — completely fabricated |
| Low-activity discount | `action_center.py:76` | **20% off** | MEDIUM |
| Low-activity elasticity | `action_center.py:78` | `1 + 1.2 × 0.20 = 1.24×` qty | MEDIUM — assumes 1.2 price elasticity |
| Revenue trend threshold | `insights.py:79` | `slope_pct > 0.5%` = "upward" | LOW — but very sensitive; normal variance can trigger |
| Per-product trend threshold | `forecast.py:55` | `slope_pct > 2%` = "Growing" | LOW |
| Impact range width | `action_center.py:105,240` | ±25–50% of central estimate | MEDIUM — arbitrary confidence interval |

**The 65% margin fallback is the most dangerous**: If a customer uploads data without cost info, EVERY dollar impact number is calculated with this invisible assumption. A business with 30% margins would see impact numbers 2× too high.

---

## Generic vs. Data-Driven Check

| Claim | Is it custom to this business? |
|-------|-------------------------------|
| "Raise Espresso price" | ✅ Custom — triggered by this product's actual percentile rank |
| "Could add ~$17/month" | ⚠️ Hybrid — qty is real; margin assumed at 65% |
| "Customers aren't price-sensitive" | ✅ Custom — from OLS on this product's data (when calculable) |
| "+5% increase suggested" | ❌ Generic — hardcoded for every product |
| "Bundle Star with Hidden Gem" | ⚠️ Custom in product names, generic in logic (10% attach always) |
| "Consider discounting Low Activity items" | ⚠️ Custom in product names, generic in discount % (always 20%) |
| "Revenue up 12% this week" | ✅ Custom — calculated from actual transaction data |

**Verdict**: Recommendations are **custom in target selection** (which products) but **generic in prescription** (how much to change, what the impact will be). A clever customer will notice if they compare two products getting the same "+5% recommendation."

---

## What Customer Will Trust

✅ Recommendations that build trust:
- "Your sales are up 12% this week vs last" — concrete, verifiable
- "Latte is in your top third by volume" — checkable
- "Croissant revenue down 31% in last 30 days" — data-visible

⚠️ Recommendations that may lose trust:
- "Could add ~$X/month" without disclosing the margin assumption
- "+5% suggestion" with no explanation for why specifically 5%
- "10% attach rate" on bundles — sounds precise but is fabricated

❌ Recommendations that will lose trust with analytical customers:
- Any dollar impact when cost data not uploaded (silent 65% assumption)
- "Customers aren't price-sensitive" when based on very few price bins

---

## Red Flags

- [x] **65% fallback margin never disclosed**: All impact calculations silently assume 65% if no cost data
- [x] **+5% amount never justified**: Every product gets the same suggestion regardless of elasticity magnitude
- [x] **Bundle attach rate fabricated**: 10% is not from data; it's a placeholder
- [x] **Model selection hidden**: User can't tell if forecast came from AutoARIMA or linear regression
- [x] **Silhouette score hidden**: User doesn't know if clustering quality is 0.3 or 0.8
- [x] **Rising stars/declining products silently absent** for businesses < 60 days old
- [ ] Low-data products below threshold are correctly filtered (not recommended anyway)
- [ ] Confidence tiers (high/directional/insufficient) are honest and shown in UI
- [ ] Anomaly detection day-of-week normalization is good defensive design
