# Bias & Fairness Audit

> Based on source code review of `clusters.py`, `pricing.py`, `forecast.py`, `anomaly.py`, `insights.py`.

---

## Clustering Fairness

### How clusters are assigned
K-Means runs on **log1p(quantity)** and **log1p(revenue)**, StandardScaled. The log transform is the key fairness mechanism: it compresses extreme values so a $500/month product vs a $50/month product aren't infinitely far apart.

**Labels are assigned by scoring:**
```
Stars:        high quantity + high revenue  (top of both dimensions)
Low Activity: low quantity + low revenue    (bottom of both dimensions)
Cash Cows:    high revenue relative to quantity  (high margin proxy)
Hidden Gems:  high quantity relative to revenue  (volume, low price)
```

### Fairness assessment

| Question | Answer |
|----------|--------|
| Do high-revenue products dominate "Stars"? | ✅ Intentional — Stars = high volume + high revenue |
| Do low-revenue products get "Low Activity"? | ✅ Intentional but risky: seasonal or new products may be mislabeled |
| Is clustering based on revenue or behavior? | Both — but log transform reduces extreme revenue skew |
| Are cluster assignments stable? | ✅ YES — random seed = 42, deterministic K selection via silhouette |
| Could adding one new product shift all clusters? | ⚠️ YES — silhouette-optimal K may change from 3 to 4, reshuffling all assignments |

### Bias concern: Seasonal products in "Low Activity"
A product that only sells in winter (e.g., Hot Cocoa) analyzed in spring will have low cumulative quantity and revenue. K-Means will correctly reflect that it's currently underperforming — but the "Low Activity" label and the "consider discounting" prescription are wrong in this context.

**Current handling**: `_find_declining_products()` has `seasonality = "possibly_seasonal"` detection based on whether overall business is also down. But clustering has **no seasonality awareness at all**. A seasonal product will be labeled "Low Activity" with a discount prescription, year-round.

**Verdict**: Clustering is fair by design for established, non-seasonal products. It is unfair for seasonal or new products. No warning is shown.

---

## Pricing Fairness

### Minimum transactions to trigger recommendation

| Action | Min threshold | Code location |
|--------|-------------|--------------|
| Raise Price | **25 transactions** | `pricing.py:134` |
| Lower Price | **20 transactions** | `pricing.py:135` |
| Maintain | **20 transactions** | `pricing.py:136` |
| Overall recommendation | **3 products with ≥20 txns** | `pricing.py:153-154` |

### How many products fall below threshold?

For a business with 80 total transactions and 10 products:
- Average per product: 8 transactions
- Products with 25+ transactions: probably 2–3 (top sellers only)
- Products below threshold: ~7–8 ← silently excluded

**What the user sees**: 2–3 recommendations. 7–8 products show nothing. No explanation.

### Are excluded products marked?
❌ No. If a product has 15 transactions, it simply doesn't appear in the Pricing page. The user doesn't know why.

### Do price ranges matter?

The RAISE/LOWER thresholds are **percentile-based within your own product portfolio**. A $1 item and a $100 item are compared relative to all other products, not against market benchmarks. This means:

- **If all products are cheap**: Percentile logic still works correctly
- **If one product is 10× more expensive**: That product is always in "high price" tier; others always in "low price" tier — recommendation can be driven by product category rather than pricing strategy

**Example**: A coffee shop with coffees ($3–$5) and one catering box ($150) — the catering box will always be flagged as "high price" and "lower" may trigger if catering has low volume. This is technically correct but potentially misleading.

### Is there a cheap vs. expensive bias?
No explicit bias. Percentile logic is product-agnostic. However, **food categories** will typically have lower absolute prices than products, meaning coffees may always appear in "low price" tier and desserts in "high price" tier — recommending coffee price raises structurally.

---

## Forecast Fairness

### Seasonal products
- **Do they get proper forecasts?** ⚠️ PARTIAL
  - Linear fallback: No seasonality awareness
  - Prophet (if 60+ days): `weekly_seasonality=True` and `monthly_seasonality` via Fourier
  - AutoARIMA (if 60+ days): Seasonal decomposition included
  - For most small businesses (28–59 days of data): **linear fallback only, no seasonality**

