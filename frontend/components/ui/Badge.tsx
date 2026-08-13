'use client'

import type { CSSProperties, ReactNode } from 'react'
import { type Tone, tone } from './tokens'

export interface BadgeProps {
  children: ReactNode
  toneName?: Tone
  /** Leading status dot in the badge's own colour. */
  dot?: boolean
  /** Leading icon (a lucide element). Inherits the badge colour. */
  icon?: ReactNode
  /** `pill` for status chips, `tag` for the squared metadata chips. */
  shape?: 'pill' | 'tag'
  title?: string
  style?: CSSProperties
}

/**
 * Status chip. Always tinted-background + coloured-text, never a saturated
 * fill with white text, which is where the old trend pills failed contrast
 * against --green / --amber.
 *
 * Set in the heading sans at reading case: a badge says something like
 * "Upward trend" or "vs prior week", and those are words. Figures inside one
 * still line up, via tabular numerals.
 */
export default function Badge({
  children,
  toneName = 'neutral',
  dot = false,
  icon,
  shape = 'pill',
  title,
  style,
}: BadgeProps) {
  const t = tone(toneName)

  return (
    <span
      title={title}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        padding: shape === 'pill' ? '4px 11px' : '3px 8px',
        borderRadius: shape === 'pill' ? '999px' : '4px',
        backgroundColor: t.dim,
        border: `1px solid ${t.edge}`,
        color: t.fg,
        fontFamily: 'var(--font-heading)',
        fontSize: '0.72rem',
        fontWeight: 600,
        fontVariantNumeric: 'tabular-nums',
        letterSpacing: '-0.002em',
        lineHeight: 1.4,
        whiteSpace: 'nowrap',
        ...style,
      }}
    >
      {dot && (
        <span style={{
          width: '6px',
          height: '6px',
          borderRadius: '50%',
          backgroundColor: t.fg,
          flexShrink: 0,
        }} />
      )}
      {icon}
      {children}
    </span>
  )
}
