'use client'

import { useRef, useState, type KeyboardEvent, type ReactNode } from 'react'
import { Badge } from '@/components/ui'
import { useReveal } from './useReveal'
import { COFFEE, COFFEE_CLUSTERS, DECLINING_TOP, RISING_TOP } from './demoOutput'

interface Tab {
  id: string
  label: string
  question: string
  copy: string
  /* What the view reads out of the upload, in the reader's terms. Named
     techniques belong in the repo, not on a page whose whole argument is that
     the operator does not have to be an analyst. */
  inputs: string
  /* Real output from the bundled coffee-shop export, rendered with the same
     parts the dashboard uses. Where the demo cannot support a figure, the
     panel shows the output's actual fields instead of inventing one. */
  panel: ReactNode
}

const rowStyle = {
  display: 'flex',
  alignItems: 'baseline',
  justifyContent: 'space-between',
  gap: '16px',
  padding: '11px 0',
  borderBottom: '1px solid var(--lp-line)',
} as const

const dataStyle = {
  fontFamily: 'var(--font-mono)',
  fontVariantNumeric: 'tabular-nums' as const,
  fontSize: '0.8rem',
  color: 'var(--lp-ink)',
}

/* engine/pricing.py, coffee-shop demo — the five rows it returns, in order. */
const PRICE_ROWS: [string, string, string, 'up' | 'down'][] = [
  ['Americano', '$4.00', '$4.12', 'up'],
  ['Croissant', '$3.50', '$3.60', 'up'],
  ['Espresso', '$3.49', '$3.60', 'up'],
  ['Avocado Toast', '$8.92', '$8.48', 'down'],
  ['BLT Sandwich', '$8.46', '$8.04', 'down'],
]

/* engine/forecast.py, coffee-shop demo — a flat trend at ~$73/day with a wide
   range, which is the honest read on 1,400 line items. The range is shown
   rather than trimmed: a projection without one is a guess in a suit. */
const FORECAST_ROWS: [string, string][] = [
  ['Trend', 'Flat (+0.1% / week)'],
  ['Avg daily revenue', '$73.23'],
  ['Next 7 days', '$71 – $75 / day'],
  ['Could land between', '$31 – $113 / day'],
]

