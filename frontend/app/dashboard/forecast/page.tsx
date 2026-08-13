'use client'

import { useCallback } from 'react'
import { LineChart, Minus, TrendingDown, TrendingUp } from 'lucide-react'
import { useSession } from '@/context/SessionContext'
import { getForecast } from '@/lib/api'
import { usePageData } from '@/lib/hooks'
import type { ForecastResponse } from '@/types'
import ChartCard from '@/components/ChartCard'
import ErrorCard from '@/components/ErrorCard'
import { SkeletonRecommendation } from '@/components/SkeletonCard'
import { CHART_COLORS, tooltipStyle, axisStyle } from '@/lib/chartConfig'
import {
  Badge,
  Card,
  EmptyState,
  PageHeader,
  emptyIconProps,
  type Tone,
} from '@/components/ui'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

const TREND_META: Record<string, { label: string; tone: Tone; Icon: typeof TrendingUp }> = {
  upward:   { label: 'Upward trend',   tone: 'positive', Icon: TrendingUp },
  downward: { label: 'Downward trend', tone: 'negative', Icon: TrendingDown },
  flat:     { label: 'Stable',         tone: 'info',     Icon: Minus },
}

export default function ForecastPage() {
  const { sessionId, uploadMeta } = useSession()
  const currency = uploadMeta?.currency ?? '$'

  const fetchData = useCallback(
    () => {
      if (!sessionId) return Promise.reject(new Error('No session'))
      return getForecast(sessionId)
    },
    [sessionId]
  )

  const { data, loading, error, slow, retry } = usePageData<ForecastResponse>(
    fetchData,
    sessionId ? `kern_cache_forecast_${sessionId}` : undefined,
  )

  function formatDate(d: string) {
    const date = new Date(d)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  const chartData = data?.forecast_points.map((p) => ({
    ...p,
    date: formatDate(p.date),
  }))

  const trend = data ? TREND_META[data.trend] ?? TREND_META.flat : null

  return (
    <div>
      <PageHeader
        title="What to Expect"
        context="Where revenue is heading if the last few weeks carry on as they are."
        actions={trend ? (
          <Badge toneName={trend.tone} icon={<trend.Icon size={13} strokeWidth={2} aria-hidden />}>
            {trend.label}
          </Badge>
        ) : undefined}
      />

      {error && <div style={{ marginBottom: '20px' }}><ErrorCard message={error} onRetry={retry} /></div>}

      {slow && loading && (
        <Card accent="warning" padding="16px 20px" style={{ marginBottom: '20px' }}>
          <p style={{ fontFamily: 'var(--font-body)', color: 'var(--t2)', fontSize: '0.85rem' }}>
            This is running slowly. A refresh usually clears it.
          </p>
        </Card>
      )}

      {data && trend ? (
        <>
          {/* Early estimate banner */}
          {data.data_quality_flag === 'early_estimate' && (
            <Card accent="warning" padding="13px 18px" className="fade-up" style={{ marginBottom: '20px' }}>
              <p style={{ fontFamily: 'var(--font-body)', color: 'var(--t2)', fontSize: '0.82rem', margin: 0 }}>
                Built on a short history, so treat it as a rough shape rather than a number.
              </p>
            </Card>
          )}

          {/* Chart */}
          <div className="fade-up fade-up-delay-1">
            <ChartCard title="Revenue forecast" caption="Expected weekly revenue, with the range it could reasonably fall in">
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="confidenceGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={CHART_COLORS.primary} stopOpacity={0.18} />
                      <stop offset="95%" stopColor={CHART_COLORS.primary} stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} vertical={false} />
                  <XAxis dataKey="date" tick={axisStyle.tick} axisLine={axisStyle.axisLine} tickLine={axisStyle.tickLine} />
                  <YAxis tick={axisStyle.tick} axisLine={axisStyle.axisLine} tickLine={axisStyle.tickLine}
                         tickFormatter={(v: number) => `${currency}${(v/1000).toFixed(1)}k`} />
                  <Tooltip {...tooltipStyle} formatter={(v) => [`${currency}${Number(v).toFixed(2)}`, '']} />
                  {/* Confidence band: the `lower` area is a mask that punches the
                      band back to the card surface, so it has to match --bg-card
                      exactly or the chart grows a visible shelf. CHART_COLORS.surface
                      is the literal mirror of that token — var() does not resolve
                      inside SVG presentation attributes. */}
                  <Area dataKey="upper" stroke="transparent" fill="url(#confidenceGrad)" fillOpacity={1} />
                  <Area dataKey="lower" stroke="transparent" fill={CHART_COLORS.surface} fillOpacity={1} />
                  {/* Main predicted line on top */}
                  <Area dataKey="predicted" stroke={CHART_COLORS.primary} strokeWidth={2.5}
                        fill="transparent" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          {/* Growth actions */}
          {data.growth_actions.length > 0 && (
            <div style={{ marginTop: '28px' }}>
              <h3 style={{ marginBottom: '14px' }}>Growth actions</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
                {data.growth_actions.map((action, i) => (
                  <Card
                    key={i}
                    interactive
                    padding="16px 20px"
                    className={`fade-up fade-up-delay-${Math.min(i + 1, 4)}`}
                  >
                    <p style={{ fontFamily: 'var(--font-body)', color: 'var(--t1)', fontSize: '0.88rem', lineHeight: 1.65 }}>
                      {action}
                    </p>
                  </Card>
                ))}
              </div>
            </div>
          )}
        </>
      ) : loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
          <SkeletonRecommendation />
          <SkeletonRecommendation />
        </div>
      ) : !error ? (
        <EmptyState
          icon={<LineChart {...emptyIconProps} aria-hidden />}
          title="Need more data"
          description="A forecast needs at least 28 days of sales behind it. Upload a longer export and this page fills in."
        />
      ) : null}
    </div>
  )
}
