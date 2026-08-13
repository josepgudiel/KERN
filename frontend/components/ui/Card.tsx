'use client'

import type { CSSProperties, ReactNode } from 'react'
import { type Tone, tone } from './tokens'

export interface CardProps {
  children: ReactNode
  /**
   * Marks the card as a semantic *state* panel — a warning, a failure, a
   * measured rise or fall. It tints the fill and the hairline, and it is only
   * for cards whose meaning is the state itself. It is not an emphasis device:
   * a card does not get coloured to look important.
   */
  accent?: Exclude<Tone, 'info' | 'neutral'>
  /** `elevated` sits on --bg-mid, for panels nested inside a card. */
  variant?: 'surface' | 'elevated'
  /** Lifts on hover. Use for cards that are clickable or scannable lists. */
  interactive?: boolean
  padding?: string
  className?: string
  style?: CSSProperties
}

/**
 * The single card container for the app.
 *
 * A flat fill, a hairline all the way round, and one step of shadow. The
 * coloured strip that used to run down the left edge is gone: it decorated
 * cards that had nothing to signal, and a stack of tiles each wearing a
 * different bar down its side is the house style of every generated dashboard
 * template. Separation now comes from the border, the shadow and the spacing
 * between cards, which is what the landing page does too.
 */
export default function Card({
  children,
  accent,
  variant = 'surface',
  interactive = false,
  padding = '20px 22px',
  className = '',
  style,
}: CardProps) {
  const state = accent ? tone(accent) : null
  const restingBg = variant === 'elevated' ? 'var(--bg-mid)' : 'var(--bg-card)'

  return (
    <div
      className={className}
      style={{
        backgroundColor: state ? state.dim : restingBg,
        border: `1px solid ${state ? state.edge : 'var(--border)'}`,
        borderRadius: 'var(--radius-card)',
        boxShadow: 'var(--shadow-xs)',
        padding,
        /* Hover moves the shadow and the hairline, never the card's position:
           most of these tiles arrive under a `fade-up` animation, and an
           animation's transform outranks an inline one, so a translate here
           would simply never fire. */
        transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
        ...style,
      }}
      onMouseEnter={interactive ? (e) => {
        e.currentTarget.style.borderColor = state ? state.edge : 'var(--border2)'
        e.currentTarget.style.boxShadow = 'var(--shadow-md)'
      } : undefined}
      onMouseLeave={interactive ? (e) => {
        e.currentTarget.style.borderColor = state ? state.edge : 'var(--border)'
        e.currentTarget.style.boxShadow = 'var(--shadow-xs)'
      } : undefined}
    >
      {children}
    </div>
  )
}
