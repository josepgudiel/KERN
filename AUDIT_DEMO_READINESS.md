# Demo Readiness Checklist

> One week to demo. This is your honest pre-flight checklist.

---

## MUST-HAVES (Show-Stoppers)

- [ ] Upload works without errors (test with a real non-demo CSV — NOT just demo data)
- [ ] At least 3 recommendations appear in Action Center after upload
- [ ] Recommendations are plausible (run the real CSV before demo day, not day-of)
- [ ] Action Center is clearly the entry point — not buried under other pages
- [ ] Mobile works (demo on phone, portrait + landscape — recent commits suggest mobile is addressed)
- [ ] No crashes or blank screens
- [ ] Dismiss recommendation works (shows tool is interactive, not read-only)
- [ ] Backend starts in < 30 seconds (or is already running when demo starts — no cold start)

**Critical blocker to resolve before demo:**

> If the business owner's data has fixed prices (e.g., a standard coffee shop menu), ALL pricing recommendations will show "Not enough data" confidence. This kills the pricing demo. 
> **Solution**: Have a backup CSV with some price variation (different sizes, modifiers as separate line items, occasional discounts). Verify before demo day.

---

## SHOULD-HAVES (Confidence-Builders)

- [ ] At least ONE recommendation clearly explains *why* in terms of the owner's data (not just "high demand, low price" — also "your espresso sells 143 units/month, which is your 3rd most ordered item")
- [ ] Dollar impact visible and labeled clearly ("Could add ~$X/month")
- [ ] Confidence tier visible on Action Center cards (not just Pricing page)
- [ ] Can show the Pricing page detail view with confidence badges
- [ ] Forecast page loads and shows a trend direction
- [ ] The "data quality" badge is visible somewhere ("Based on 450 transactions · 8 products · 3 months")
- [ ] At least one "aha!" recommendation — something the owner didn't already know

**What creates the "aha!" moment:**
- A specific declining product they weren't tracking ("Croissant is down 31% in the last 30 days — while the rest of your business was flat")
- A product they undervalue ("Your Latte is your 2nd highest-volume item but priced below your portfolio average")
- A surprising anomaly ("Valentine's Day 2025 was your best day — you were up 147%")

---

## NICE-TO-HAVES (Polish)

- [ ] "I acted on this" workflow (even just a checkbox + revisit prompt in 2 weeks)
- [ ] Annualized impact shown ("$18/month = $216/year")
- [ ] Forecast page shows model selection ("Using ARIMA — upgraded from linear because you have 60+ days of data")
- [ ] Margin disclosure inline ("Assumes ~65% margin — upload cost data for exact profit figures")
- [ ] Export to PDF report (customer leaves with something tangible)
- [ ] Industry context note somewhere ("Most similar businesses see 50–70% gross margins")

---

## Pre-Demo Testing Plan

Run these **before demo day** — not the morning of:

- [ ] **Test with your own CSV (not demo data)**
  - Minimum 60 days of data for full feature set
  - Include multiple products (8+) with different performance levels
  - Verify at least 3 Action Center recommendations appear

- [ ] **Test on mobile (portrait + landscape)**
  - Action Center cards readable
  - Forecast chart scrollable
  - No overflow / horizontal scroll on recommendation cards

- [ ] **Test with sparse data (1–2 weeks old business)**
  - Upload only 14 days of data
  - Expected: forecast returns "insufficient data" (clear message)
  - Expected: Action Center shows fewer/no trend recommendations
  - Does it fail gracefully or blank-page?

- [ ] **Test fixed-price scenario**
  - Upload a CSV where all prices per product are identical (no variation)
  - Expected: Pricing page shows all "Not enough data" confidence
  - Is this explained to the user, or does it just show blank badges?

- [ ] **Test with seasonal data**
  - Upload a CSV where one product drops to zero in a certain month
  - Does it get labeled "Low Activity" incorrectly? Will this confuse the demo customer?

- [ ] **Test cold start (< 60 days)**
  - Expected: No rising stars, no declining products, forecast uses linear only
  - Does the UI explain why these sections are absent?

---