const TABS: Tab[] = [
  {
    id: 'pricing',
    label: 'Pricing Check',
    question: 'Which prices can move, and by how much?',
    copy:
      'Every product is placed against everything else you sell on price and on demand. Items carrying top-third demand at a bottom-third price are flagged to raise; items priced high and moving slowly are flagged to test downward.',
    inputs:
      'Where your prices have varied enough, Kern measures how sales responded. Where they have not, it goes on where the product sits against the rest of your range.',
    panel: (
      <div>
        <div style={{ ...rowStyle, paddingTop: 0, borderBottom: '1px solid var(--lp-line-2)' }}>
          <span className="lp-label">Product</span>
          <span className="lp-label">Current → suggested</span>
        </div>
        {PRICE_ROWS.map(([product, current, suggested, dir]) => (
          <div key={product} style={rowStyle}>
            <span style={{ fontFamily: 'var(--font-body)', fontSize: '0.88rem', color: 'var(--lp-ink)' }}>
              {product}
            </span>
            <span style={{ ...dataStyle, whiteSpace: 'nowrap' }}>
              <span style={{ color: 'var(--lp-ink-2)' }}>{current}</span>
              {'  →  '}
              <span style={{ color: dir === 'up' ? 'var(--green)' : 'var(--amber)' }}>{suggested}</span>
            </span>
          </div>
        ))}
        <p style={{ margin: '14px 0 0', fontSize: '0.82rem' }}>
          Each row opens onto its transaction count and unit volume, plus how
          sales responded to price where your export shows enough movement to
          tell.
        </p>
      </div>
    ),
  },
  {
    id: 'selling',
    label: "What's Selling",
    question: 'What is carrying the business, and what is slipping?',
    copy:
      'Products are clustered into Stars, Cash Cows, Hidden Gems and Low Activity, then checked for momentum against their own prior 30 days. Declines are separated into structural and seasonal so a normal quiet month does not read as a crisis.',
    inputs:
      'Revenue and unit volume across the whole catalogue, then each product measured against its own previous 30 days.',
    panel: (
      <div>
        <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap', marginBottom: '20px' }}>
          <Badge toneName="positive" shape="tag">{COFFEE_CLUSTERS.stars} Stars</Badge>
          <Badge toneName="info" shape="tag">{COFFEE_CLUSTERS.cashCows} Cash Cows</Badge>
          <Badge toneName="neutral" shape="tag">{COFFEE_CLUSTERS.lowActivity} Low Activity</Badge>
        </div>

        <div style={{ ...rowStyle, borderBottom: '1px solid var(--lp-line-2)' }}>
          <span style={{ minWidth: 0 }}>
            <span style={{ display: 'block', fontFamily: 'var(--font-body)', fontSize: '0.9rem', color: 'var(--lp-ink)' }}>
              {RISING_TOP.product}
            </span>
            <span style={{ display: 'block', fontSize: '0.8rem', color: 'var(--lp-ink-2)', marginTop: '3px' }}>
              Rising · {RISING_TOP.recentRevenue} over {RISING_TOP.window}
            </span>
          </span>
          <span className="lp-num" style={{ fontSize: '1.3rem', color: 'var(--green)' }}>
            {RISING_TOP.growth}
          </span>
        </div>

        <div style={{ ...rowStyle, borderBottom: 'none' }}>
          <span style={{ minWidth: 0 }}>
            <span style={{ display: 'block', fontFamily: 'var(--font-body)', fontSize: '0.9rem', color: 'var(--lp-ink)' }}>
              {DECLINING_TOP.product}
            </span>
            <span style={{ display: 'block', fontSize: '0.8rem', color: 'var(--lp-ink-2)', marginTop: '3px' }}>
              {DECLINING_TOP.from} → {DECLINING_TOP.to} · {DECLINING_TOP.classification}
            </span>
          </span>
          <span className="lp-num" style={{ fontSize: '1.3rem', color: 'var(--red)' }}>
            {DECLINING_TOP.decline}
          </span>
        </div>
      </div>
    ),
  },
  {
    id: 'staffing',
    label: 'When to Staff',
    question: 'Which days and hours actually carry the week?',
    copy:
      'Revenue and order count are laid out by day of week and by hour, with the peak and the quietest period named and a shift move suggested between them. It answers the rota question directly rather than handing back a heatmap to interpret.',
    inputs:
      'Every timestamped order in your upload, grouped by day of the week and by hour of the day.',
    panel: (
      <div>
        <div style={{ ...rowStyle, paddingTop: 0, borderBottom: '1px solid var(--lp-line-2)' }}>
          <span className="lp-label">Returns</span>
          <span className="lp-label">From your export</span>
        </div>
        {[
          ['Revenue by day of week', '7 rows, avg per week'],
          ['Orders by day of week', '7 rows, avg per week'],
          ['Peak and slowest day', 'Named, with the gap'],
          ['Suggested shift move', 'Hours, from slow to peak'],
        ].map(([field, shape]) => (
          <div key={field} style={rowStyle}>
            <span style={{ fontFamily: 'var(--font-body)', fontSize: '0.88rem', color: 'var(--lp-ink)' }}>
              {field}
            </span>
            <span style={{ ...dataStyle, color: 'var(--lp-ink-2)', textAlign: 'right' }}>{shape}</span>
          </div>
        ))}
        {/* Straight answer rather than a fabricated peak day: the bundled demo
            spreads its timestamps evenly, so it has no staffing pattern to
            quote. Saying so is the same behaviour the product has. */}
        <p style={{ margin: '14px 0 0', fontSize: '0.82rem' }}>
          No figures are quoted here because the bundled demo spreads its
          timestamps evenly and has no real staffing pattern to report. Run it
          on your own export to see this view populated.
        </p>
      </div>
    ),
  },
  {
    id: 'forecast',
    label: 'What to Expect',
    question: 'What does next month look like if nothing changes?',
    copy:
      'A revenue projection out to eight weeks, showing a range rather than a single confident line. Per-product trends sit underneath it, so a flat total that hides one product collapsing and another climbing does not read as calm.',
    inputs:
      'The shape of your daily revenue over the whole upload, carried forward with the spread it has actually shown.',
    panel: (
      <div>
        <div style={{ ...rowStyle, paddingTop: 0, borderBottom: '1px solid var(--lp-line-2)' }}>
          <span className="lp-label">Forecast</span>
          <span className="lp-label">{COFFEE.file}</span>
        </div>
        {FORECAST_ROWS.map(([k, v]) => (
          <div key={k} style={rowStyle}>
            <span style={{ fontFamily: 'var(--font-body)', fontSize: '0.88rem', color: 'var(--lp-ink)' }}>
              {k}
            </span>
            <span style={{ ...dataStyle, textAlign: 'right' }}>{v}</span>
          </div>
        ))}
        <p style={{ margin: '14px 0 0', fontSize: '0.82rem' }}>
          That range is wide because {COFFEE.lineItems} line items is not much
          history. Kern shows the width rather than reporting the midpoint as a
          number you can bank.
        </p>
      </div>
    ),
  },
]

