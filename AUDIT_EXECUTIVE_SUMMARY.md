# KERN Pre-Demo Audit — Executive Summary

> Audit date: 2026-04-05  
> Basis: Full source code review — pricing.py, forecast.py, clusters.py, anomaly.py, action_center.py, insights.py, safety.py, frontend pages

---

## The Good

**Genuine differentiation:**
Tableau shows you charts. Power BI shows you charts. KERN says "raise your Espresso price by 18 cents — here's why, here's the math." That's a real and valuable gap. The Action Center concept is the right product.

**Real analytics, not templates:**
- Pricing decisions are based on actual percentile comparisons from this business's data
- Elasticity estimation (when price variation exists) uses log-log OLS regression — real econometrics
- Anomaly detection uses MAD with day-of-week normalization — smarter than most BI tools
- Revenue forecasting has a real three-path hierarchy (AutoARIMA → Prophet → linear fallback)
- Clustering uses silhouette-optimized K-Means with log-scale normalization

**Honest confidence system:**
Three-tier confidence (high / worth testing / not enough data) is shown to users. Low-confidence signals are marked, not hidden. Safety gates prevent analysis on insufficient data.

**Strong safety engineering:**
- Minimum transaction thresholds prevent noise-based recommendations
- Deterministic random seed (42) makes clustering reproducible
- `data_quality_flag` warns when forecasts are early estimates
- Day-of-week normalization prevents false anomalies on slow weekdays

**Clean, distinctive design:**
The frontend has personality. Not generic. Mobile-responsive (recent commits address this well).

---

## The Uncertain

**Fixed-price businesses break the pricing engine:**
Coffee shops, restaurants, and retailers with fixed menus have price coefficient of variation < 3%. This causes elasticity estimation to fail for every product. All pricing recommendations get "Not enough data" confidence. This is the honest behavior, but it neuters the most compelling feature for the most common demo customer.

> **Verify before demo**: Does the demo dataset or customer CSV have price variation? If not, the Pricing page will be nearly empty of signal.

**The 65% fallback margin is invisible and consequential:**
When cost data isn't uploaded (most demos), every dollar impact number silently assumes 65% gross margin. A business with 30% margins sees impact numbers 2× too high. A business with 80% margins sees them 18% too low. This assumption is never surfaced. It's technically disclosed in the code comments, but the user never sees it.

**Generic prescriptions wrapped in custom targeting:**
- *Which* product to raise: ✅ Data-driven (percentile logic on actual data)
- *How much* to raise: ❌ Always +5% (hardcoded)
- *What the impact will be*: ⚠️ Hybrid (quantity real, margin assumed)
- Bundle attach rate: ❌ Always 10% (fabricated)
- Low-activity discount: ❌ Always 20% off (hardcoded)

A business owner comparing two products both receiving "+5% raise" recommendations will notice they got the same advice. This erodes the "custom intelligence" positioning.

---

## The Risks

**Elasticity failure for fixed-price businesses (HIGH):**
If the demo customer runs a standard coffee shop with a printed menu, the pricing page will show "Not enough data" for every product. You can work around this by explaining the test-price approach, but it requires a demo pivot you should prepare for.

**The "show me the math" moment (MEDIUM):**
Analytical customers will ask about the dollar impact calculation. The correct answer — "we multiply your actual monthly units by the price change, then apply a 65% gross margin assumption since you didn't upload cost data" — is honest but sounds like guesswork if you're not ready to say it confidently.

**Silent data exclusions (MEDIUM):**
Products below transaction thresholds, businesses < 60 days old, and fixed-price products are silently excluded from analyses with no explanation to the user. The user doesn't know why [Product X] doesn't appear. This creates a "why isn't Muffin here?" question that you need to be ready to answer.

**Rising stars / declining products absent for new businesses (MEDIUM):**
Both `_find_rising_stars()` and `_find_declining_products()` require 60+ days of history (prior period comparison). A business 45 days old sees no rising stars and no declining products. The Action Center looks sparse and unconvincing without these signals.

