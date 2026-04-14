'use client'

import { useCallback, useState, useEffect } from 'react'
import { useSession } from '@/context/SessionContext'
import { getActionCenter, dismissRecommendation, getDismissed } from '@/lib/api'
import { usePageData } from '@/lib/hooks'
import type { ActionCenterResponse } from '@/types'
import MetricCard from '@/components/MetricCard'
import RecommendationCard from '@/components/RecommendationCard'
import ErrorCard from '@/components/ErrorCard'
import { SkeletonMetric, SkeletonRecommendation } from '@/components/SkeletonCard'

export default function ActionCenterPage() {
  const { sessionId, uploadMeta } = useSession()
  const currency = uploadMeta?.currency ?? '$'
  const [dismissed, setDismissed] = useState<Set<string>>(new Set())

  const fetchData = useCallback(
    () => {
      if (!sessionId) return Promise.reject(new Error('No session'))
      return getActionCenter(sessionId)
    },
    [sessionId]
  )

  const { data, loading, error, slow, retry } = usePageData<ActionCenterResponse>(fetchData, sessionId ? `kern_cache_action_${sessionId}` : undefined)

  // Fetch dismissed IDs from backend on mount
  useEffect(() => {
    if (!sessionId) return
    getDismissed(sessionId)
      .then(res => setDismissed(new Set(res.dismissed)))
      .catch(() => {/* ignore */})
  }, [sessionId])

  function fmt(n: number) {
    if (n >= 1_000_000) return `${currency}${(n / 1_000_000).toFixed(1)}M`
    if (n >= 1_000) return `${currency}${(n / 1_000).toFixed(1)}K`
    return `${currency}${n.toFixed(2)}`
  }

  async function handleDismiss(recId: string) {
    if (!sessionId) return
    setDismissed(prev => { const next = new Set(Array.from(prev)); next.add(recId); return next })
    try {
      await dismissRecommendation(sessionId, recId)
    } catch {/* optimistic update already applied */}
  }

  const visibleRecs = data?.recommendations?.filter((r: { id: string }) => !dismissed.has(r.id)) ?? []
  const actionCount = visibleRecs.length

  return (
    <div>
      {/* Page header */}
      <div style={{ marginBottom: 'clamp(24px, 5vw, 44px)' }}>
        <div style={{
          fontFamily: 'var(--font-mono)',
          fontSize: '0.60rem',
          fontWeight: 700,
          letterSpacing: '0.14em',
          textTransform: 'uppercase',
          color: 'var(--accent)',
          marginBottom: '12px',
        }}>
          Action Center
        </div>
        <h1 className="accent-underline" style={{ marginBottom: '20px' }}>
          Action Center
        </h1>
        <p style={{
          fontFamily: 'var(--font-body)',
          fontSize: '0.88rem',
          color: 'var(--text-secondary)',
          maxWidth: '480px',
          lineHeight: 1.7,
          marginTop: '14px',
        }}>
          {data
            ? `${actionCount} action${actionCount !== 1 ? 's' : ''} require${actionCount === 1 ? 's' : ''} attention today, ranked by revenue impact.`
            : 'The most important things to act on today, ranked by estimated revenue impact.'}
        </p>
        <div className="divider" style={{ marginTop: '24px' }} />
      </div>

      {error && <div style={{ marginBottom: '24px' }}><ErrorCard message={error} onRetry={retry} /></div>}

      {slow && loading && (
        <div style={{
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border)',
          borderLeft: '3px solid var(--warning)',
          borderRadius: 'var(--radius-card)',
          padding: '16px 20px',
          marginBottom: '24px',
        }}>
          <p style={{ fontFamily: 'var(--font-body)', color: 'var(--text-secondary)', fontSize: '0.82rem' }}>
            This is taking longer than usual. The server may be starting up — try refreshing in a moment.
          </p>
        </div>
      )}

      {/* Health Brief */}
      {data?.health_brief && (
        <div className="fade-up" style={{
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border)',
          borderLeft: '3px solid var(--accent)',
          borderRadius: 'var(--radius-card)',
          padding: '20px 22px',
          marginBottom: '28px',
        }}>
          <h3 style={{ marginBottom: '10px' }}>Business Summary</h3>
          <p style={{ fontSize: '0.85rem', marginBottom: '8px' }}>
            {data.health_brief.paragraph_1}
          </p>
          <p style={{ fontSize: '0.85rem' }}>
            {data.health_brief.paragraph_2}
          </p>
        </div>
      )}

      {/* Metrics */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: '12px',
        marginBottom: '28px',
      }}
        className="grid-keep-2 lg:!grid-cols-4"
      >
        {data ? (
          <>
            <MetricCard label="Total Revenue" value={fmt(data.metrics.total_revenue)} delay={0} accent />
            <MetricCard label="Total Orders" value={data.metrics.total_orders.toLocaleString()} delay={50} />
            <MetricCard label="Avg Order Value" value={fmt(data.metrics.avg_order_value)} delay={100} />
            {data.metrics.wow_pct != null ? (
              <MetricCard
                label="Week-over-Week"
                value={`${data.metrics.wow_pct > 0 ? '+' : ''}${data.metrics.wow_pct.toFixed(1)}%`}
                delta="vs prior week"
                deltaPositive={data.metrics.wow_pct >= 0}
                delay={150}
              />
            ) : data.metrics.wow_stale_note ? (
              <MetricCard
                label="Week-over-Week"
                value="—"
                delta={data.metrics.wow_stale_note}
                delay={150}
              />
            ) : (
              <MetricCard
                label="Unique Products"
                value={data.metrics.unique_products.toString()}
                delay={150}
              />
            )}
          </>
        ) : (
          loading && <>
            <SkeletonMetric />
            <SkeletonMetric />
            <SkeletonMetric />
            <SkeletonMetric />
          </>
        )}
      </div>

      {/* Recommendations */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '28px' }}>
        {data ? (
          visibleRecs.length > 0 ? (
            visibleRecs
              .sort((a, b) => b.urgency_score - a.urgency_score)
              .map((rec, i) => (
                <RecommendationCard
                  key={rec.id}
                  rec={rec}
                  delay={i * 40}
                  onDismiss={handleDismiss}
                />
              ))
          ) : (
            <div style={{
              backgroundColor: 'var(--bg-surface)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-card)',
              padding: '48px 28px',
              textAlign: 'center',
            }}>
              <div style={{
                fontFamily: 'var(--font-mono)',
                fontSize: '0.60rem',
                letterSpacing: '0.12em',
                textTransform: 'uppercase',
                color: 'var(--accent)',
                marginBottom: '10px',
              }}>
                {dismissed.size > 0 ? 'All caught up' : 'Not enough data yet'}
              </div>
              <p style={{
                fontFamily: 'var(--font-body)',
                color: 'var(--text-muted)',
                fontSize: '0.82rem',
                maxWidth: '380px',
                margin: '0 auto',
                lineHeight: 1.65,
              }}>
                {dismissed.size > 0
                  ? "You've marked all recommendations as done. Upload fresh data to get new insights."
                  : 'We need at least 14 transactions to generate reliable recommendations. Upload a larger dataset to unlock the Action Center.'}
              </p>
            </div>
          )
        ) : (
          loading && <>
            <SkeletonRecommendation />
            <SkeletonRecommendation />
            <SkeletonRecommendation />
          </>
        )}
      </div>

      {/* Data confidence note */}
      {data && (
        <p style={{
          fontFamily: 'var(--font-mono)',
          color: 'var(--text-muted)',
          fontSize: '0.62rem',
          textAlign: 'center',
          letterSpacing: '0.04em',
        }}>
          {data.data_confidence_badge}
        </p>
      )}
    </div>
  )
}