export default function FeatureShowcase() {
  const [active, setActive] = useState(0)
  const tabRefs = useRef<(HTMLButtonElement | null)[]>([])
  const reveal = useReveal<HTMLDivElement>()

  function onKeyDown(e: KeyboardEvent<HTMLDivElement>) {
    const last = TABS.length - 1
    let next: number | null = null
    if (e.key === 'ArrowRight' || e.key === 'ArrowDown') next = active === last ? 0 : active + 1
    if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') next = active === 0 ? last : active - 1
    if (e.key === 'Home') next = 0
    if (e.key === 'End') next = last
    if (next === null) return
    e.preventDefault()
    setActive(next)
    tabRefs.current[next]?.focus()
  }

  return (
    <section id="features" className="lp-band">
      <div
        ref={reveal.ref}
        className={`lp-wrap ${reveal.className}`}
        style={{ paddingTop: '84px', paddingBottom: '84px' }}
      >
        <div style={{ maxWidth: '54ch', marginBottom: '38px' }}>
          <span className="lp-eyebrow" style={{ marginBottom: '14px' }}>
            What you get back
          </span>
          <h2 style={{ maxWidth: '20ch', marginBottom: '16px' }}>Four questions, answered on upload.</h2>
          <p style={{ margin: 0 }}>
            Every panel below is real output from the bundled coffee-shop export,
            the same file the demo button loads.
          </p>
        </div>

        {/* Horizontal rail. The active tab carries a solid accent underline
            against a hairline baseline, so the row reads as one ruled edge
            with a marker on it rather than four buttons. */}
        <div
          role="tablist"
          aria-label="Kern's analysis views"
          onKeyDown={onKeyDown}
          className="lp-tabrail"
          style={{
            display: 'flex',
            gap: '34px',
            flexWrap: 'wrap',
            borderBottom: '1px solid var(--lp-line-2)',
            marginBottom: '40px',
          }}
        >
          {TABS.map((t, i) => {
            const on = i === active
            return (
              <button
                key={t.id}
                ref={el => {
                  tabRefs.current[i] = el
                }}
                role="tab"
                id={`feature-tab-${t.id}`}
                aria-selected={on}
                aria-controls={`feature-panel-${t.id}`}
                tabIndex={on ? 0 : -1}
                onClick={() => setActive(i)}
                style={{
                  padding: '0 0 14px',
                  marginBottom: '-1px',
                  background: 'none',
                  border: 'none',
                  borderBottom: `2px solid ${on ? 'var(--lp-accent)' : 'transparent'}`,
                  cursor: 'pointer',
                  fontFamily: 'var(--font-heading)',
                  fontSize: '1.02rem',
                  fontWeight: 600,
                  letterSpacing: '-0.01em',
                  color: on ? 'var(--lp-ink)' : 'var(--lp-ink-3)',
                  transition: 'color 0.18s ease, border-color 0.18s ease',
                  whiteSpace: 'nowrap',
                }}
              >
                {t.label}
              </button>
            )
          })}
        </div>

        {/* All four panels are mounted and stacked in a single grid cell, so
            the switch is a genuine crossfade — the outgoing panel is still on
            screen as the incoming one arrives — and the section is already as
            tall as its tallest panel, which means changing tabs never shifts
            the page under the reader. Only the selected layer is visible to
            assistive technology; the panels hold no focusable content, so
            visibility alone keeps the inactive ones out of the tab order. */}
        <div className="lp-xfade">
          {TABS.map((t, i) => {
            const on = i === active
            return (
              <div
                key={t.id}
                role="tabpanel"
                id={`feature-panel-${t.id}`}
                aria-labelledby={`feature-tab-${t.id}`}
                aria-hidden={!on}
                tabIndex={on ? 0 : -1}
                className={`lp-xfade-layer lp-feature${on ? ' lp-xfade-layer--on' : ''}`}
                style={{
                  display: 'grid',
                  gridTemplateColumns: 'minmax(0, 0.92fr) minmax(0, 1.08fr)',
                  gap: '56px',
                  alignItems: 'start',
                }}
              >
                <div>
                  <h3 style={{ margin: '0 0 16px', fontSize: '1.5rem', maxWidth: '20ch' }}>{t.question}</h3>
                  <p style={{ margin: '0 0 26px', maxWidth: '46ch', fontSize: '0.96rem' }}>{t.copy}</p>
                  <div style={{ paddingTop: '16px', borderTop: '1px solid var(--lp-line)' }}>
                    <div className="lp-label" style={{ marginBottom: '7px' }}>
                      What it reads
                    </div>
                    <p style={{ margin: 0, fontSize: '0.88rem', maxWidth: '42ch' }}>{t.inputs}</p>
                  </div>
                </div>

                <div
                  style={{
                    backgroundColor: 'var(--lp-paper)',
                    border: '1px solid var(--lp-line)',
                    borderRadius: '10px',
                    padding: '24px 26px',
                    boxShadow: 'var(--shadow-sm)',
                  }}
                >
                  {t.panel}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
