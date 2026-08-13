'use client'

import { useReveal } from './useReveal'

/* Formats Kern reads, not customers Kern has. These are set as plain wordmarks
   in the page's own type rather than as vendor logos: a row of borrowed brand
   marks reads as a customer carousel, which would be a claim nobody here is
   entitled to make. The systems listed are the ones whose column names
   engine/data_loader.py carries candidates for. */

const SOURCES = ['Square', 'Toast', 'Shopify', 'Clover', 'Lightspeed', 'Any CSV export']

export default function CompatibilityStrip() {
  const reveal = useReveal<HTMLDivElement>()

  return (
    <section className="lp-band" aria-label="Supported point-of-sale exports">
      <div className="lp-wrap" style={{ paddingTop: '30px', paddingBottom: '30px' }}>
        <div
          ref={reveal.ref}
          className={`lp-compat ${reveal.className}`}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '28px 40px',
            flexWrap: 'wrap',
          }}
        >
          <span className="lp-label" style={{ flexShrink: 0 }}>
            Reads exports from
          </span>

          <ul
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '36px',
              flexWrap: 'wrap',
              listStyle: 'none',
              margin: 0,
              padding: 0,
            }}
          >
            {SOURCES.map((name, i) => (
              <li
                key={name}
                style={{
                  fontFamily: 'var(--font-heading)',
                  fontSize: '1.02rem',
                  fontWeight: 600,
                  letterSpacing: '-0.01em',
                  /* The catch-all sits in accent so the row ends on the claim
                     that actually matters — the named systems are examples. */
                  color: i === SOURCES.length - 1 ? 'var(--lp-accent)' : 'var(--lp-ink-3)',
                  whiteSpace: 'nowrap',
                }}
              >
                {name}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  )
}
