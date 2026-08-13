'use client'

import type { ReactNode } from 'react'

export interface PageHeaderProps {
  title: string
  /** One line of context, rendered inline beside the title on desktop. */
  context?: string
  /** Optional right-aligned controls (buttons, badges). */
  actions?: ReactNode
}

/**
 * Two elements, by design: the title and one line of context.
 *
 * The previous per-page header stacked five (rule + eyebrow + h1 + paragraph +
 * divider) and cost roughly 120px of vertical space above the fold on every
 * page. Section identity now comes from the sidebar's active state, which is
 * already on screen.
 */
export default function PageHeader({ title, context, actions }: PageHeaderProps) {
  return (
    <header style={{
      display: 'flex',
      alignItems: 'baseline',
      justifyContent: 'space-between',
      flexWrap: 'wrap',
      gap: '10px 20px',
      marginBottom: '24px',
    }}>
      <div style={{
        display: 'flex',
        alignItems: 'baseline',
        flexWrap: 'wrap',
        gap: '6px 14px',
        minWidth: 0,
      }}>
        <h1 style={{ margin: 0 }}>{title}</h1>
        {context && (
          <p style={{
            fontFamily: 'var(--font-body)',
            fontSize: '0.85rem',
            color: 'var(--t2)',
            lineHeight: 1.5,
            margin: 0,
            maxWidth: '58ch',
          }}>
            {context}
          </p>
        )}
      </div>
      {actions && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
          {actions}
        </div>
      )}
    </header>
  )
}
