'use client'

import { useState, type CSSProperties } from 'react'
import { ArrowRight, ChevronDown, ChevronUp } from 'lucide-react'
import { Badge } from '@/components/ui'
import { PRICING_TOP } from './demoOutput'

interface ActionCardPreviewProps {
  /** `hero` floats over photography and stays closed; `full` opens its
   *  supporting detail inline and is the page's worked example. */
  variant?: 'hero' | 'full'
}

/* The Pricing Check card, rendered with the same parts the dashboard uses —
   view label, action chip, the decision as a heading, the plain-English
   reasoning, and the figures behind it under a disclosure. Figures come from
   demoOutput.ts, which is the engine's own output on the bundled coffee-shop
   export.

   The card leads with a price move rather than a dollar total on purpose: on
   this dataset the engine cannot fit an elasticity, so it declines to project
   a figure. Showing that refusal is more persuasive than inventing the number
   it withheld. */
export default function ActionCardPreview({ variant = 'hero' }: ActionCardPreviewProps) {
  const [open, setOpen] = useState(variant === 'full')
  const hero = variant === 'hero'
  /* `p` carries the card's own heading styles from the h3 below; the landing
     page styles h3 by tag, so the two are set explicitly here. */
  const Title = hero ? 'p' : 'h3'

  return (
    <figure style={{ margin: 0 }}>
      <div
        className="lp-lift"
        /* Resting and hover depth are handed to .lp-lift as properties rather
           than set as an inline box-shadow — inline would win against the
           :hover rule and the card would lift with a flat shadow. Over the
           photograph both rungs are far heavier: a card floating on a picture
           needs the separation that the same card on paper does not. */
        style={{
          backgroundColor: 'var(--lp-paper)',
          border: '1px solid var(--lp-line)',
          borderTop: '3px solid var(--lp-accent)',
          borderRadius: '10px',
          padding: hero ? '20px 22px' : '24px 26px',
          '--lift-rest': hero ? '0 32px 70px rgba(10,8,6,0.44)' : 'var(--shadow-md)',
          '--lift-hover': hero ? '0 40px 88px rgba(10,8,6,0.5)' : 'var(--shadow-lg)',
        } as CSSProperties}
      >
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
            marginBottom: '14px',
          }}
        >
          <span className="lp-label">{PRICING_TOP.view} · Rank 01</span>
          <Badge toneName="info" shape="tag">
            {PRICING_TOP.action}
          </Badge>
        </div>

        {/* The decision. The price move is the number that carries the card.

            Heading level is conditional on placement, not on appearance. In the
            worked example the card is the section's content and its title is a
            real h3 under that section's h2. Floating over the hero there is no
            h2 above it, so emitting a heading there would put an h3 directly
            under the page h1 and leave a hole in the document outline for the
            sake of one styled line. */}
        <Title
          style={{
            margin: '0 0 10px',
            fontFamily: 'var(--font-heading)',
            fontSize: hero ? '1.16rem' : '1.3rem',
            fontWeight: 600,
            letterSpacing: '-0.008em',
            lineHeight: 1.3,
            color: 'var(--lp-ink)',
          }}
        >
          {PRICING_TOP.product}
        </Title>

        <div
          style={{
            display: 'flex',
            alignItems: 'baseline',
            gap: '11px',
            flexWrap: 'wrap',
            paddingBottom: '15px',
            marginBottom: '14px',
            borderBottom: '1px solid var(--lp-line)',
          }}
        >
          <span className="lp-num" style={{ fontSize: '1.25rem', color: 'var(--lp-ink-2)' }}>
            {PRICING_TOP.current}
          </span>
          <ArrowRight size={15} strokeWidth={2.25} style={{ color: 'var(--lp-ink-3)' }} aria-hidden />
          <span
            className="lp-num"
            style={{ fontSize: hero ? '1.6rem' : '1.85rem', color: 'var(--green)' }}
          >
            {PRICING_TOP.suggested}
          </span>
          <span style={{ fontFamily: 'var(--font-body)', fontSize: '0.82rem', color: 'var(--lp-ink-2)' }}>
            {PRICING_TOP.deltaPct} · {PRICING_TOP.units} sold
          </span>
        </div>

        <p style={{ fontSize: '0.88rem', lineHeight: 1.6, marginBottom: '16px' }}>
          {PRICING_TOP.summary}
        </p>

        {/* The reasoning above is the answer; this is what it rests on. In the
            hero it stays a disclosure so the card reads as a live control; in
            the worked example it opens on load. */}
        <button
          type="button"
          onClick={() => setOpen(v => !v)}
          aria-expanded={open}
          aria-controls="pricing-detail"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '5px',
            padding: 0,
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            fontFamily: 'var(--font-heading)',
            fontSize: '0.82rem',
            fontWeight: 600,
            color: 'var(--lp-accent)',
          }}
        >
          {open ? (
            <ChevronUp size={14} strokeWidth={2.25} aria-hidden />
          ) : (
            <ChevronDown size={14} strokeWidth={2.25} aria-hidden />
          )}
          Why this
        </button>

        <div
          id="pricing-detail"
          style={{ maxHeight: open ? '400px' : '0', overflow: 'hidden', transition: 'max-height 0.32s ease' }}
        >
          <div
            style={{
              marginTop: '13px',
              padding: '15px 16px',
              backgroundColor: 'var(--lp-shell)',
              border: '1px solid var(--lp-line)',
              borderRadius: '8px',
            }}
          >
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px' }}>
              {PRICING_TOP.basis.map(p => (
                <div key={p.label}>
                  <div className="lp-label" style={{ fontSize: '0.62rem', marginBottom: '5px' }}>
                    {p.label}
                  </div>
                  <div className="lp-data" style={{ fontSize: '0.85rem', color: 'var(--lp-ink)' }}>
                    {p.value}
                  </div>
                </div>
              ))}
            </div>

            {/* The engine's own hedge, quoted rather than smoothed over. */}
            <p
              style={{
                margin: '15px 0 0',
                paddingTop: '13px',
                borderTop: '1px solid var(--lp-line)',
                fontSize: '0.82rem',
                lineHeight: 1.6,
              }}
            >
              {PRICING_TOP.caveat}
            </p>
          </div>
        </div>
      </div>

      <figcaption
        style={{
          marginTop: '11px',
          fontFamily: 'var(--font-heading)',
          fontSize: '0.72rem',
          letterSpacing: '0.02em',
          color: hero ? 'rgba(255,255,255,0.72)' : 'var(--lp-ink-3)',
        }}
      >
        Live output · bundled coffee-shop demo export
      </figcaption>
    </figure>
  )
}
