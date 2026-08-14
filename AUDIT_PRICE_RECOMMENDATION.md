# Price Recommendation Audit — Merged Elasticity Architecture

> Traced end-to-end against the coffee demo (`backend/engine/demo.py`, seed 42 — 4,375 transactions, 19 products, ~6-month span).

---

## Architecture

There is **one** elasticity estimator and **one** price-change sizing function. Both live in
`backend/engine/pricing_core.py`. Two product surfaces consume them with different
selection criteria:

```
                     backend/engine/pricing_core.py
                     ├── estimate_elasticity(df, product)      → dict
                     ├── elasticity_to_price_delta(e, dir)     → (pct, label)
                     └── _elasticity_test_price(price, slope)  → (suggested, increase)
                                    │
              ┌─────────────────────┴─────────────────────┐
              │                                           │
   recommendations.py                              pricing.py
   _build_pricing_rec (Path A)                     _get_price_recommendations
   → Action Center                                 → Price Intelligence page
   HIGH BAR, few results                           BROWSE-ALL, up to 8 recs
              │                                           │
   action_center.py::_prescribe_low_activity      (discount ladder, same estimator)
   recommendations.py::_build_rising_rec          (price_tolerant gate, same estimator)
```

**Why this exists.** Before the merge, `recommendations.py` and `pricing.py` each had their
own estimator and their own percentage formula. The same product could be shown two
different recommendations depending on which page rendered it — Drip Coffee came out at
elasticity −0.509 / +6.2% / $2.50 on the Action Center and +0.497 / +8% / $2.53 on Price
Intelligence. `tests/test_pricing_consistency.py` now fails loudly if the two ever diverge
again.

**What did *not* merge:** selection and gating. Each page decides *which* products get a
recommendation on its own terms, and the two frontend pages and their API endpoints remain
separate.

### Sign convention

The two callers historically disagreed on sign, so `estimate_elasticity` returns both:

| Field | Meaning | Consumed by |
|---|---|---|
| `slope` | Signed OLS coefficient, e.g. `−0.497`. Negative = normal downward demand. | `recommendations.py` (`price_tolerant` is `slope > −0.7`), `_elasticity_test_price` |
| `elasticity` | Magnitude, `abs(slope)` clipped to `[0.05, 2.5]`, e.g. `0.497`. | `pricing.py`, `action_center.py` (threshold comparisons like `≥ 1.2`) |

Feeding a magnitude to a function expecting a signed slope silently produces the maximum
price bump for every product. The convention is documented at the top of `pricing_core.py`
and asserted in the consistency tests.

---

## Elasticity estimation — `estimate_elasticity`

Daily-aggregated, quantile-binned log-log OLS. Daily aggregation and binning are what make
this robust to transaction-level noise; a raw per-transaction regression mostly fits
within-day scatter.

| Gate | Threshold | Failure mode |
|---|---|---|
| Transactions | ≥ 10 | `valid=False` |
| Daily observations | ≥ 5 | `valid=False` |
| Price coefficient of variation | ≥ 0.03 | `valid=False` — "prices appear fixed" |
| Price bins after filtering (≥2 obs each) | ≥ 5 | `valid=False` |
| Degrees of freedom | ≥ 3 | `valid=False` |
| t-stat | ≥ `max(1.8, 1.645 + 2.0/dof)` | `is_significant=False` |
| R² | ≥ 0.20 | `is_significant=False` |
| Elasticity cap | 2.5 (CI cap 3.5) | clipped, flagged "directional only" in `note` |

`valid` and `is_significant` are distinct: `valid=False` means no estimate exists at all;
`is_significant=False` means the fit ran but the price/volume relationship is too weak to
trust. Callers collapse both to "unusable" via `pricing.py::_usable_elasticity`.

**The fixed-price problem persists.** Most real POS exports carry fixed menu prices, so
CV < 3% and elasticity is unavailable. On the coffee demo, **1 of 19 products** (Drip
Coffee) clears every gate. This is honest, not broken — but it means most businesses see
the fallback percentages below, and the messaging is written accordingly.

---

## Price sizing — `elasticity_to_price_delta`

Continuous, not a step ladder. Two products with similar elasticity can no longer receive
wildly different recommendations.

**Raise** — two linear segments, 12% at fully inelastic down to 1.5% at the cap:

| elasticity | 0.0 | 0.35 | 0.5 | 0.7 | 1.0 | 1.5 | 2.0 | 2.5+ |
|---|---|---|---|---|---|---|---|---|
| raise % | 12.00 | 8.00 | 6.29 | 4.00 | 3.58 | 2.89 | 2.19 | 1.50 |

The knee at 0.7 is the Action Center's `price_tolerant` boundary. Path A never sees
elasticity above it, so the second segment only affects Price Intelligence.

**Lower** — the mirror image; small cut when a cut won't buy volume, larger once demand is
clearly elastic:

| elasticity | 0.0 | 0.35 | 0.7 | 1.0 | 1.2+ |
|---|---|---|---|---|---|
| lower % | 4.00 | 5.75 | 7.50 | 9.00 | 10.00 |

