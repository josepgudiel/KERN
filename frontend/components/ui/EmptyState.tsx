'use client'

import type { ReactNode } from 'react'
import Card from './Card'

export interface EmptyStateProps {
  /** A lucide icon element — spread `emptyIconProps` onto it. */
  icon?: ReactNode
  title: string
  description: string
  action?: ReactNode
}

/**
 * The "nothing to show yet" panel. One shape for every page so a missing-data
 * state never looks like a broken one.
 */
export default function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <Card padding="40px 28px" style={{ textAlign: 'center' }}>
      {icon && (
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '14px' }}>
          {icon}
        </div>
      )}
      <h3 style={{ marginBottom: '8px' }}>{title}</h3>
      <p style={{
        fontFamily: 'var(--font-body)',
        color: 'var(--t2)',
        fontSize: '0.85rem',
        maxWidth: '42ch',
        margin: '0 auto',
        lineHeight: 1.65,
      }}>
        {description}
      </p>
      {action && <div style={{ marginTop: '18px' }}>{action}</div>}
    </Card>
  )
}
