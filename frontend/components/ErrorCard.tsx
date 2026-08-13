'use client'

import { ArrowRight } from 'lucide-react'
import { Card } from '@/components/ui'

export default function ErrorCard({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <Card accent="negative" padding="20px 22px">
      <h3 style={{ color: 'var(--red)', marginBottom: '8px' }}>
        Something went wrong
      </h3>
      <p style={{
        fontFamily: 'var(--font-body)',
        fontSize: '0.85rem',
        color: 'var(--t2)',
        marginBottom: onRetry ? '14px' : '0',
        lineHeight: 1.65,
      }}>
        {message}
      </p>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            fontFamily: 'var(--font-heading)',
            fontSize: '0.84rem',
            fontWeight: 600,
            letterSpacing: '-0.005em',
            color: 'var(--accent)',
            background: 'none',
            border: 'none',
            borderBottom: '1px solid var(--border2)',
            padding: '2px 0',
            cursor: 'pointer',
            transition: 'color 0.15s ease, border-color 0.15s ease',
          }}
          onMouseEnter={(e) => { e.currentTarget.style.borderBottomColor = 'var(--accent)' }}
          onMouseLeave={(e) => { e.currentTarget.style.borderBottomColor = 'var(--border2)' }}
        >
          Try again
          <ArrowRight size={13} strokeWidth={2} aria-hidden />
        </button>
      )}
    </Card>
  )
}
