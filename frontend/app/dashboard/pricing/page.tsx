'use client'

import { useCallback } from 'react'
import { ArrowDown, ArrowRight, ArrowUp, Check, Coins } from 'lucide-react'
import { useSession } from '@/context/SessionContext'
import { getPricing } from '@/lib/api'
import { usePageData } from '@/lib/hooks'
import type { PricingResponse } from '@/types'
import ErrorCard from '@/components/ErrorCard'
import { SkeletonRecommendation } from '@/components/SkeletonCard'
import {
  Badge,
  Card,
  EmptyState,
  PageHeader,
  emptyIconProps,
  tone,
  type Tone,
} from '@/components/ui'

/* Keys are the literal `action` strings emitted by backend/engine/pricing.py —
   they carry a glyph prefix. We match on them but never render them raw: the
   badge shows a clean label plus a lucide icon. */
const ACTION_META: Record<string, { label: string; tone: Tone; Icon: typeof ArrowUp }> = {
  '↑ Raise Price':       { label: 'Raise price',       tone: 'positive', Icon: ArrowUp },
  '↓ Consider Lowering': { label: 'Consider lowering', tone: 'negative', Icon: ArrowDown },
  '✓ Maintain':          { label: 'Maintain',          tone: 'info',     Icon: Check },
}

const ACTION_FALLBACK = { label: 'Review', tone: 'info' as Tone, Icon: Check }

const CONFIDENCE_BADGE: Record<string, { label: string; tone: Tone }> = {
  high:         { label: 'Strong signal',       tone: 'positive' },
  directional:  { label: 'Worth testing',       tone: 'warning' },
  insufficient: { label: 'Not enough data yet', tone: 'neutral' },
}

export default function PricingPage() {
  const { sessionId, uploadMeta } = useSession()
  const currency = uploadMeta?.currency ?? '$'

  const fetchData = useCallback(() => {
    if (!sessionId) return Promise.reject(new Error('No session'))
    return getPricing(sessionId)
  }, [sessionId])
  const { data, loading, error, slow, retry } = usePageData<PricingResponse>(fetchData)

  return (
    <div>
      <PageHeader
        title="Pricing Check"
        context="Where your prices look out of step with how much each product actually shifts."
      />

      {error && <div style={{ marginBottom: '20px' }}><ErrorCard message={error} onRetry={retry} /></div>}

      {slow && loading && (
        <Card accent="warning" padding="16px 20px" style={{ marginBottom: '20px' }}>
          <p style={{ fontFamily: 'var(--font-body)', color: 'var(--t2)', fontSize: '0.85rem' }}>
            Comparing prices against sales volume. This takes a moment.
          </p>
        </Card>
      )}

      {data && !data.has_data && (
        <EmptyState
          icon={<Coins {...emptyIconProps} aria-hidden />}
          title="Not enough data"
          description={data.warning ?? 'A price check needs at least 15 sales per product before it means anything.'}
        />
      )}

      {data?.recommendations && data.recommendations.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          {data.recommendations.map((rec, i) => {
            const action = ACTION_META[rec.action] ?? ACTION_FALLBACK
            const actionTone = action.tone
            const actionColor = tone(actionTone).fg
            const badge = rec.elasticity_confidence ? CONFIDENCE_BADGE[rec.elasticity_confidence] : null
            const priceChanged = rec.suggested_price !== rec.current_price

            return (
              <Card
                key={i}
                interactive
                padding="18px 22px"
                className="fade-up"
                style={{ animationDelay: `${i * 60}ms`, opacity: 0 }}
              >
                {/* Header row */}
                <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '16px', marginBottom: '12px', flexWrap: 'wrap' }}>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontFamily: 'var(--font-body)', fontWeight: 600, fontSize: '0.95rem', color: 'var(--t1)', marginBottom: '7px' }}>
                      {rec.product}
                    </div>
                    <Badge
                      toneName={actionTone}
                      icon={<action.Icon size={13} strokeWidth={2} aria-hidden />}
                    >
                      {action.label}
                    </Badge>
                  </div>

                  {/* Price */}
                  <div style={{ textAlign: 'right', flexShrink: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '9px' }}>
                      <span style={{
                        fontFamily: 'var(--font-mono)',
                        fontVariantNumeric: 'tabular-nums',
                        fontSize: '1.25rem',
                        fontWeight: 500,
                        color: priceChanged ? 'var(--t2)' : 'var(--t1)',
                        textDecoration: priceChanged ? 'line-through' : 'none',
                      }}>
                        {currency}{rec.current_price.toFixed(2)}
                      </span>
                      {priceChanged && (
                        <>
                          <ArrowRight size={14} strokeWidth={2} style={{ color: 'var(--t2)' }} aria-hidden />
                          <span style={{ fontFamily: 'var(--font-mono)', fontVariantNumeric: 'tabular-nums', fontSize: '1.25rem', fontWeight: 500, color: actionColor }}>
                            {currency}{rec.suggested_price.toFixed(2)}
                          </span>
                        </>
                      )}
                    </div>
                    <div style={{ fontFamily: 'var(--font-body)', fontSize: '0.68rem', color: 'var(--t2)', marginTop: '3px' }}>
                      {rec.n_transactions.toLocaleString()} transactions
                    </div>
                  </div>
                </div>

                {/* Reason */}
                <p style={{ fontFamily: 'var(--font-body)', fontSize: '0.85rem', color: 'var(--t2)', lineHeight: 1.7, marginBottom: 0 }}>
                  {rec.reason}
                </p>

                {/* Signal strength */}
                {(badge || rec.reliability) && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap', marginTop: '12px' }}>
                    {badge && <Badge toneName={badge.tone} shape="tag" dot>{badge.label}</Badge>}
                    {rec.reliability && (
                      <span style={{ fontFamily: 'var(--font-body)', fontSize: '0.68rem', color: 'var(--t2)' }}>
                        {rec.reliability === 'high' ? 'Strong signal' : 'Early signal, worth watching'}
                        {', '}from {rec.n_transactions.toLocaleString()} transactions
                      </span>
                    )}
                  </div>
                )}

                {/* Sensitivity label */}
                {rec.sensitivity_label && (
                  <p style={{ fontFamily: 'var(--font-body)', fontSize: '0.75rem', color: 'var(--t2)', marginTop: '8px', marginBottom: 0, lineHeight: 1.6 }}>
                    {rec.sensitivity_label}
                  </p>
                )}
              </Card>
            )
          })}
        </div>
      )}

      {loading && !data && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <SkeletonRecommendation />
          <SkeletonRecommendation />
          <SkeletonRecommendation />
        </div>
      )}
    </div>
  )
}
