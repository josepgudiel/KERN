'use client'

import Image from 'next/image'
import { ArrowRight } from 'lucide-react'
import UploadZone from '@/components/UploadZone'
import type { UploadResponse } from '@/types'
import { useReveal } from './useReveal'
import { COFFEE, RETAIL } from './demoOutput'

interface FinalCTAProps {
  onUploadSuccess: (meta: UploadResponse) => void
  onDemo: (dataset: 'coffee_shop' | 'retail') => void
  demoLoading: string | null
}

/* Row counts here are the real shape of the two bundled exports — see
   components/landing/demoOutput.ts for how to re-verify them against
   backend/engine/demo.py. */
const DEMOS = [
  { id: 'coffee_shop' as const, file: COFFEE.file, meta: `${COFFEE.lineItems} line items · ${COFFEE.window}` },
  { id: 'retail' as const, file: RETAIL.file, meta: `${RETAIL.lineItems} line items · ${RETAIL.window}` },
]

const SPEC: [string, string][] = [
  ['Formats', 'CSV · XLSX'],
  ['Source', 'Square, Toast, Shopify, Clover, any POS export'],
  ['Business', 'Food service, retail, services, anything with a till'],
  ['Account', 'Not required'],
  ['Data', 'Processed for your session, not resold'],
]

/* The closing photographic band and the page's front door. A street-level
   storefront rather than another interior: the page has spent seven sections
   inside the shop, and the last picture is the one the visitor stands outside.
   The upload panel stays on white so the shared UploadZone renders in its
   normal light state against the scrim. */
export default function FinalCTA({ onUploadSuccess, onDemo, demoLoading }: FinalCTAProps) {
  /* The copy column and the upload panel are revealed as one group so the
     page's last screen resolves in a single beat — the closing band is not the
     place to make anyone wait on a sequence. */
  const reveal = useReveal<HTMLDivElement>()

  return (
    <section id="start" className="lp-photo-band">
      <Image
        src="/photos/storefront.jpg"
        alt="A street-level café storefront with pavement seating and a chalkboard sign outside"
        fill
        sizes="100vw"
        style={{ objectFit: 'cover', objectPosition: '50% 45%', zIndex: -2 }}
      />

      <div
        ref={reveal.ref}
        className={`lp-wrap lp-cta lp-reveal-group ${reveal.className}`}
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 0.92fr) minmax(0, 1fr)',
          gap: '64px',
          alignItems: 'start',
          paddingTop: '88px',
          paddingBottom: '88px',
        }}
      >
        {/* lp-on-photo is scoped to the copy column, never the grid: the upload
            panel below is a white card, and its inherited text must stay ink. */}
        <div className="lp-on-photo">
          <span className="lp-eyebrow" style={{ marginBottom: '16px' }}>
            Start here
          </span>

          <h2 style={{ maxWidth: '14ch', marginBottom: '18px' }}>Stop guessing. Start deciding.</h2>

          <p style={{ maxWidth: '44ch', marginBottom: '34px' }}>
            Drop in a sales export and Kern returns a ranked set of actions, each
            one explained in plain English. You will not have to configure
            anything or learn a new tool to read it.
          </p>

          <dl style={{ margin: 0, borderTop: '1px solid rgba(255,255,255,0.24)' }}>
            {SPEC.map(([k, v]) => (
              <div
                key={k}
                style={{
                  display: 'grid',
                  gridTemplateColumns: '104px 1fr',
                  gap: '18px',
                  padding: '12px 0',
                  borderBottom: '1px solid rgba(255,255,255,0.24)',
                }}
              >
                <dt
                  style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: '0.68rem',
                    fontWeight: 600,
                    letterSpacing: '0.11em',
                    textTransform: 'uppercase',
                    color: '#f0c9ae',
                    paddingTop: '3px',
                  }}
                >
                  {k}
                </dt>
                <dd
                  style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: '0.9rem',
                    lineHeight: 1.5,
                    color: 'rgba(255,255,255,0.88)',
                  }}
                >
                  {v}
                </dd>
              </div>
            ))}
          </dl>
        </div>

        <div
          style={{
            backgroundColor: 'var(--lp-paper)',
            border: '1px solid var(--lp-line)',
            borderRadius: '12px',
            padding: '28px 26px',
            boxShadow: '0 30px 70px rgba(12,10,8,0.34)',
          }}
        >
          <UploadZone onSuccess={onUploadSuccess} />

          {/* Left-aligned label on a single rule — not a centred "OR" between
              two matched hairlines. */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '14px', margin: '26px 0 4px' }}>
            <span className="lp-label" style={{ whiteSpace: 'nowrap' }}>
              Or open a sample
            </span>
            <div style={{ flex: 1, height: '1px', backgroundColor: 'var(--lp-line)' }} />
          </div>

          {/* Datasets read as files to open, not as a pair of buttons. */}
          <div>
            {DEMOS.map(d => (
              <button
                key={d.id}
                onClick={() => onDemo(d.id)}
                disabled={!!demoLoading}
                className="lp-lift-row"
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  gap: '14px',
                  width: '100%',
                  padding: '13px 8px',
                  background: 'none',
                  border: 'none',
                  borderBottom: '1px solid var(--lp-line)',
                  borderRadius: '6px',
                  cursor: demoLoading ? 'default' : 'pointer',
                  textAlign: 'left',
                  opacity: demoLoading && demoLoading !== d.id ? 0.4 : 1,
                }}
              >
                <span style={{ minWidth: 0 }}>
                  <span
                    className="lp-data"
                    style={{ display: 'block', fontSize: '0.82rem', color: 'var(--lp-ink)' }}
                  >
                    {demoLoading === d.id ? 'Loading…' : d.file}
                  </span>
                  <span
                    style={{
                      display: 'block',
                      fontFamily: 'var(--font-body)',
                      fontSize: '0.78rem',
                      color: 'var(--lp-ink-2)',
                      marginTop: '3px',
                    }}
                  >
                    {d.meta}
                  </span>
                </span>
                <ArrowRight
                  size={15}
                  strokeWidth={2}
                  style={{ color: 'var(--lp-accent)', flexShrink: 0 }}
                  aria-hidden
                />
              </button>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}
