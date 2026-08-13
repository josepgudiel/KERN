'use client'

import { useCallback } from 'react'
import { BarChart3, Minus, TrendingDown, TrendingUp } from 'lucide-react'
import { useSession } from '@/context/SessionContext'
import { getOverview } from '@/lib/api'
import { usePageData } from '@/lib/hooks'
import type { OverviewResponse } from '@/types'
import ErrorCard from '@/components/ErrorCard'
import { SkeletonMetric, SkeletonRecommendation } from '@/components/SkeletonCard'
import {
  Badge,
  Card,
  EmptyState,
  PageHeader,
  StatTile,
  deltaTone,
  emptyIconProps,
  iconProps,
  tone,
  type Tone,
} from '@/components/ui'

const TREND_META: Record<string, { label: string; tone: Tone; Icon: typeof TrendingUp }> = {
  upward:   { label: 'Upward trend',   tone: 'positive', Icon: TrendingUp },
  downward: { label: 'Downward trend', tone: 'negative', Icon: TrendingDown },
  flat:     { label: 'Stable',         tone: 'info',     Icon: Minus },
}

function DeltaTile({ value, label }: { value: number; label: string }) {
  const t = deltaTone(value)
  return (
    <StatTile
      label={label}
      value={`${value > 0 ? '+' : ''}${value.toFixed(1)}%`}
      valueTone={t}
      hint="vs prior 30 days"
    />
  )
}

