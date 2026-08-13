'use client'

import type { CSSProperties, ReactNode } from 'react'
import Card from './Card'
import { type Tone, tone } from './tokens'

export interface StatTileProps {
  label: string
  value: string | number
  /** Small qualifier under the value, e.g. "vs prior 30 days". */
  hint?: string
  /** Rich content under the value (a Badge, say). Renders below `hint`. */
  footer?: ReactNode
  /** Colours the value and hint. Omit to keep the value neutral. */
  valueTone?: Tone
  icon?: ReactNode
  className?: string
  style?: CSSProperties
}

/**
 * The numeric tile used across the dashboard.
 *
 * The value is clamped to clamp(1.4rem, 2vw, 1.8rem): large enough to be the
 * focal point, small enough that a six-figure currency string still fits one
 * line in a four-up grid instead of swallowing the row.
 *
 * Label and figure are deliberately set in different voices — the label reads
 * as words in the heading sans, the figure as data in the tabular mono. When
 * both were monospaced caps, every tile looked like the same tile.
 */
export const STAT_VALUE_SIZE = 'clamp(1.4rem, 2vw, 1.8rem)'

export default function StatTile({
  label,
  value,
  hint,
  footer,
  valueTone,
  icon,
  className,
  style,
}: StatTileProps) {
  const valueColor = valueTone ? tone(valueTone).fg : 'var(--t1)'

  return (
    <Card padding="16px 18px" className={className} style={style}>
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '7px',
        marginBottom: '10px',
      }}>
        {icon}
        <span className="ui-label">{label}</span>
      </div>

      <div style={{
        fontFamily: 'var(--font-mono)',
        fontWeight: 500,
        fontVariantNumeric: 'tabular-nums',
        fontSize: STAT_VALUE_SIZE,
        lineHeight: 1.1,
        letterSpacing: '-0.02em',
        color: valueColor,
        overflowWrap: 'anywhere',
      }}>
        {value}
      </div>

      {hint && (
        <div style={{
          marginTop: '7px',
          fontFamily: 'var(--font-body)',
          fontSize: '0.7rem',
          color: valueTone ? tone(valueTone).fg : 'var(--t2)',
          opacity: valueTone ? 0.85 : 1,
          lineHeight: 1.4,
        }}>
          {hint}
        </div>
      )}

      {footer && <div style={{ marginTop: '9px' }}>{footer}</div>}
    </Card>
  )
}
