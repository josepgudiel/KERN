'use client'

import { ArrowRight } from 'lucide-react'
import ActionCardPreview from './ActionCardPreview'
import { useReveal } from './useReveal'
import { COFFEE, DECLINING_TOP, RISING_TOP, COFFEE_CLUSTERS } from './demoOutput'

interface SeeItInActionProps {
  onDemo: () => void
  demoLoading: boolean
}

/* The worked example. Everything here is Kern's own output on the file behind
   the demo button, labelled as such — there is no customer quote on this page
   because there is no customer to quote yet, and a testimonial in this slot
   would be the one thing a visitor could catch us on.

   The card opens with its supporting detail already expanded: the disclosure
   has done its job in the hero, and hiding the figures in the section named
   after showing them would be a joke at the reader's expense. */
export default function SeeItInAction({ onDemo, demoLoading }: SeeItInActionProps) {
  const head = useReveal<HTMLDivElement>()
  const body = useReveal<HTMLDivElement>()

  const alsoReturned: [string, string][] = [
    [
      `${RISING_TOP.product} is rising`,
      `${RISING_TOP.growth} over the ${RISING_TOP.window} · ${RISING_TOP.recentRevenue} and ${RISING_TOP.recentUnits}`,
    ],
    [
      `${DECLINING_TOP.product} is falling`,
      `${DECLINING_TOP.decline} · ${DECLINING_TOP.from} → ${DECLINING_TOP.to} · ${DECLINING_TOP.classification}`,
    ],
    [
      'Menu split into clusters',
      `${COFFEE_CLUSTERS.stars} Stars · ${COFFEE_CLUSTERS.cashCows} Cash Cows · ${COFFEE_CLUSTERS.lowActivity} Low Activity`,
    ],
    [
      'Revenue projected out 8 weeks',
      'Flat trend, $73.23/day average, range shown',
    ],
  ]

  return (
    <section id="demo" className="lp-band">
      <div className="lp-wrap" style={{ paddingTop: '84px', paddingBottom: '84px' }}>
        <div
          ref={head.ref}
          className={head.className}
          style={{
            display: 'flex',
            alignItems: 'flex-end',
            justifyContent: 'space-between',
            gap: '40px',
            flexWrap: 'wrap',
            paddingBottom: '28px',
            marginBottom: '44px',
            borderBottom: '1px solid var(--lp-line)',
          }}
        >
          <div>
            <span className="lp-eyebrow" style={{ marginBottom: '14px' }}>
              See it in action
            </span>
            <h2 style={{ maxWidth: '20ch' }}>One file in. This is what comes back.</h2>
          </div>
          <p style={{ maxWidth: '34ch', fontSize: '0.92rem', margin: 0 }}>
            Live demo output, not a customer story. Press the button and you get
            these exact screens.
          </p>
        </div>

        <div
          ref={body.ref}
          className={`lp-demo lp-reveal-group ${body.className}`}
          style={{
            display: 'grid',
            gridTemplateColumns: 'minmax(0, 1fr) minmax(0, 1fr)',
            gap: '56px',
            alignItems: 'start',
          }}
        >
          {/* Input, stated plainly so the output has something to be measured
              against. */}
          <div>
            <div className="lp-label" style={{ marginBottom: '16px' }}>
              The input
            </div>

            <dl style={{ margin: '0 0 34px', borderTop: '1px solid var(--lp-line)' }}>
              {[
                ['File', COFFEE.file],
                ['Line items', COFFEE.lineItems],
                ['Orders', COFFEE.orders],
                ['Products', COFFEE.products],
                ['Window', COFFEE.window],
                ['Revenue', COFFEE.revenue],
              ].map(([k, v]) => (
                <div
                  key={k}
                  style={{
                    display: 'grid',
                    gridTemplateColumns: '112px 1fr',
                    gap: '18px',
                    padding: '10px 0',
                    borderBottom: '1px solid var(--lp-line)',
                  }}
                >
                  <dt className="lp-label" style={{ paddingTop: '2px' }}>
                    {k}
                  </dt>
                  <dd className="lp-data" style={{ margin: 0, fontSize: '0.84rem', color: 'var(--lp-ink)' }}>
                    {v}
                  </dd>
                </div>
              ))}
            </dl>

            <div className="lp-label" style={{ marginBottom: '16px' }}>
              Also returned on the same pass
            </div>

            <ul style={{ listStyle: 'none', margin: 0, padding: 0, borderTop: '1px solid var(--lp-line)' }}>
              {alsoReturned.map(([title, detail]) => (
                <li key={title} style={{ padding: '13px 0', borderBottom: '1px solid var(--lp-line)' }}>
                  <div
                    style={{
                      fontFamily: 'var(--font-heading)',
                      fontSize: '0.95rem',
                      fontWeight: 600,
                      color: 'var(--lp-ink)',
                      marginBottom: '4px',
                    }}
                  >
                    {title}
                  </div>
                  <div style={{ fontFamily: 'var(--font-body)', fontSize: '0.85rem', color: 'var(--lp-ink-2)', lineHeight: 1.55 }}>
                    {detail}
                  </div>
                </li>
              ))}
            </ul>

            <button
              type="button"
              onClick={onDemo}
              disabled={demoLoading}
              className="btn-lp"
              style={{ marginTop: '28px' }}
            >
              {demoLoading ? 'Loading demo…' : 'Run this dataset yourself'}
              {!demoLoading && <ArrowRight size={15} strokeWidth={2.25} aria-hidden />}
            </button>
          </div>

          <div>
            <div className="lp-label" style={{ marginBottom: '16px' }}>
              The top-ranked action
            </div>
            <ActionCardPreview variant="full" />
          </div>
        </div>
      </div>
    </section>
  )
}