export default function OverviewPage() {
  const { sessionId, uploadMeta } = useSession()
  const currency = uploadMeta?.currency ?? '$'

  const fetchData = useCallback(() => {
    if (!sessionId) return Promise.reject(new Error('No session'))
    return getOverview(sessionId)
  }, [sessionId])
  const { data, loading, error, slow, retry } = usePageData<OverviewResponse>(fetchData)

  function fmtRev(n: number) {
    if (n >= 1_000_000) return `${currency}${(n / 1_000_000).toFixed(1)}M`
    if (n >= 1_000) return `${currency}${(n / 1_000).toFixed(1)}K`
    return `${currency}${n.toFixed(2)}`
  }

  const trend = data ? TREND_META[data.trend] ?? TREND_META.flat : null
  const comparison = data?.period_comparison

  return (
    <div>
      <PageHeader
        title="Summary"
        context="The last 30 days measured against the 30 before them, plus any day that stood out."
        actions={data && trend ? (
          <>
            <Badge toneName={trend.tone} icon={<trend.Icon size={13} strokeWidth={2} aria-hidden />}>
              {trend.label}
            </Badge>
            {data.wow_pct != null && (
              <Badge toneName={deltaTone(data.wow_pct)} shape="tag">
                {data.wow_pct > 0 ? '+' : ''}{data.wow_pct.toFixed(1)}% WoW
              </Badge>
            )}
          </>
        ) : undefined}
      />

      {error && <div style={{ marginBottom: '20px' }}><ErrorCard message={error} onRetry={retry} /></div>}

      {slow && loading && (
        <Card accent="warning" padding="16px 20px" style={{ marginBottom: '20px' }}>
          <p style={{ fontFamily: 'var(--font-body)', color: 'var(--t2)', fontSize: '0.85rem' }}>
            Still loading. Refresh in a moment if nothing appears.
          </p>
        </Card>
      )}

      {/* Period comparison */}
      {comparison ? (
        <section style={{ marginBottom: '36px' }}>
          <h3 style={{ marginBottom: '4px' }}>Period comparison</h3>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: '0.78rem', color: 'var(--t2)', marginBottom: '16px' }}>
            {comparison.label_b} ({fmtRev(comparison.rev_b)}) vs {comparison.label_a} ({fmtRev(comparison.rev_a)})
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px', marginBottom: '20px' }}>
            <DeltaTile value={comparison.revenue_delta_pct} label="Revenue" />
            <DeltaTile value={comparison.orders_delta_pct} label="Orders" />
            <DeltaTile value={comparison.aov_delta_pct} label="Average order value" />
          </div>

          {/* Risers / Fallers */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            {comparison.top_risers.length > 0 && (
              <Card accent="positive">
                <h3 style={{ color: 'var(--green)', marginBottom: '10px' }}>Rising</h3>
                {comparison.top_risers.map((r, i) => (
                  <div key={i} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px',
                    padding: '6px 0',
                    borderBottom: i < comparison.top_risers.length - 1 ? '1px solid var(--border)' : 'none',
                  }}>
                    <span style={{ fontFamily: 'var(--font-body)', fontSize: '0.85rem', color: 'var(--t1)', minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.product}</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--green)', flexShrink: 0 }}>+{r.delta_pct.toFixed(1)}%</span>
                  </div>
                ))}
              </Card>
            )}
            {comparison.top_fallers.length > 0 && (
              <Card accent="negative">
                <h3 style={{ color: 'var(--red)', marginBottom: '10px' }}>Falling</h3>
                {comparison.top_fallers.map((r, i) => (
                  <div key={i} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '12px',
                    padding: '6px 0',
                    borderBottom: i < comparison.top_fallers.length - 1 ? '1px solid var(--border)' : 'none',
                  }}>
                    <span style={{ fontFamily: 'var(--font-body)', fontSize: '0.85rem', color: 'var(--t1)', minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.product}</span>
                    <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', color: 'var(--red)', flexShrink: 0 }}>{r.delta_pct.toFixed(1)}%</span>
                  </div>
                ))}
              </Card>
            )}
          </div>

          {/* New / Dropped products */}
          {(comparison.new_products.length > 0 || comparison.dropped_products.length > 0) && (
            <div style={{ display: 'flex', gap: '12px', marginTop: '14px', flexWrap: 'wrap' }}>
              {comparison.new_products.length > 0 && (
                <div style={{
                  backgroundColor: tone('positive').dim,
                  border: `1px solid ${tone('positive').edge}`,
                  borderRadius: '10px',
                  padding: '9px 13px',
                }}>
                  <span className="ui-label" style={{ color: 'var(--green)' }}>New this period · </span>
                  <span style={{ fontFamily: 'var(--font-body)', fontSize: '0.80rem', color: 'var(--t2)' }}>{comparison.new_products.join(', ')}</span>
                </div>
              )}
              {comparison.dropped_products.length > 0 && (
                <div style={{
                  backgroundColor: tone('negative').dim,
                  border: `1px solid ${tone('negative').edge}`,
                  borderRadius: '10px',
                  padding: '9px 13px',
                }}>
                  <span className="ui-label" style={{ color: 'var(--red)' }}>Not sold this period · </span>
                  <span style={{ fontFamily: 'var(--font-body)', fontSize: '0.80rem', color: 'var(--t2)' }}>{comparison.dropped_products.join(', ')}</span>
                </div>
              )}
            </div>
          )}
        </section>
      ) : data && data.has_dates && (
        <Card style={{ marginBottom: '36px' }}>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: '0.85rem', color: 'var(--t2)' }}>
            {data.warning ?? 'A period comparison needs at least 60 days of history.'}
          </p>
        </Card>
      )}

      {/* Anomalies */}
      {data && (
        <section>
          <h3 style={{ marginBottom: '4px' }}>Unusual days</h3>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: '0.78rem', color: 'var(--t2)', marginBottom: '16px' }}>
            Dates that came in well above or below your normal takings.
          </p>

          {data.anomalies.length === 0 ? (
            <Card padding="28px" style={{ textAlign: 'center' }}>
              <p style={{ fontFamily: 'var(--font-body)', color: 'var(--t2)', fontSize: '0.85rem' }}>
                Nothing stood out. Takings have been steady.
              </p>
            </Card>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {data.anomalies.map((a, i) => {
                const isSpike = a.direction === 'spike'
                const t: Tone = isSpike ? 'positive' : 'negative'
                const Icon = isSpike ? TrendingUp : TrendingDown
                return (
                  <Card
                    key={i}
                    accent={t}
                    padding="13px 18px"
                    className={'fade-up anomaly-row'}
                    style={{
                      animationDelay: `${i * 40}ms`,
                      opacity: 0,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '14px',
                    }}
                  >
                    <Icon {...iconProps} aria-hidden />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontFamily: 'var(--font-body)', fontWeight: 600, fontSize: '0.85rem', color: 'var(--t1)', marginBottom: '2px' }}>
                        {a.date_label || a.date}
                        {a.auto_label && <span style={{ fontWeight: 400, color: 'var(--t2)', marginLeft: '8px', fontSize: '0.78rem' }}>· {a.auto_label}</span>}
                      </div>
                      {a.top_product && (
                        <div style={{ fontFamily: 'var(--font-body)', fontSize: '0.75rem', color: 'var(--t2)' }}>
                          Top: {a.top_product}
                        </div>
                      )}
                    </div>
                    <div style={{ textAlign: 'right', flexShrink: 0 }}>
                      <div style={{ fontFamily: 'var(--font-mono)', fontVariantNumeric: 'tabular-nums', fontSize: '1.15rem', fontWeight: 500, color: tone(t).fg }}>
                        {currency}{a.revenue.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                      </div>
                      <div style={{ fontFamily: 'var(--font-body)', fontSize: '0.68rem', color: 'var(--t2)', marginTop: '1px' }}>
                        {a.pct_above > 0 ? '+' : ''}{Math.abs(a.pct_above).toFixed(0)}% vs typical
                      </div>
                    </div>
                  </Card>
                )
              })}
            </div>
          )}
        </section>
      )}

      {loading && !data && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px' }}>
            <SkeletonMetric /><SkeletonMetric /><SkeletonMetric />
          </div>
          <SkeletonRecommendation />
          <SkeletonRecommendation />
        </div>
      )}

      {!data && !loading && !error && (
        <EmptyState
          icon={<BarChart3 {...emptyIconProps} aria-hidden />}
          title="No data available"
          description="This view needs at least 30 days of sales history. Upload a longer export to see it."
        />
      )}
    </div>
  )
}
