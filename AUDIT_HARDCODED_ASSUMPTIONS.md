# Hardcoded Assumptions Audit

## Pricing Module (pricing.py)

### `+5%` price increase — `_get_price_recommendations`
- **Location**: `pricing.py:174` — `sug = round(price * 1.05, 2)`
- **Also**: `pricing.py:182` — `adj_qty = qty * (1 - _e_used * 0.05)` uses 5% as the delta for impact math
- **Should it be data-driven?** YES — elasticity is already computed in this branch
- **Current fallback**: No fallback — always +5% regardless of elasticity
- **Fix**: Use `_elasticity_to_raise_pct(elasticity)` helper to derive % from elasticity bucket (8%/6%/4%/2%). Fall back to 3% conservative with caveat when no elasticity data.

### `−5%` price decrease — `_get_price_recommendations`
- **Location**: `pricing.py:229` — `sug = round(price * 0.95, 2)`
- **Should it be data-driven?** YES — elastic products may need more than 5%; inelastic products shouldn't be cut at all
- **Current fallback**: Always −5% regardless of elasticity
- **Fix**: Use `_elasticity_to_lower_pct(elasticity)` helper. If no elasticity or inelastic (<0.7), note that price cut may not be the right lever.

---

## Discounting Module (action_center.py — `_prescribe_low_activity`)

### `20%` discount for low-activity items
- **Location**: `action_center.py:76` — `discount_price = avg_price * 0.80`
- **Location**: `action_center.py:78` — `new_qty = monthly_qty * (1 + 1.2 * 0.20)` (also uses hardcoded 20% demand uplift multiplier)
- **Location**: `action_center.py:100` — text: "A 20% discount could unlock dormant demand"
- **Should it be data-driven?** YES — if a product is inelastic, a 20% discount loses margin without boosting volume
- **Current fallback**: Always 20%, always applied to all low-activity products
- **Fix**: Call `_estimate_product_elasticity` for each product. Derive discount % from elasticity (15–20% for elastic, skip discount entirely for inelastic). Show reason why specific % was chosen.

---

## Bundling Module (action_center.py — `_build_action_center`)

### `10%` bundle attach rate
- **Location**: `action_center.py:299` — `bundle_upside = gem_price * (float(stars.iloc[0]["quantity"]) * 0.10)`
- **Location**: `action_center.py:315` — `"impact_label": f"... (estimated, 10% attach rate assumed)"`
- **Should it be data-driven?** YES — Apriori basket analysis is already run in `recommendations.py`. The cross-cluster bundle in `action_center.py` ignores this entirely.
- **Current fallback**: Always 10%, regardless of whether co-purchase data exists
- **Fix**: Import `_compute_basket_rules` in `action_center.py`. Look up the star+gem pair in Apriori rules. If a rule exists, use actual `confidence` as the attach rate. If no rule, label as "no co-purchase signal" and use a conservative 5% with explicit caveat.

### `10%` bundle discount in impact label (recommendations.py)
- **Location**: `recommendations.py:748` — `f"Bundle at {currency}{bundle_price:.2f} (10% off combined)."`
- **Location**: `recommendations.py:707` — `bundle_price = round((price_a + price_b) * 0.90, 2)`
- **Note**: This 10% is the *test discount*, not the attach rate. Reasonable as a suggested test parameter. Lower priority than the 10% attach rate in action_center.py.

### `30%` attach rate assumption (recommendations.py)
- **Location**: `recommendations.py:722` — `attach_30pct = round(avg_weekly * 0.30, 0)`
- **Should it be data-driven?** YES — Apriori `confidence` IS the probability that a buyer of A also buys B. That is directly the expected attach rate.
- **Current fallback**: Always 30%, even though the actual Apriori confidence is computed and available in `pair["confidence"]`
- **Fix**: Use `pair["confidence"]` as the expected attach rate. Show "At expected X% attach rate (from your co-purchase data)".

---

## Staffing Module
- No staffing module found. No hardcoded staffing prescriptions.

## Forecasting Module (forecast.py)
- `forecast.py:162`: `changepoint_prior_scale` (0.15–0.25) — these are Prophet tuning parameters that scale with data span. These are methodology parameters, not business prescriptions. Not data-driven assumptions.

## Anomaly Module (anomaly.py)
- No hardcoded detection thresholds that affect user-facing recommendations — anomaly detection uses statistical methods (MAD). Not flagged.

## Clusters Module (clusters.py)
- Cluster labels (Stars, Cash Cows, Hidden Gems, Low Activity) are derived from data quantile thresholds. Not hardcoded business prescriptions. Not flagged.

---

## Summary

| Module | Hardcoded Value | Should Be Data-Driven | Priority |
|--------|----------------|----------------------|----------|
| `pricing.py:174` | +5% price raise | YES — from elasticity | HIGH |
| `pricing.py:229` | −5% price cut | YES — from elasticity | HIGH |
| `action_center.py:76` | 20% discount | YES — from elasticity | HIGH |
| `action_center.py:299` | 10% attach rate | YES — from Apriori | HIGH |
| `recommendations.py:722` | 30% attach rate | YES — from Apriori confidence | MEDIUM |
| `recommendations.py:707` | 10% bundle discount | Low — is a test parameter | LOW |

**Total hardcoded business assumptions: 6**
**Total that should be data-driven: 5** (excluding the bundle discount test parameter)
