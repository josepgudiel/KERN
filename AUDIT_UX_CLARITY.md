# UX Clarity Audit

> Perspective: First-time coffee shop owner with zero analytics experience, seeing this tool for the first time.

---

## First-Time User Flow

### Landing Page (/)
- **Clarity: 8/10**
- Would you click "Get Started"? ✅ YES — if the value prop is clear
- First question you'd ask: "What file do I need to upload?" and "What does this tell me that my POS doesn't?"
- **Gap**: If the landing page doesn't immediately answer "this tells you which prices to raise and where your revenue is leaking," the elevator pitch is lost.

### Upload Page (/dashboard/upload)
- **Clarity: 7/10**
- Can you find your CSV? ✅ YES — basic file upload UX
- Is the expected format clear? ⚠️ PARTIAL
  - README says it supports 10+ POS formats (Square, Toast, Shopify, etc.)
  - But does the upload page SAY this? If it just says "Upload CSV," a business owner will wonder if their Square export works
  - The `data_loader.py` does automatic column detection — but the user doesn't know this
- After upload, does it feel broken or loading? ⚠️ UNCERTAIN
  - There's a `slow` state with a "server starting up" message — this is good
  - But if analysis takes 10–15 seconds, the user may think it's broken
- **Gap**: "Upload your Square export, your Shopify export, or any CSV with sales data" would eliminate format anxiety

### Action Center (First Time)
- **Clarity: 7/10**
- Do you understand why these recommendations exist? ⚠️ MIXED
  - Recommendation titles like "Raise Espresso price → $3.68" are clear
  - Recommendation titles like "Amplify Latte — gaining momentum fast" are clear
  - Watch out titles like "Revenue trend unclear — upload more history" are confusing to a non-analyst
- Which recommendation would you act on first? The one at the top (highest dollar impact) — the ranking by impact is good UX
- Do you know what happens if you dismiss one? ✅ YES — dismiss button exists and works
- **Gap**: Users need to understand "quick wins" vs "watch outs" immediately. If these sections aren't labeled prominently, users will read them in order without knowing one is opportunity and the other is risk.

---

## Typical Recommendation Card

### Is the action clear?

| Card Type | Example | Clarity |
|-----------|---------|---------|
| Price raise | "Raise Espresso price → $3.68" | ✅ VERY CLEAR — specific product, specific price |
| Bundle | "Bundle Latte with Croissant to lift avg order" | ✅ CLEAR — specific products |
| Rising star | "Amplify Muffin — gaining momentum fast" | ⚠️ VAGUE — "amplify" and "feature as daily special" aren't specific enough |
| Low activity | "Consider discounting these 3 slow items — projected recovery: $45/month" | ✅ CLEAR — specific items, specific discount, specific impact |
| Declining product | "[Product] is losing revenue — investigate now" | ⚠️ ACTION UNCLEAR — "bundle, flash sale, or remove" is three different strategies |
| WoW momentum | "Your sales are up 12% this week — capitalize now" | ✅ CLEAR — but "capitalize now" needs a specific action |

### Do you understand the upside?
✅ Dollar impact shown prominently ("Could add ~$18/month")
⚠️ But: Is it profit or revenue? User doesn't know. (It's actually revenue × assumed 65% margin = estimated profit)
❌ No breakeven shown: "If you raise the price and lose 10% of customers, you still profit $X"

### Do you trust it?
⚠️ UNCERTAIN — depends on customer sophistication

A non-analytical customer:
- ✅ Will trust "high demand, below-average price" framing — makes intuitive sense
- ❌ May feel uneasy about AI making pricing decisions

An analytical customer:
- ✅ Will appreciate confidence tiers (strong signal / worth testing)
- ❌ Will want to see the data (how many transactions? what price range?)
- ❌ Will question the +5% amount ("why not 8%?")

---

## Other Pages

### Pricing Page (/dashboard/pricing)
- **Why would you visit?**: "I want to see all pricing suggestions in detail"
- **What question does it answer?**: "Which products should I consider re-pricing?"
- **Confidence badges visible?** ✅ YES — "Strong signal", "Worth testing", "Not enough data" shown
- **n_transactions visible?** ✅ YES — shown on cards
- **Would you take action?** ⚠️ YES but with friction — the "reason" text is long and includes caveats that feel like legal disclaimers

### Forecast Page (/dashboard/forecast)
- **Why would you visit?**: "I want to know if my business will be bigger or smaller next month"
- **Does the page answer it?**: ✅ YES — projected revenue for 1–8 weeks ahead
- **Is the model shown?**: ❌ NO — user doesn't know if it's ARIMA or linear regression
- **Are uncertainty bands shown?**: Should be (data is in API), but depends on frontend rendering
- **Would you take action?**: ⚠️ UNCLEAR — forecast is informational, not prescriptive on its own

