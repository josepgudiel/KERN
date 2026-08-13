'use client'

import { useEffect, useRef, useState } from 'react'

interface RevealOptions {
  /** Fraction of the element that must be on screen before it reveals. */
  threshold?: number
  /** Shrinks the viewport from the bottom so a section commits a little after
   *  its first pixel appears, rather than the instant it clips the edge. */
  rootMargin?: string
}

/* Scroll reveal, one shot.
 *
 * Returns a ref to attach to the element and the class string that carries the
 * transition. The element is hidden in the server-rendered HTML and revealed
 * once it enters the viewport, so a visitor scrolling down meets each section
 * as it arrives instead of finding the whole page already settled.
 *
 * Three deliberate properties:
 * — it fires once and disconnects. Sections that re-animate every time they
 *   pass the fold call attention to the animation rather than the content.
 * — anything already on screen at mount reveals on the first callback, which
 *   IntersectionObserver delivers immediately. A reload part-way down the page
 *   therefore does not leave the section under the cursor blank.
 * — with no IntersectionObserver it shows everything at once, and `<noscript>`
 *   in app/page.tsx neutralises the hidden state entirely. Motion is the
 *   enhancement; the content never depends on it.
 */
export function useReveal<T extends HTMLElement = HTMLDivElement>(options: RevealOptions = {}) {
  const { threshold = 0.06, rootMargin = '0px 0px -8% 0px' } = options
  const ref = useRef<T | null>(null)
  const [inView, setInView] = useState(false)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    if (typeof IntersectionObserver === 'undefined') {
      setInView(true)
      return
    }

    const io = new IntersectionObserver(
      entries => {
        if (entries.some(e => e.isIntersecting)) {
          setInView(true)
          io.disconnect()
        }
      },
      { threshold, rootMargin }
    )

    io.observe(el)
    return () => io.disconnect()
  }, [threshold, rootMargin])

  return {
    ref,
    inView,
    /** Spread-friendly: `<div {...reveal.props} />` for the common case. */
    className: `lp-reveal${inView ? ' lp-reveal--in' : ''}`,
  }
}
