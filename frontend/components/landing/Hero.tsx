'use client'

import Image from 'next/image'
import { ArrowRight } from 'lucide-react'
import ActionCardPreview from './ActionCardPreview'

interface HeroProps {
  onDemo: () => void
  demoLoading: boolean
}

/* Full-bleed photograph, scrimmed hard on the left so the copy column keeps
   full contrast while the picture stays a picture on the right. The product
   card floats over the photograph as a live element — it is the real Pricing
   Check card with a working disclosure, not a screenshot and not a terminal
   pastiche. The scrim is a two-axis gradient rather than a flat wash: a flat
   overlay at the opacity this copy needs would kill the photograph entirely. */
export default function Hero({ onDemo, demoLoading }: HeroProps) {
  return (
    <section id="top" className="lp-hero-full">
      <Image
        src="/photos/register.jpg"
        alt="A shop worker at a point-of-sale terminal, handing a card reader across the counter to a customer"
        fill
        priority
        sizes="100vw"
        className="lp-hero-img"
        style={{ objectFit: 'cover', zIndex: -2 }}
      />

      <div
        className="lp-wrap lp-hero"
        style={{
          display: 'grid',
          gridTemplateColumns: 'minmax(0, 1.05fr) minmax(0, 0.95fr)',
          gap: '64px',
          alignItems: 'center',
          paddingTop: '96px',
          paddingBottom: '96px',
        }}
      >
        <div className="lp-on-photo fade-up">
          <span className="lp-eyebrow" style={{ marginBottom: '20px' }}>
            Sales intelligence for independent operators
          </span>

          <h1 style={{ margin: '0 0 22px', maxWidth: '17ch' }}>
            Your sales data already knows what to do next.
          </h1>

          <p style={{ maxWidth: '46ch', marginBottom: '34px', fontSize: '1.06rem', lineHeight: 1.65 }}>
            Whatever you sell, Kern reads the export your register already
            produces and hands back ranked decisions: which price to test, which
            product is slipping, what to expect next month. Every one says in
            plain English why it is there.
          </p>

          <div
            className="lp-hero-actions"
            style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}
          >
            <button type="button" onClick={onDemo} disabled={demoLoading} className="btn-lp">
              {demoLoading ? 'Loading demo…' : 'Run the demo dataset'}
              {!demoLoading && <ArrowRight size={15} strokeWidth={2.25} aria-hidden />}
            </button>
            <a href="#start" className="btn-lp-outline">
              Upload your own export
            </a>
          </div>

          <p
            style={{
              marginTop: '20px',
              fontFamily: 'var(--font-body)',
              fontSize: '0.86rem',
              color: 'rgba(255,255,255,0.72)',
            }}
          >
            CSV or XLSX · no account, no card, no setup
          </p>
        </div>

        <div className="fade-up-delay-2 lp-hero-card">
          <ActionCardPreview variant="hero" />
        </div>
      </div>
    </section>
  )
}