### Best Sellers / Clusters (/dashboard/whats-selling)
- **Why would you visit?**: "I want to know which products are my best performers"
- **Stars/Cash Cows/Hidden Gems labeling**: ✅ MEMORABLE and intuitive
- **Gap**: Seasonal products may be labeled "Low Activity" incorrectly. No caveat shown.

### Peak Hours / Staffing (/dashboard/when-to-staff)
- **Why would you visit?**: "I want to know when to add or cut staff"
- **Does it show specific hours?**: Should show hour×day heatmap
- **Gap**: If business is small (< 30 days), staffing recommendations may be too sparse to act on

### AI Advisor (/dashboard/ai-advisor)
- **Why would you visit?**: "I want to ask a question"
- **What question?**: "Why is my revenue down?" or "Should I add a new product?"
- **Risk**: Groq/Llama may give generic business advice that contradicts the data-driven recommendations on other pages. These two sources of truth need to be reconciled.

---

## Clarity Issues Found

- [x] **Tool is partially read-only**: You can view recommendations and dismiss them, but you can't:
  - Mark a recommendation as "done"
  - Track whether acting on a recommendation improved revenue
  - Set a target price and monitor if sales held
  - → The loop is: see recommendation → act offline → come back and see if numbers changed. This is fine for MVP but feels incomplete.

- [x] **"Quick wins" vs "watch outs" labels**: If the visual distinction isn't crystal clear, first-time users may read declining products as opportunities

- [x] **Technical jargon not explained inline**:
  - "Elasticity": appears on Pricing page; most business owners don't know what it means
  - "MAD" (anomaly detection): not visible to users, but the anomaly explanations should be in plain English only ✅ (auto_label handles this)
  - "Cash Cows" / "Hidden Gems": intuitive in BCG context, but do coffee shop owners know BCG matrix?

- [x] **No "what should I do first?" guide**: A first-time user sees 5–8 recommendations. There's no "start here" prompt. The ranking by dollar impact is good UX, but a first-time user may not realize that ordering = priority.

- [x] **Impact range not contextualized**: "$18/month" sounds small. "That's $216/year, just from one product" would land differently. No annualized figure shown.

- [x] **No confirmation of action taken**: After dismissing a recommendation, there's no way to say "I did this and here's what happened." The tool doesn't close the loop.

---

## Biggest UX Gaps

**1. The "Why?" gap**
Most recommendation details don't explain the underlying data in one sentence. "Espresso is your 3rd most-sold item but 5th in price" is data the user can verify. That's trust-building. More recommendations should lead with the data observation, not the conclusion.

**2. The dollar impact trust gap**
"Could add ~$18/month" will be immediately questioned. What margins did you use? Is this profit or revenue? One line — "Based on your actual sales volume; assumes ~65% margin since cost data wasn't uploaded" — would dramatically increase trust.

**3. The "now what?" gap**
After reading all recommendations, a user doesn't have a clear sequence of next steps. A simple "Here's your 3-step plan for this week: 1) test Espresso price, 2) promote Croissant bundle, 3) monitor declining items" would transform this from a report into a workflow.

---

## What Would Make It Crystal Clear

- [ ] **"Based on X transactions from [date range]" on every recommendation** — provenance for each recommendation
- [ ] **Inline margin disclosure**: "~$18/month (assuming 65% margin — upload cost data for exact figures)"
- [ ] **"I did this" button**: Mark a recommendation as acted on; revisit in 2 weeks to see outcome
- [ ] **Priority ordering annotation**: "Start here → then here → then here"
- [ ] **Seasonal caveat on clustering**: "Note: 'Low Activity' may reflect seasonal patterns, not permanent performance"
- [ ] **Model selection on forecast**: "Forecast method: Linear trend (need 60+ days for more accurate models)"
- [ ] **One-line explainer on confidence badges**: "Worth testing = based on 25–49 transactions; Strong signal = 50+"

---

## Demo Script Recommendation

Don't start with the upload. Start with the outcome:

> "Let me show you what a coffee shop owner found out last week."  
> [Show pre-loaded demo with familiar product names]  
> "Their top recommendation was to raise their espresso price by 18 cents — not because of guesswork, but because espresso was selling in the top third of all their products while being priced in the bottom third. The model estimated that would add $23/month in profit."  
> "Then I'll show you how to get this for your own data — takes 2 minutes."

This script builds trust BEFORE asking for data, not after.
