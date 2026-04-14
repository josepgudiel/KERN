# Real Data Test Audit

> **Note**: This audit documents what WOULD happen with a small real dataset based on code-level analysis, not a live run. To complete this properly, upload a real CSV before your demo. The scenarios below predict engine behavior from source code.

---

## Test Dataset (Predicted Scenario)

Use this to test before demo:

```
CSV: small_cafe_test.csv
Products: 8–10 (e.g., Espresso, Latte, Muffin, Sandwich, OJ, Croissant, Tea, Water)
Transactions: ~80–120
Date range: 60–90 days (use 90 to unlock rising stars + declining products)
Currency: USD
Format: date, product, quantity, price/revenue
```

If you use exactly 60 days: rising stars require `prior_start = max_date - 59 days`.  
If data starts after that → `_find_rising_stars()` returns `None` → no rising stars in Action Center.  
Use **90 days minimum** to get the full recommendation set.

---

## Predicted Action Center Output (80–120 txns, 8 products, 90 days)

### Recommendation 1: Price Raise (e.g., "Raise Espresso price → $X.XX")
- **Type**: Pricing
- **Impact**: ~$15–$40/month (quantity × $0.18 × 0.65 assumed margin)
- **Plausible?** ✅ YES — espresso is typically high-volume, low-priced relative to food items
- **Data-driven?** ⚠️ HYBRID
  - Evidence: "Espresso is top-3 in volume, bottom-3 in price" — from actual data
  - BUT: +5% is hardcoded, 65% margin is assumed, zero demand loss assumed
- **Actionable?** ✅ YES — "Raise Espresso from $3.50 to $3.68"
- **What's missing**: Why 5%? What if I lose customers? What's my actual margin on espresso?
- **Elasticity confidence**: Likely "insufficient" for a fixed-price menu ← KEY DEMO RISK

### Recommendation 2: Amplify [Product] — gaining momentum fast
- **Type**: Rising Star
- **Impact**: ~$X × (growth_pct / 100) — may be small in absolute terms
- **Plausible?** ✅ YES if product genuinely grew last 30 days
- **Data-driven?** ✅ YES — calculated from actual 30-day vs prior-30-day comparison
- **Actionable?** ⚠️ UNCLEAR — "feature as daily special, stock up" is vague
- **Risk**: Impact = recent_rev × growth_pct/100. If a $20 product grew 50%, impact shows as $10/month. Small number may underwhelm.

### Recommendation 3: Bundle [Star] with [Hidden Gem] to lift avg order
- **Type**: Cross-cluster bundle
- **Impact**: gem_price × star_qty × 10% — always 10% attach rate
- **Plausible?** ✅ YES — bundling logic is intuitive
- **Data-driven?** ❌ NO — 10% attach rate is hardcoded, not from basket analysis
- **Actionable?** ✅ YES — specific products named, action is "add upsell at point of sale"
- **Customer question**: "How do you know 10% of my customers will buy both?"

### Watch Out 1: [Product] is losing revenue — investigate now
- **Type**: Declining product
- **Impact**: at_risk = (older_rev - recent_rev), labeled as monthly risk
- **Plausible?** ✅ YES — if product genuinely declined
- **Data-driven?** ✅ YES — day-of-week normalized comparison, seasonality flag
- **Actionable?** ⚠️ UNCLEAR — "bundle, flash sale, or remove" is three different actions, no guidance on which

### Watch Out 2: Low Activity items — consider discounting
- **Type**: Low Activity prescription
- **Impact**: Modeled as 20% discount → 24% volume increase (1.2 elasticity assumed)
- **Plausible?** ✅ YES — slow items exist in every business
- **Data-driven?** ⚠️ HYBRID — product names real, discount amount and elasticity hardcoded
- **Customer question**: "Why 20% off? Why not 10%?"

---

## Edge Cases to Test