## Risk Mitigation

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| Customer's CSV causes a parsing error | Medium | Test their CSV format in advance. Have a clean backup CSV ready. |
| All pricing shows "Not enough data" (fixed prices) | High for retail/food | Test with a CSV that has price variation. Explain: "For more precise recommendations, your data needs some price variation — e.g., different sizes or occasional discounts." |
| Customer's business is < 60 days old | Medium | Be upfront: "Full recommendations unlock after 60 days — here's what you see at your current stage" |
| Server cold start (free tier hosting) | Medium | Either keep server warm with a ping, or start the server 5 minutes before demo |
| Customer asks "what margin did you use?" | High | Have the answer ready: "We estimate based on a 65% margin when cost data isn't uploaded. Upload your COGS and you'll see exact profit figures." |
| Customer questions the +5% suggestion | High | "5% is a conservative starting point for a 2-week test. The key insight is whether to test a raise at all — the amount is yours to adjust." |
| Forecast seems too optimistic or pessimistic | Medium | Frame as a range: "The shaded area is the uncertainty band — the midpoint is the trend, but the real outcome could be anywhere in that range." |

---

## Known Limitations to Disclose (Proactively)

Disclose these before the customer asks — it builds trust:

- [ ] "Recommendations are based on your historical data — they show patterns from the past, not predictions of future behavior."
- [ ] "Our pricing suggestions assume you're selling at a fixed price. If you run frequent promotions, the price sensitivity estimate will be noisier."
- [ ] "When you haven't uploaded cost data, impact numbers assume a ~65% gross margin — upload your costs for exact profit figures."
- [ ] "The bundling suggestion assumes 1 in 10 customers will add the second item — that's a reasonable benchmark, but your actual attach rate may vary."
- [ ] "Data is processed in your browser session and not stored permanently. To get fresh recommendations, re-upload your latest export."

---

## Demo Script

**Opening (30 seconds):**
> "I built a tool that looks at your sales data and tells you the 3–5 most important things you should do today to make more money. Not charts — specific actions with dollar estimates. Let me show you with a real coffee shop dataset."

**Flow (10–12 minutes):**

1. **Upload** (1 min): "Here's a CSV export from a coffee shop's POS. Drop it in."
2. **Wait** (10–15 sec): "It's running 6 different analyses right now — pricing, forecasting, clustering, anomaly detection."
3. **Action Center first** (3 min): "These are ranked by dollar impact. The top one says raise Espresso from $3.50 to $3.68. Here's why..."
4. **Trace one recommendation** (2 min): "Espresso is in the top third of volume, bottom third of price. A small raise is worth testing. The model estimates $18/month in extra profit — that's conservative since we don't have their cost data."
5. **Show a watch-out** (2 min): "Croissants are down 31% in the last 30 days, while the overall business was flat. That's structural, not seasonal. Time to investigate."
6. **Forecast page** (1 min): "Revenue trend is upward at +0.8%/day. The business is growing. Now's the time to test price increases, not cut them."
7. **Best Sellers / Clusters** (1 min): "Here's the portfolio map — Stars, Cash Cows, Hidden Gems, Low Activity. Where do you want to spend your energy?"
8. **Closing question** (1 min): "What's the one thing you'd want this tool to tell you that it's not telling you yet?"

**Don't show**: AI Advisor (too much surface area for questions), Report page (no strong demo value), When to Staff (unless they have hourly data)

---

## Post-Demo Feedback Plan

Capture these immediately after the demo:

- [ ] What surprised them? (validation that data is custom)
- [ ] What confused them? (UX gaps to fix)
- [ ] What did they immediately ask for? (feature roadmap input)
- [ ] Would they use this weekly / monthly? (usage frequency expectation)
- [ ] What would make them trust the recommendations more? (confidence gap)
- [ ] What data do they have that they'd want to upload? (format + data richness)
- [ ] What would they pay for this? ($9/month? $49? $149?) (pricing calibration)

---

## Summary

**Ready for demo?** ⚠️ MOSTLY — with these three caveats:
1. Test with a real CSV with price variation before demo day
2. Prepare a verbal answer for "what margin did you use?" and "why 5%?"
3. Know which features break gracefully for thin data (< 60 days) vs. which ones silently disappear

**Biggest strength**: Specific product-level recommendations with dollar amounts. Nobody else tells a coffee shop owner "raise your Espresso price by 18 cents."

**Biggest risk**: Customer uploads fixed-price CSV, everything shows "Not enough data," demo falls flat. Test the actual data first.
