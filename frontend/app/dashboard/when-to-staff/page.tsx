'use client'

import { useCallback } from 'react'
import { Clock } from 'lucide-react'
import { useSession } from '@/context/SessionContext'
import { getWhenToStaff } from '@/lib/api'
import { usePageData } from '@/lib/hooks'
import type { StaffingResponse } from '@/types'
import ChartCard from '@/components/ChartCard'
import ErrorCard from '@/components/ErrorCard'
import { SkeletonRecommendation } from '@/components/SkeletonCard'
import { CHART_COLORS, tooltipStyle, axisStyle } from '@/lib/chartConfig'
import { Card, EmptyState, PageHeader, StatTile, emptyIconProps } from '@/components/ui'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

export default function WhenToStaffPage() {
  const { sessionId } = useSession()

  const fetchData = useCallback(
    () => {
      if (!sessionId) return Promise.reject(new Error('No session'))
      return getWhenToStaff(sessionId)
    },
    [sessionId]
  )

  const { data, loading, error, slow, retry } = usePageData<StaffingResponse>(fetchData)

  return (
    <div>
      <PageHeader
        title="When to Staff"
        context="Which days of the week earn most, so you can put people where the trade is."
      />

      {error && <div style={{ marginBottom: '20px' }}><ErrorCard message={error} onRetry={retry} /></div>}

      {slow && loading && (
        <Card accent="warning" padding="16px 20px" style={{ marginBottom: '20px' }}>
          <p style={{ fontFamily: 'var(--font-body)', color: 'var(--t2)', fontSize: '0.85rem' }}>
            The server is slow to answer right now. Refresh if this does not clear.
          </p>
        </Card>
      )}

      {data ? (
        <>
          {/* Peak / Slowest */}
          <div className="grid-keep-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', marginBottom: '20px' }}>
            <StatTile
              className="fade-up"
              label="Peak day"
              value={data.peak_day ?? 'No data'}
              valueTone={data.peak_day ? 'positive' : undefined}
            />
            <StatTile
              className="fade-up fade-up-delay-1"
              label="Slowest day"
              value={data.slowest_day ?? 'No data'}
              valueTone={data.slowest_day ? 'negative' : undefined}
            />
          </div>

          {/* Staffing recommendation */}
          {data.has_dates ? (
            data.staffing_recommendation ? (
              <Card className="fade-up fade-up-delay-2" padding="20px 22px" style={{ marginBottom: '20px' }}>
                <h3 style={{ marginBottom: '10px' }}>Staffing recommendation</h3>
                <p style={{ fontFamily: 'var(--font-body)', color: 'var(--t2)', fontSize: '0.88rem', lineHeight: 1.75, margin: 0 }}>
                  {data.staffing_recommendation}
                </p>
              </Card>
            ) : (
              <Card className="fade-up fade-up-delay-2" padding="20px 22px" style={{ marginBottom: '20px' }}>
                <p style={{ fontFamily: 'var(--font-body)', color: 'var(--t2)', fontSize: '0.85rem', margin: 0 }}>
                  The days look too alike so far to suggest anything useful.
                </p>
              </Card>
            )
          ) : (
            <div className="fade-up fade-up-delay-2" style={{ marginBottom: '20px' }}>
              <EmptyState
                icon={<Clock {...emptyIconProps} aria-hidden />}
                title="Date column required"
                description="Add a date column to your export and this page will show how the week breaks down."
              />
            </div>
          )}

          {/* Chart */}
          {data.has_dates && data.day_of_week.length > 0 && (
            <div className="fade-up fade-up-delay-3">
              <ChartCard title="Revenue by day of week" caption="Average takings for each day, across the whole file">
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={data.day_of_week}>
                    <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} vertical={false} />
                    <XAxis dataKey="day" tick={axisStyle.tick} axisLine={axisStyle.axisLine} tickLine={axisStyle.tickLine} />
                    <YAxis tick={axisStyle.tick} axisLine={axisStyle.axisLine} tickLine={axisStyle.tickLine}
                           tickFormatter={(v: number) => v >= 1000 ? `$${(v/1000).toFixed(1)}K` : `$${v.toFixed(0)}`} />
                    <Tooltip {...tooltipStyle} />
                    <Bar dataKey="avg_revenue" fill={CHART_COLORS.primary} radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>
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
          icon={<Clock {...emptyIconProps} aria-hidden />}
          title="No staffing data yet"
          description="Once your export includes dates, you will see which days carry the week."
        />
      ) : null}
    </div>
  )
}
