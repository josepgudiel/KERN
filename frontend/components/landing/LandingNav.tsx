'use client'

import { useEffect, useRef, useState } from 'react'

interface LandingNavProps {
  onDemo: () => void
  demoLoading: boolean
}

/* Anchors only — every one resolves to a section on this page. A nav link to a
   page that does not exist is the fastest way to lose a visitor's trust, which
   is why Pricing left the bar when the pricing section did. */
const LINKS = [
  { href: '#how-it-works', label: 'How it works' },
  { href: '#features', label: 'Features' },
  { href: '#demo', label: 'Live demo' },
]

/* Flat header: the wordmark left, three plain links centre-right, one filled
   action at the end. The wordmark is text, not a mark: at 1.15rem an icon
   beside it adds a second thing to read and nothing to recognise.

   Two states, and the hero is what switches them. For the whole height of the
   photograph the bar is transparent and its contents invert to white, so the
   picture runs to the top edge of the window instead of being capped by a
   paper strip. The paper ground, the hairline and the shadow arrive at the
   moment the photograph clears the bottom of the bar — not on the first pixel
   of scroll, which would drop a white strip across a picture the visitor is
   still looking at. The filled terracotta action is the one element that does
   not change: it clears contrast on both grounds. */
export default function LandingNav({ onDemo, demoLoading }: LandingNavProps) {
  const [scrolled, setScrolled] = useState(false)
  const navRef = useRef<HTMLElement | null>(null)

  useEffect(() => {
    /* The hero owns `#top`. Watching the element rather than a scroll figure
       means the switch stays correct when the hero is re-laid-out — a wrapped
       headline or the demo error banner above it changes the crossover point,
       and a hard-coded offset would go stale. */
    const hero = document.getElementById('top')

    if (!hero || typeof IntersectionObserver === 'undefined') {
      // No hero to track: fall back to "the page has moved at all", so the bar
      // is still legible over whatever is beneath it.
      const onScroll = () => setScrolled(window.scrollY > 8)
      onScroll()
      window.addEventListener('scroll', onScroll, { passive: true })
      return () => window.removeEventListener('scroll', onScroll)
    }

    /* Pulling the observation root down by the bar's own height puts the
       trip-wire along the bar's bottom edge: the hero stops intersecting
       exactly when its last pixel passes under the nav. The callback also runs
       once on observe, so a reload part-way down the page renders the right
       state immediately. */
    const navHeight = navRef.current?.offsetHeight ?? 64

    const io = new IntersectionObserver(
      ([entry]) => setScrolled(!entry.isIntersecting),
      { rootMargin: `-${navHeight}px 0px 0px 0px`, threshold: 0 }
    )
    io.observe(hero)
    return () => io.disconnect()
  }, [])

  return (
    <nav ref={navRef} className={`lp-nav${scrolled ? ' lp-nav--scrolled' : ' lp-nav--over'}`}>
      <div
        className="lp-wrap"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '16px',
          /* Fixed height, not vertical padding — see --lp-nav-h in globals.css:
             the hero offsets itself by exactly this figure. */
          height: 'var(--lp-nav-h)',
        }}
      >
        <a
          href="#top"
          className="lp-navmark"
          style={{ display: 'flex', alignItems: 'center', textDecoration: 'none', minWidth: 0 }}
        >
          <span
            style={{
              fontFamily: 'var(--font-heading)',
              fontSize: '1.15rem',
              fontWeight: 700,
              letterSpacing: '-0.01em',
              color: 'inherit',
            }}
          >
            Kern
          </span>
        </a>

        <div
          className="lp-navlinks"
          style={{ display: 'flex', alignItems: 'center', gap: '30px', marginLeft: '40px' }}
        >
          {LINKS.map(l => (
            <a key={l.href} href={l.href} className="lp-navlink">
              {l.label}
            </a>
          ))}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '18px', marginLeft: 'auto' }}>
          <button type="button" className="lp-navlink lp-hide-sm" onClick={onDemo} disabled={demoLoading}>
            {demoLoading ? 'Loading…' : 'View demo'}
          </button>
          <a href="#start" className="btn-lp" style={{ padding: '9px 18px', fontSize: '0.88rem' }}>
            Upload your export
          </a>
        </div>
      </div>
    </nav>
  )
}
