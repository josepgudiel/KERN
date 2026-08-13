'use client'

import Image from 'next/image'
import { useReveal } from './useReveal'
import { COFFEE, RETAIL, RISING_TOP, RETAIL_DECLINING } from './demoOutput'

interface Column {
  id: string
  heading: string
  photo: string
  alt: string
  body: string[]
  metric: { value: string; label: string; source: string; positive: boolean }
}

/* Two illustrations, one product. Each column earns its claim with a figure the
   engine actually produced on that column's demo export rather than with a
   sector adjective — the food column is a rising item, the retail column is a
   decline caught early, because those are the two shapes of decision each side
   tends to be making. Neither column is a gate: the sectors are worked
   examples, and the lede above them says so. */
const COLUMNS: Column[] = [
  {
    id: 'food',
    heading: 'Food and drink',
    photo: '/photos/coffee-counter.jpg',
    alt: 'A coffee shop service counter with espresso equipment and a chalkboard menu overhead',
    body: [
      'Cafes, bakeries, bars, food trucks: a short menu, high transaction counts and prices that have not moved in two years is the exact shape Kern reads best. Items are ranked against each other on both demand and price, so the ones quietly carrying the counter separate from the ones just occupying the board.',
      'Momentum is checked against each item’s own prior month, not against the shop next door.',
    ],
    metric: {
      value: RISING_TOP.growth,
      label: `${RISING_TOP.product} rising, ${RISING_TOP.recentRevenue} over the ${RISING_TOP.window}`,
      source: `${COFFEE.file} · ${COFFEE.lineItems} line items · ${COFFEE.window}`,
      positive: true,
    },
  },
  {
    id: 'retail',
    heading: 'Retail and goods',
    photo: '/photos/retail-interior.jpg',
    alt: 'Interior of a small independent retail store, with clothing rails and shelved stock',
    body: [
      'Shops, boutiques, studios, salons carrying product: wider catalogues, higher ticket sizes and slower turns change which signal matters, so a single line going quiet costs more than a whole shelf drifting. Kern separates a structural decline from a seasonal dip before it puts anything in front of you.',
      'Stock decisions carry the same supporting detail as pricing ones: sample size, date window and confidence.',
    ],
    metric: {
      value: RETAIL_DECLINING.decline,
      label: `${RETAIL_DECLINING.product}, ${RETAIL_DECLINING.from} → ${RETAIL_DECLINING.to} in 30 days`,
      source: `${RETAIL.file} · ${RETAIL.lineItems} line items · ${RETAIL.window}`,
      positive: false,
    },
  },
]

export default function AudienceSplit() {
  const head = useReveal<HTMLDivElement>()
  const columns = useReveal<HTMLDivElement>()

  return (
    <section className="lp-band-shell">
      <div className="lp-wrap" style={{ paddingTop: '84px', paddingBottom: '84px' }}>
        <div ref={head.ref} className={head.className} style={{ maxWidth: '48ch', marginBottom: '44px' }}>
          <span className="lp-eyebrow" style={{ marginBottom: '14px' }}>
            Who it is for
          </span>
          <h2 style={{ maxWidth: '22ch', marginBottom: '16px' }}>Built for the operator, not the analyst.</h2>
          <p style={{ margin: 0, fontSize: '0.94rem' }}>
            If your business runs a POS, Kern reads its export. The two below are
            worked examples rather than a list of who qualifies: the same pass
            runs on a hardware store, a salon, a gym or a food truck.
          </p>
        </div>

        <div
          ref={columns.ref}
          className={`lp-audience lp-reveal-group ${columns.className}`}
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, minmax(0, 1fr))',
            gap: '56px',
            alignItems: 'start',
          }}
        >
          {COLUMNS.map(col => (
            <div key={col.id}>
              <figure className="lp-figure" style={{ marginBottom: '24px' }}>
                <div style={{ position: 'relative', aspectRatio: '16 / 10' }}>
                  <Image
                    src={col.photo}
                    alt={col.alt}
                    fill
                    sizes="(max-width: 900px) 100vw, 46vw"
                    style={{ objectFit: 'cover' }}
                  />
                </div>
              </figure>

              <h3 style={{ margin: '0 0 14px', fontSize: '1.32rem' }}>{col.heading}</h3>

              {col.body.map(p => (
                <p key={p.slice(0, 24)} style={{ margin: '0 0 14px', fontSize: '0.94rem' }}>
                  {p}
                </p>
              ))}

              {/* The example, ruled off rather than boxed — it is evidence for
                  the paragraph above it, not a separate stat card. */}
              <div style={{ marginTop: '22px', paddingTop: '18px', borderTop: '2px solid var(--lp-accent)' }}>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '13px', flexWrap: 'wrap' }}>
                  <span
                    className="lp-num"
                    style={{
                      fontSize: 'clamp(1.7rem, 3vw, 2.1rem)',
                      color: col.metric.positive ? 'var(--green)' : 'var(--red)',
                    }}
                  >
                    {col.metric.value}
                  </span>
                  <span style={{ fontFamily: 'var(--font-body)', fontSize: '0.88rem', color: 'var(--lp-ink)', minWidth: 0 }}>
                    {col.metric.label}
                  </span>
                </div>
                <div className="lp-label" style={{ marginTop: '10px' }}>
                  {col.metric.source}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