### Trending vs. flat products
- **Trending**: Linear slope captures direction; exponential weighting (half-life = n/3 weeks) gives more weight to recent data ✅
- **Declining**: Downward trend in forecast; `"↓ Declining"` label applied ✅
- **Flat**: Flat products forecast as flat; no issue ✅

### Forecast confidence: is it proportional to data quality?
✅ YES — CI bands are widened by `max(1.0, 60/n_history_days)` multiplier for datasets < 60 days. More uncertainty → wider bands. **But this multiplier is not disclosed to the user.**

---

## Anomaly Detection Fairness

### High-volume vs low-volume products
**Anomaly detection runs on total daily revenue, not per-product.** This means:

- A day where one high-volume product had a spike → flagged as a day-level anomaly
- Low-volume products can't individually cause anomalies unless they're the only product selling that day

**Consistency**: Per-weekday MAD baselines are computed if there are ≥4 observations for that weekday. If a weekday has < 4 observations, it falls back to global MAD. This means:

- **Inconsistency in sensitivity**: Mondays with 4+ data points get a tighter, weekday-specific baseline. Sundays with only 3 observations get the noisier global baseline.
- **Fairness concern**: Day-of-week comparison is good (Monday compared to Mondays), but new businesses with < 4 weeks of data get global MAD everywhere → potentially noisier anomaly detection.

### Threshold: z = 2.5 for all businesses
The same `_MAD_ANOMALY_Z = 2.5` threshold applies regardless of:
- Business volatility (a seasonal business is inherently more volatile)
- Product mix (a single-product business has higher revenue concentration)
- Dataset size (a business with 14 days has 2 Mondays; the Monday baseline is established from just 2 data points)

**Fairness verdict**: The threshold is constant. Volatile businesses will see more anomalies (higher false positive rate). Stable businesses will see fewer. This isn't unfair per se, but it's not disclosed.

---

## Potential Bias Issues

- [x] **Seasonal products labeled "Low Activity"**: No seasonality correction in clustering. Wrong label → wrong prescription.
- [x] **New products in "cold start"**: Products with < 20 transactions get no pricing signals, no rising star calculation, potentially no anomaly visibility.
- [x] **High-revenue products dominate recommendations**: Action Center sorts by `impact_dollars` (descending). Low-revenue products with genuine issues surface only at the bottom.
- [x] **Category-driven clustering**: A coffee shop's coffees (low price, high volume) will always cluster as "Hidden Gems" or "Stars" while food (high price, low volume) will always be "Cash Cows." This is structurally correct but can make recommendations feel repetitive.
- [x] **Fixed-price businesses**: Elasticity estimation fails (CV < 3%) for all products, all confidence badges say "Not enough data." The Pricing page becomes nearly useless for fixed-price businesses.

---

## What's Fair

- ✅ Every product with sufficient data gets analyzed; below-threshold products are filtered (not misrecommended)
- ✅ Log-scaling in clustering prevents single high-revenue products from collapsing all other clusters
- ✅ Day-of-week normalization in anomaly detection is fair (Mondays compared to Mondays)
- ✅ Recommendations are proportional to transaction count (low-reliability label for < 50 txns)
- ✅ Seasonality flag in declining products shows contextual awareness
- ✅ Rising star "velocity_score" weights by `log1p(recent_rev)` — prevents a $1 product from dominating just because of high growth %
- ✅ Dynamic `_min_rev_floor` (20th percentile) for rising stars prevents trivial-revenue products from appearing

---

## Summary Table

| Analysis | Fairness Rating | Key Issue |
|----------|----------------|-----------|
| Clustering | ⚠️ Moderate | Seasonal products mislabeled; no seasonality awareness |
| Pricing (raise/lower) | ✅ Good | Percentile logic is data-driven, product-agnostic |
| Pricing (exclusion) | ❌ Poor | Silently excludes products; no explanation to user |
| Forecast | ✅ Good | CI widened for thin data; multiple model fallbacks |
| Anomaly detection | ✅ Good | Day-of-week normalization is best-in-class for this type of tool |
| Impact calculation | ❌ Poor | 65% fallback margin never disclosed |