---

## Demo Readiness

**Status: ⚠️ MOSTLY READY — three action items before demo**

**Action Item 1 (Critical — do today):**
Test with a CSV that has price variation (not fixed-price menu). Verify pricing recommendations show "Strong signal" or "Worth testing" confidence. Without this, the pricing demo is compromised. If your customer has fixed prices, practice the pivot: "For more precise pricing insights, we need some price variation in your data — tell me more about how you currently vary prices."

**Action Item 2 (Important — do before demo day):**
Prepare three verbal answers for likely customer questions:
1. "What margin did you use?" → "65% estimated. Upload your cost data and we'll use your exact figures."
2. "Why 5%?" → "5% is the conservative test threshold — the key insight is whether to test a raise, not the exact amount. You pick the number."
3. "Why doesn't [Product X] appear?" → "That product has [N] transactions — we need 25+ for a pricing signal. It'll appear as your data builds up."

**Action Item 3 (Optional — adds polish):**
Add one line to each Action Center recommendation: "Based on [N] transactions from [date range]." This makes provenance visible and dramatically increases trust. It requires a small frontend change, not a backend change — all data is already in the API response.

---

## Top 3 Things to Verify Before Demo

1. **Pick a real CSV with price variation** — test pricing recommendations show meaningful confidence (not all "Not enough data")
2. **Ask "why?" for each recommendation** — can you explain the data behind it in one sentence? If not, practice the explanation
3. **Simulate "show me the math"** — know the answer to "what margin did you use?" before the customer asks

---

## What to Expect from Customer Feedback

**Things they'll validate (you'll be right about):**
- "I didn't know Croissants were declining" — anomaly and declining product detection works well
- "That's actually true about espresso" — relative pricing logic resonates intuitively
- "How did you know that was Valentine's Day?" — anomaly labeling is a delightful surprise

**Things they'll push back on (prepare for these):**
- "Why 5%? That seems arbitrary." — It is. Acknowledge it. "It's a conservative test threshold; the real insight is that you have room to test a raise."
- "Is this profit or revenue?" — Acknowledge the 65% assumption upfront, don't wait for the question
- "What about [seasonal product X]?" — Clustering has no seasonality awareness; "Low Activity" may be wrong for seasonal items

**Feature requests you'll hear:**
- "Can I set a target price and track whether sales held?" → Action tracking / A/B test follow-up
- "Can I upload my costs?" → Cost data integration (partially supported — if cost column exists, it's used)
- "Can you show me this for specific locations?" → Multi-location filtering (if location column exists, it's in the data loader)
- "Can I export this to Excel?" → Report export

---

## One-Sentence Differentiation (Practice This)

> "Other tools show you what happened. KERN tells you what to do about it — with specific products, specific prices, and a dollar estimate of what it's worth."

---

## Success Criteria

- Customer says: "I didn't know this about my business" → ✅ Data is custom and valuable
- Customer says: "How did you figure that out?" → ✅ Model is intriguing, not a black box
- Customer says: "When can I use this with my data?" → ✅ Product-market fit signal
- Customer says: "That's a cool dashboard" → ❌ Wrong reaction — you're not a dashboard, you're an advisor

---

## Files in This Audit

| File | Contents |
|------|----------|
| `AUDIT_PRICE_RECOMMENDATION.md` | End-to-end trace of one pricing recommendation; hardcoded assumptions documented |
| `AUDIT_MODEL_CONFIDENCE.md` | Confidence transparency; hidden assumptions; filtering behavior |
| `AUDIT_REAL_DATA_TEST.md` | Predicted behavior on small real dataset; edge cases |
| `AUDIT_BIAS_FAIRNESS.md` | Fairness across product types; seasonal bias; fixed-price bias |
| `AUDIT_UX_CLARITY.md` | First-time user flow; clarity gaps; what creates trust |
| `AUDIT_DEMO_READINESS.md` | Go/no-go checklist; demo script; risk mitigation |
| `AUDIT_EXECUTIVE_SUMMARY.md` | This file |
