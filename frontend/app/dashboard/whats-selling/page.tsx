'use client'

import { useCallback } from 'react'
import { Package, TrendingDown, TrendingUp } from 'lucide-react'
import { useSession } from '@/context/SessionContext'
import { getWhatsSelling } from '@/lib/api'
import { usePageData } from '@/lib/hooks'
import type { WhatsSelling } from '@/types'
import ClusterCard from '@/components/ClusterCard'
import ErrorCard from '@/components/ErrorCard'
import { SkeletonRecommendation } from '@/components/SkeletonCard'
import {
  Card,
  EmptyState,
  PageHeader,
  emptyIconProps,
  tone,
  type Tone,
} from '@/components/ui'

/** Basket-rule lift → how strongly the pairing beats chance. */
function signalFor(lift: number): { label: string; tone: Tone } {
  if (lift >= 2)   return { label: 'Strong',   tone: 'positive' }
  if (lift >= 1.5) return { label: 'Moderate', tone: 'warning' }
  return { label: 'Weak', tone: 'neutral' }
}

/** Horizontal scroller card for the rising / declining rails. */
function TrendRailCard({
  product,
  pct,
  revenue,
  currency,
  direction,
  delayIndex,
}: {
  product: string
  pct: number
  revenue: number
  currency: string
  direction: 'up' | 'down'
  delayIndex: number
}) {
  const t: Tone = direction === 'up' ? 'positive' : 'negative'
  const Icon = direction === 'up' ? TrendingUp : TrendingDown

  return (
    <Card
      interactive
      padding="14px 16px"
      className={`fade-up fade-up-delay-${Math.min(delayIndex + 1, 4)}`}
      style={{ minWidth: 'min(210px, 70vw)', flexShrink: 0 }}
    >
      <p style={{
        fontFamily: 'var(--font-body)', fontWeight: 600, fontSize: '0.85rem', color: 'var(--t1)',
        marginBottom: '8px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
      }}>
        {product}
      </p>
      <div style={{
        display: 'flex', alignItems: 'center', gap: '5px', marginBottom: '8px',
        color: tone(t).fg, fontFamily: 'var(--font-mono)', fontVariantNumeric: 'tabular-nums', fontSize: '0.78rem',
      }}>
        <Icon size={14} strokeWidth={2} aria-hidden />
        {direction === 'up' ? '+' : ''}{pct.toFixed(1)}%
      </div>
      <p className="number-display" style={{ fontSize: '1.15rem' }}>
        {currency}{revenue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
      </p>
    </Card>
  )
}

export default function WhatsSellingPage() {
  const { sessionId, uploadMeta } = useSession()
  const currency = uploadMeta?.currency ?? '$'

  const fetchData = useCallback(
    () => {
      if (!sessionId) return Promise.reject(new Error('No session'))
      return getWhatsSelling(sessionId)
    },
    [sessionId]
  )

  const { data, loading, error, slow, retry } = usePageData<WhatsSelling>(
    fetchData,
    sessionId ? `kern_cache_selling_${sessionId}` : undefined,
  )

  return (
    <div>
      <PageHeader
        title="What's Selling"
        context="How each product is performing, grouped by behaviour and ranked by trend."
      />

      {error && <div style={{ marginBottom: '20px' }}><ErrorCard message={error} onRetry={retry} /></div>}

      {slow && loading && (
        <Card accent="warning" padding="16px 20px" style={{ marginBottom: '20px' }}>
          <p style={{ fontFamily: 'var(--font-body)', color: 'var(--t2)', fontSize: '0.85rem' }}>
            Taking longer than expected. A refresh usually sorts it out.
          </p>
        </Card>
      )}

      {data ? (
        <>
          <h3 style={{ marginBottom: '14px' }}>Your product groups</h3>
          {data.clusters.length === 0 ? (
            <div style={{ marginBottom: '20px' }}>
              <EmptyState
                icon={<Package {...emptyIconProps} aria-hidden />}
                title="Need more products"
                description="Grouping needs at least four different products. This file has fewer than that."
              />
            </div>
          ) : (
            <div
              className="grid-keep-2 lg:!grid-cols-4"
              style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '14px', marginBottom: '32px' }}
            >
              {data.clusters.map((c, i) => (
                <div key={c.label} className={`fade-up fade-up-delay-${Math.min(i + 1, 4)}`}>
                  <ClusterCard cluster={c} currency={currency} />
                </div>
              ))}
            </div>
          )}

          {/* Rising Stars */}
          {data.rising_stars.length > 0 && (
            <>
              <h3 style={{ marginBottom: '14px' }}>Rising stars</h3>
              <div style={{ display: 'flex', gap: '14px', overflowX: 'auto', paddingBottom: '12px', marginBottom: '32px' }}>
                {data.rising_stars.map((p, i) => (
                  <TrendRailCard
                    key={p.product}
                    product={p.product}
                    pct={p.growth_pct}
                    revenue={p.recent_revenue}
                    currency={currency}
                    direction="up"
                    delayIndex={i}
                  />
                ))}
              </div>
            </>
          )}

          {/* Declining */}
          {data.declining_products.length > 0 && (
            <>
              <h3 style={{ marginBottom: '14px' }}>Declining products</h3>
              <div style={{ display: 'flex', gap: '14px', overflowX: 'auto', paddingBottom: '12px', marginBottom: '32px' }}>
                {data.declining_products.map((p, i) => (
                  <TrendRailCard
                    key={p.product}
                    product={p.product}
                    pct={p.decline_pct}
                    revenue={p.recent_revenue}
                    currency={currency}
                    direction="down"
                    delayIndex={i}
                  />
                ))}
              </div>
            </>
          )}

          {/* Basket info — shown when single-item transactions dominate */}
          {data.basket_info && data.basket_rules.length === 0 && (
            <Card style={{ marginBottom: '32px' }}>
              <h3 style={{ marginBottom: '8px' }}>Bundle suggestions</h3>
              <p style={{ fontFamily: 'var(--font-body)', color: 'var(--t2)', fontSize: '0.85rem', lineHeight: 1.65, margin: 0 }}>
                {data.basket_info}
              </p>
            </Card>
          )}

          {/* Basket Rules */}
          {data.basket_rules.length > 0 && (
            <>
              <h3 style={{ marginBottom: '14px' }}>Frequently bought together</h3>
              <Card padding="0" className="overflow-x-mobile" style={{ overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '500px' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border)' }}>
                      <th className="ui-label" style={{ textAlign: 'left', padding: '13px 18px' }}>Item A</th>
                      <th className="ui-label" style={{ textAlign: 'left', padding: '13px 18px' }}>Item B</th>
                      <th className="ui-label" style={{ textAlign: 'right', padding: '13px 18px' }} title="When Item A is sold, how often Item B is also sold">How often together</th>
                      <th className="ui-label" style={{ textAlign: 'right', padding: '13px 18px' }} title="How strong the pairing is. Strong means the two sell together far more often than chance would explain.">Signal</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.basket_rules.slice(0, 10).map((r, i) => {
                      const signal = signalFor(r.lift)
                      return (
                        <tr
                          key={i}
                          style={{
                            borderBottom: i < Math.min(data.basket_rules.length, 10) - 1 ? '1px solid var(--border)' : 'none',
                            transition: 'background-color 0.15s ease',
                          }}
                          onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--bg-alt)' }}
                          onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent' }}
                        >
                          <td style={{ fontFamily: 'var(--font-body)', color: 'var(--t1)', fontSize: '0.82rem', padding: '12px 18px' }}>{r.antecedent}</td>
                          <td style={{ fontFamily: 'var(--font-body)', color: 'var(--t1)', fontSize: '0.82rem', padding: '12px 18px' }}>{r.consequent}</td>
                          <td style={{ fontFamily: 'var(--font-mono)', fontVariantNumeric: 'tabular-nums', color: 'var(--t2)', fontSize: '0.78rem', padding: '12px 18px', textAlign: 'right' }}>{r.confidence_pct.toFixed(0)}% of the time</td>
                          <td style={{ fontFamily: 'var(--font-body)', fontSize: '0.82rem', padding: '12px 18px', textAlign: 'right', fontWeight: 600, color: tone(signal.tone).fg }}>
                            {signal.label}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </Card>
            </>
          )}
        </>
      ) : (
        loading && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <SkeletonRecommendation />
            <SkeletonRecommendation />
          </div>
        )
      )}
    </div>
  )
}
