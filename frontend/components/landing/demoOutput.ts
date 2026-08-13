/* Figures shown on the landing page, taken from Kern's own engine run against
   the two bundled demo exports. Nothing here is illustrative — every number
   below was produced by backend/engine on the datasets that
   `GET /demo-data/{coffee_shop|retail}` serves.
   ────────────────────────────────────────────────────────────────────────────
   To re-verify after any change to backend/engine/demo.py or the analysis
   modules, run from the repo root:

     python - <<'PY'
     import sys; sys.path.insert(0, 'backend')
     from engine.demo import _generate_demo_df, _generate_retail_demo_df
     from engine.pricing import _get_price_recommendations
     from engine.insights import _find_rising_stars, _find_declining_products
     from engine.clusters import _get_product_clusters
     for name, fn in [('coffee', _generate_demo_df), ('retail', _generate_retail_demo_df)]:
         df = fn()
         print(name, len(df), df.order_id.nunique(), df['product'].nunique(), round(df.revenue.sum()))
         print(_get_price_recommendations(df)[:1])
         print(_find_rising_stars(df).head(1).to_dict('records'))
         print(_find_declining_products(df)[:1])
         print(_get_product_clusters(df).category.value_counts().to_dict())
     PY

   Both generators use a fixed seed and lay their transactions out as fixed
   offsets behind `today`, so totals, product ranks and the 30-day momentum
   windows are reproducible on any date. Day-of-week and hour-of-day are NOT
   stable across dates (the block slides through the calendar) and the demo's
   hours are drawn uniformly anyway — which is why no staffing figure is quoted
   anywhere on this page. */

export interface DemoDataset {
  /** Filename as served by the demo-data endpoint. */
  file: string
  lineItems: string
  orders: string
  products: string
  window: string
  revenue: string
}

export const COFFEE: DemoDataset = {
  file: 'demo_coffee_shop.csv',
  lineItems: '1,400',
  orders: '929',
  products: '18',
  window: '6 months',
  revenue: '$13,327',
}

export const RETAIL: DemoDataset = {
  file: 'demo_retail_store.csv',
  lineItems: '1,200',
  orders: '779',
  products: '20',
  window: '6 months',
  revenue: '$52,204',
}

/* ── Pricing Check, top row, coffee-shop demo ──
   engine/pricing.py → "↑ Raise Price", Espresso, 202 transactions, 387 units.
   The engine could not fit an elasticity here (the export has no real price
   variation), so it caps the suggestion at a conservative +3% and asks for a
   two-week test rather than asserting a dollar outcome. That refusal is the
   point of the card, so it is shown, not hidden. */
export const PRICING_TOP = {
  view: 'Pricing Check',
  product: 'Espresso',
  action: 'Raise price',
  current: '$3.49',
  suggested: '$3.60',
  deltaPct: '+3%',
  units: '387 units',
  transactions: '202',
  summary:
    'Demand sits in the top third of your menu while the price sits in the bottom third. Test the increase for two weeks and watch unit volume.',
  basis: [
    { label: 'Sample', value: '202 transactions' },
    { label: 'Window', value: 'Trailing 6 months' },
    { label: 'Volume', value: '387 units' },
    { label: 'Price sensitivity', value: 'Not measurable here' },
  ],
  /* engine/pricing.py emits this reasoning when price variation is too thin to
     regress against. Reworded for the landing page only. */
  caveat:
    'There is not enough price variation in this export to tell how customers respond, so Kern proposes a 2-week test rather than a projection.',
} as const

/* ── What's Selling, coffee-shop demo ── engine/insights.py */
export const RISING_TOP = {
  view: "What's Selling",
  product: 'Americano',
  growth: '+38%',
  recentRevenue: '$207',
  recentUnits: '52 units',
  window: 'last 30 days vs the 30 before',
} as const

export const DECLINING_TOP = {
  view: "What's Selling",
  product: 'Flat White',
  decline: '−67%',
  from: '$200',
  to: '$66',
  /* engine/insights.py classifies the drop as `structural` rather than
     seasonal, and reports it against a −13% move in the business overall. */
  classification: 'Structural, not seasonal',
  context: 'Business overall moved −13% over the same window',
} as const

/* ── Product clusters, coffee-shop demo ── engine/clusters.py (K-Means) */
export const COFFEE_CLUSTERS = {
  stars: '5',
  cashCows: '11',
  lowActivity: '2',
} as const

/* ── Retail demo, used in the audience split ── */
export const RETAIL_RISING = {
  product: 'Running Sneakers',
  growth: '+45%',
  recentRevenue: '$1,176',
} as const

export const RETAIL_DECLINING = {
  product: 'Denim Jeans',
  decline: '−53%',
  from: '$1,531',
  to: '$717',
} as const
