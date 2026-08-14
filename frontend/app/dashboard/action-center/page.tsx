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
import { Card, EmptyState, PageHeader, emptyIconProps } from '@/components/ui'
import { CheckCircle2, ListChecks } from 'lucide-react'

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

  async function handleDismiss(recId: string, status: 'done' | 'not_relevant', reason?: string) {
    if (!sessionId) return
    // Both statuses hide the card identically — only the recorded meaning differs.
    setDismissed(prev => { const next = new Set(Array.from(prev)); next.add(recId); return next })
    const recType = data?.recommendations?.find(r => r.id === recId)?.rec_type
    try {
      await dismissRecommendation(sessionId, recId, status, reason, recType)
    } catch {/* optimistic update already applied */}
  }

  const visibleRecs = data?.recommendations?.filter((r: { id: string }) => !dismissed.has(r.id)) ?? []
  const actionCount = visibleRecs.length

  /* The API wraps this line in markdown emphasis, but nothing in the dashboard
     renders markdown — it was printing the asterisks. Strip the wrapper and let
     CSS carry the emphasis; the sentence itself is untouched. */
  const confidenceNote = data?.data_confidence_badge?.replace(/^\*+|\*+$/g, '').trim()

  return (
    <div>
      <PageHeader
        title="Action Center"
        context={data
          ? `${actionCount} action${actionCount !== 1 ? 's' : ''} need${actionCount === 1 ? 's' : ''} attention today, ranked by revenue impact.`
          : 'What to deal with today, in order of what it is worth.'}
      />

      {error && <div style={{ marginBottom: '20px' }}><ErrorCard message={error} onRetry={retry} /></div>}

      {slow && loading && (
        <Card accent="warning" padding="16px 20px" style={{ marginBottom: '20px' }}>
          <p style={{ fontFamily: 'var(--font-body)', color: 'var(--t2)', fontSize: '0.82rem' }}>
            Still working. The server may be waking up, so give it a few seconds.
          </p>
        </Card>
      )}

      {/* Health Brief */}
      {data?.health_brief && (
        <Card className="fade-up" padding="22px 24px" style={{ marginBottom: '20px' }}>
          <h3 style={{ marginBottom: '10px' }}>Business summary</h3>
          <p style={{ fontSize: '0.85rem', marginBottom: '8px' }}>
            {data.health_brief.paragraph_1}
          </p>
          <p style={{ fontSize: '0.85rem' }}>
            {data.health_brief.paragraph_2}
          </p>
        </Card>
      )}

      {/* Metrics */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: '12px',
        marginBottom: '20px',
      }}
        className="grid-keep-2 lg:!grid-cols-4"
      >
        {data ? (
          <>
            <MetricCard label="Total revenue" value={fmt(data.metrics.total_revenue)} delay={0} />
            <MetricCard label="Total orders" value={data.metrics.total_orders.toLocaleString()} delay={50} />
            <MetricCard label="Average order value" value={fmt(data.metrics.avg_order_value)} delay={100} />
            {data.metrics.wow_pct != null ? (
              <MetricCard
                label="Week over week"
                value={`${data.metrics.wow_pct > 0 ? '+' : ''}${data.metrics.wow_pct.toFixed(1)}%`}
                delta="vs prior week"
                deltaPositive={data.metrics.wow_pct >= 0}
                delay={150}
              />
            ) : data.metrics.wow_stale_note ? (
              <MetricCard
                label="Week over week"
                value="n/a"
                delta={data.metrics.wow_stale_note}
                delay={150}
              />
            ) : (
              <MetricCard
                label="Unique products"
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
            <EmptyState
              icon={dismissed.size > 0
                ? <CheckCircle2 {...emptyIconProps} aria-hidden />
                : <ListChecks {...emptyIconProps} aria-hidden />}
              title={dismissed.size > 0 ? 'All caught up' : 'Not enough data yet'}
              /* Cards leave this list for two different reasons now, so the copy
                 can't claim they were all acted on. */
              description={dismissed.size > 0
                ? 'Nothing left to review — upload a fresher export when you have one.'
                : 'This page needs at least 14 transactions before it can rank anything. Try a file covering a longer period.'}
            />
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
      {confidenceNote && (
        <p style={{
          fontFamily: 'var(--font-body)',
          fontStyle: 'italic',
          color: 'var(--t2)',
          fontSize: '0.76rem',
          textAlign: 'center',
          margin: 0,
        }}>
          {confidenceNote}
        </p>
      )}
    </div>
  )
}