Below 0.7 the label carries the caveat: *"a price cut likely won't drive volume —
investigate visibility or product-market fit first."*

**Fallbacks when elasticity is unavailable:** raise 3%, lower 5%, both with explicit
"we couldn't measure this" language.

`_elasticity_test_price` wraps the raise direction in dollar space for the Action Center:
caps the increase at `min(25% of price, $2.00)`, floors it at $0.05, and rounds the
suggested price to the nearest nickel. Price Intelligence rounds to the cent instead, so
the two pages can differ by a few cents on the *displayed* price while agreeing exactly on
elasticity and percentage. That is presentation, not math.

---

## Selection criteria — deliberately different per page

### Action Center — `_build_pricing_rec` Path A (high bar)

All must pass:
1. 3+ distinct price points
2. Product is not in a significant decline (shared gate with Path B)
3. `valid` **and** `is_significant` from the canonical estimator
4. `price_tolerant` — `slope > −0.7`
5. `relative_standing` — price is a low outlier (|z| > 1.5, direction low)
6. Monthly impact ≥ `min_impact` (1% of monthly revenue, floored at $50)

**On the coffee demo this fires zero times.** Drip Coffee is the only product reaching the
calculation and it dies at the `min_impact` gate. Path B (portfolio comparison) handles
single-price businesses separately and carries no elasticity.

### Price Intelligence — `_get_price_recommendations` (browse-all)

| Branch | Trigger | Min txns |
|---|---|---|
| ↑ Raise Price | qty ≥ 65th %ile AND price ≤ 35th %ile | 25 |
| ↓ Consider Lowering | price ≥ 65th %ile AND qty ≤ 35th %ile | 20 |
| ✓ Maintain | price ≥ 65th %ile AND (margin ≥ 65th %ile with cost data, else qty ≥ 65th %ile) | 20 |

Sorted by priority, capped at 8. Margin-aware messaging appears when cost data exists —
including the note that renegotiating supplier cost may beat raising customer price when a
product's margin sits below the portfolio median.

---

## Worked example — Drip Coffee (coffee demo)

| | Before merge | After merge |
|---|---|---|
| Action Center elasticity | −0.509 (raw per-txn OLS) | −0.497 signed / 0.497 magnitude |
| Price Intelligence elasticity | +0.497 (binned daily OLS) | 0.497 |
| Action Center raise % | 6.18% | **6.3183%** |
| Price Intelligence raise % | 8% (step ladder) | **6.3183%** |
| Suggested price | $2.50 vs $2.53 | $2.50 (nickel) vs $2.49 (cent) |

Fit quality: R² = 0.312, t = 1.91, 95% CI [0.05, 1.02]. The wide CI is why the copy says
"test for 2 weeks" rather than "this will earn you $X".

---

## Honest assessment: what is data-driven and what is not

- ✅ **Which product** gets a recommendation — percentile comparison across this business's
  own products, both pages.
- ✅ **How much** to change the price — now derived from the product's own measured
  elasticity on a continuous curve. The old hardcoded +5% / step-ladder percentages are gone.
- ✅ **Consistency** — one implementation, enforced by test.
- ⚠️ **Dollar impact** — real quantity, but a **0.65 gross-margin fallback** when no cost
  data is uploaded (`action_center.py:279`), and it is still never surfaced to the user.
- ⚠️ **Volume response** — Price Intelligence applies `adj_qty = qty × (1 − e × pct)` in its
  revenue signal, but the Action Center's impact estimate assumes no volume loss beyond a
  flat 0.85 haircut in `estimate_monthly_impact`.
- ❌ **Confounders** — seasonality, day-of-week effects and promotional periods are not
  removed from the price/volume relationship. A promo-driven price dip that coincides with a
  volume spike reads as elasticity. The t-stat/R² gate filters the worst of it; a controlled
  price experiment is the honest fix.

---

## Remaining gaps for customer trust

- [ ] Disclose the 65% margin fallback wherever an impact figure derives from it
- [x] Explain why *this* percentage — `elasticity_to_price_delta` returns a human-readable
      label, rendered as "Why this %:" on Price Intelligence
- [x] Show transaction counts — `n_txn` / `transaction_count` ship on every rec
- [ ] Surface confidence on the Action Center card, not just the Pricing page
- [ ] Exclude known promotional periods from the elasticity fit
- [ ] Show the operational shape of "test first" — what to measure, when to stop

---

## Test coverage

| File | Covers |
|---|---|
| `tests/test_pricing_elasticity.py` | 15 cases on `_elasticity_test_price` — band, monotonicity, floor, caps, nickel rounding, positive-slope clamping |
| `tests/test_pricing_consistency.py` | 6 cases — shared function identity, per-product elasticity and percentage equality across all 19 demo products, the rendered Price Intelligence output matching `pricing_core`, and the Drip Coffee worked example |

The consistency tests compare **every product in the dataset**, not only products that
produce a recommendation on both pages. That intersection is currently empty (Path A does
not fire on the demo), and a test over an empty set passes vacuously — which is precisely
how the original divergence survived.