### Smallest product (5–10 transactions)
- **What happens**: Silently excluded from pricing recommendations (gate: 20–25 min)
- **User sees**: Nothing — the product just doesn't appear
- **Risk**: Customer wonders "why didn't I see [Product X]?" — no explanation given

### Newest product (added 2 weeks ago)
- **What happens**:
  - Pricing: May qualify if enough txns in 2 weeks
  - Rising stars: Needs to appear in BOTH recent (last 30 days) and prior (30–60 days) periods
  - Forecast: LinearFallback only; no trend established
- **Risk**: New products get no insights → "cold start" problem uncovered

### Seasonal product (e.g., Hot Cocoa only in winter months)
- **What happens**:
  - Declining products: `seasonality = "possibly_seasonal"` flag is set if overall business is also down
  - Forecast: Linear fallback won't capture seasonality well
  - Clustering: Placed in "Low Activity" during off-season — potentially misleading
- **Risk**: A seasonal "Low Activity" product might incorrectly get a "consider removing" suggestion

### Product generating 80% of revenue
- **What happens**:
  - Clustering: Will be in "Stars" by large margin
  - Pricing: Likely "Maintain" since high revenue + high price
  - Action Center: Bundle suggestion will use this as the star
- **Risk**: Everything points to this one product — recommendations feel repetitive

---

## Products That Didn't Get Recommendations

In a typical 8-product, 80-transaction dataset:

| Product | Why no recommendation |
|---------|----------------------|
| Low-transaction item (< 20 txns) | Below pricing gate; silently omitted |
| New product (< 30 days) | Can't calculate declining status |
| Stable middle-performer | Not in top or bottom quartile; no pricing signal |

---

## Gaps Discovered

- [ ] **Cold start problem**: New products (< 30 days) get essentially no insights. A business 2 months old sees a dramatically diminished Action Center. No message to the user explaining why.
- [ ] **Fixed-price businesses**: All elasticity estimates will be "insufficient" (CV < 3%). The entire Pricing page will show "Worth testing" or "Not enough data" for every product.
- [ ] **Missing: "I don't have cost data" context**: Impact calculations silently use 65% margin. User assumes these are real profit figures.
- [ ] **Rising star impact is optimistic**: A product growing 50% doesn't necessarily keep growing. The model treats the growth trend as if it will continue, which is regression-to-mean blind.
- [ ] **Declining product action is too broad**: "Bundle, flash sale, or remove" is not an action — it's three different strategies. Customer doesn't know which to pick.
- [ ] **No way to dismiss a recommendation from Action Center and give feedback**: The dismiss button exists, but there's no "why are you dismissing?" capture. No learning loop.

---

## Customer Reaction Prediction

**They will be impressed by:**
- 😍 Seeing their specific product names in recommendations ("Raise Espresso" not "raise prices")
- 😍 The WoW comparison ("sales up 12% this week")
- 😍 Declining product detection — "I didn't realize Croissants were down 31%"
- 😍 The anomaly labels — "Valentine's Day effect?" is a delightful detail

**They will be skeptical of:**
- 😐 The +5% suggestion — "Why not 8%? Why not 3%?"
- 😐 Bundle recommendations — "How do you know 10% will add it?"
- 😐 Dollar impact numbers — "Is this profit or revenue? What margins did you use?"
- 😐 "Low Activity" items — if it's seasonal, the label is wrong

**They will ask questions about:**
- ❓ "How did you calculate that $18/month?"
- ❓ "What's my actual margin on espresso?"
- ❓ "What does 'worth testing' vs 'strong signal' mean?"
- ❓ "Why doesn't [Product X] appear here?"
- ❓ "What happens if I raise the price and sales drop?"

**They will reject:**
- 🚫 Any recommendation for a product they know is seasonal — if it's labeled "Low Activity" when it's just winter's over
- 🚫 Bundle suggestions if the two products aren't actually complementary (system doesn't check category compatibility)
