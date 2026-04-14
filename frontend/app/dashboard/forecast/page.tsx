'use client'

import { useCallback } from 'react'
import { useSession } from '@/context/SessionContext'
import { getForecast } from '@/lib/api'
import { usePageData } from '@/lib/hooks'
import type { ForecastResponse } from '@/types'
import ChartCard from '@/components/ChartCard'
import ErrorCard from '@/components/ErrorCard'
import { SkeletonRecommendation } from '@/components/SkeletonCard'
import { CHART_COLORS, tooltipStyle, axisStyle } from '@/lib/chartConfig'
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'

const trendConfig: Record<string, { label: string; color: string }> = {
  upward:   { label: 'Upward Trend',   color: '#16a34a' },
  downward: { label: 'Downward Trend', color: '#dc2626' },
  flat:     { label: 'Stable',         color: '#1e3a5f' },
}

const trendArrow: Record<string, string> = { upward: '\u2197', downward: '\u2198', flat: '\u2192' }

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

  const { data, loading, error, slow, retry } = usePageData<ForecastResponse>(fetchData, sessionId ? `kern_cache_forecast_${sessionId}` : undefined)

  function formatDate(d: string) {
    const date = new Date(d)
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
  }

  const chartData = data?.forecast_points.map((p) => ({
    ...p,
    date: formatDate(p.date),
  }))

  const trend = data ? trendConfig[data.trend] ?? trendConfig.flat : null

  return (
    <div>
      {/* Page header */}
      <div style={{ marginBottom: 'clamp(28px, 5vw, 48px)' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          marginBottom: '12px',
        }}>
          <div style={{ width: '28px', height: '1px', backgroundColor: 'var(--accent)' }} />
          <span className="label-caps" style={{ color: 'var(--accent)' }}>
            Outlook
          </span>
        </div>
        <h1 style={{ color: 'var(--navy)', marginBottom: '14px' }}>
          What to Expect
        </h1>
        <p style={{
          fontFamily: 'Raleway',
          fontSize: '0.92rem',
          color: 'var(--text-muted)',
          maxWidth: '500px',
          lineHeight: 1.75,
        }}>
          Where your revenue is heading based on your recent trend.
        </p>
        <div className="divider" style={{ marginTop: '24px' }} />
      </div>

      {error && <div style={{ marginBottom: '24px' }}><ErrorCard message={error} onRetry={retry} /></div>}

      {slow && loading && (
        <div style={{
          backgroundColor: 'var(--surface)',
          border: '1px solid var(--border)',
          borderLeft: '4px solid #d97706',
          borderRadius: '20px',
          padding: '18px 22px',
          marginBottom: '24px',
          boxShadow: 'var(--shadow-xs)',
        }}>
          <p style={{ fontFamily: 'Raleway', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            This is taking longer than usual. The server may be starting up &mdash; try refreshing in a moment.
          </p>
        </div>
      )}

      {data && trend ? (
        <>
          {/* Trend pill */}
          <div className="fade-up" style={{ marginBottom: '32px' }}>
            <span style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              fontFamily: 'Raleway',
              fontWeight: 800,
              textTransform: 'uppercase',
              fontSize: '0.68rem',
              letterSpacing: '0.14em',
              padding: '8px 20px',
              borderRadius: '999px',
              color: '#ffffff',
              backgroundColor: trend.color,
            }}>
              {trendArrow[data.trend]} {trend.label}
            </span>
          </div>

          {/* Early estimate banner */}
          {data.data_quality_flag === 'early_estimate' && (
            <div className="fade-up" style={{
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border)',
              borderLeft: '3px solid #d97706',
              borderRadius: '20px',
              padding: '14px 20px',
              marginBottom: '24px',
            }}>
              <p style={{ fontFamily: 'Raleway', color: 'var(--text-secondary)', fontSize: '0.82rem', margin: 0 }}>
                Based on limited history — accuracy improves with more data.
              </p>
            </div>
          )}

          {/* Chart */}
          <div className="fade-up fade-up-delay-1">
            <ChartCard title="Revenue Forecast" caption="Predicted weekly revenue with estimated range">
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="confidenceGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2563eb" stopOpacity={0.15} />
                      <stop offset="95%" stopColor="#2563eb" stopOpacity={0.02} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={CHART_COLORS.grid} vertical={false} />
                  <XAxis dataKey="date" tick={axisStyle.tick} axisLine={axisStyle.axisLine} tickLine={axisStyle.tickLine} />
                  <YAxis tick={axisStyle.tick} axisLine={axisStyle.axisLine} tickLine={axisStyle.tickLine}
                         tickFormatter={(v: number) => `${currency}${(v/1000).toFixed(1)}k`} />
                  <Tooltip {...tooltipStyle} formatter={(v) => [`${currency}${Number(v).toFixed(2)}`, '']} />
                  {/* Confidence band: area between upper and lower */}
                  <Area dataKey="upper" stroke="transparent" fill="url(#confidenceGrad)" fillOpacity={1} />
                  <Area dataKey="lower" stroke="transparent" fill="white" fillOpacity={1} />
                  {/* Main predicted line on top */}
                  <Area dataKey="predicted" stroke={CHART_COLORS.primary} strokeWidth={2.5}
                        fill="transparent" dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>

          {/* Growth actions */}
          {data.growth_actions.length > 0 && (
            <div style={{ marginTop: '32px' }}>
              <h3 style={{ color: 'var(--accent)', marginBottom: '18px' }}>Growth Actions</h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                {data.growth_actions.map((action, i) => (
                  <div
                    key={i}
                    className={`fade-up fade-up-delay-${Math.min(i + 1, 4)}`}
                    style={{
                      backgroundColor: 'var(--surface)',
                      border: '1px solid var(--border)',
                      borderLeft: '4px solid var(--accent)',
                      borderRadius: '20px',
                      padding: '18px 22px',
                      boxShadow: 'var(--shadow-sm)',
                      transition: 'box-shadow 0.25s ease, transform 0.25s ease',
                    }}
                    onMouseEnter={(e) => {
                      e.currentTarget.style.boxShadow = 'var(--shadow-md)'
                      e.currentTarget.style.transform = 'translateY(-2px)'
                    }}
                    onMouseLeave={(e) => {
                      e.currentTarget.style.boxShadow = 'var(--shadow-sm)'
                      e.currentTarget.style.transform = 'translateY(0)'
                    }}
                  >
                    <p style={{ fontFamily: 'Raleway', color: 'var(--text-primary)', fontSize: '0.88rem', lineHeight: 1.65 }}>{action}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </>
      ) : loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <SkeletonRecommendation />
          <SkeletonRecommendation />
        </div>
      ) : !error ? (
        <div style={{
          backgroundColor: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: '20px',
          padding: '48px 28px',
          textAlign: 'center',
          boxShadow: 'var(--shadow-sm)',
        }}>
          <div style={{ fontSize: '2rem', marginBottom: '12px' }}>📈</div>
          <div className="label-caps" style={{ color: 'var(--accent)', marginBottom: '10px' }}>Need more data</div>
          <p style={{
            fontFamily: 'Raleway',
            color: 'var(--text-muted)',
            fontSize: '0.85rem',
            maxWidth: '380px',
            margin: '0 auto',
            lineHeight: 1.65,
          }}>
            We need at least 28 days of sales history to build a forecast. Upload a file with more history to unlock this.
          </p>
        </div>
      ) : null}
    </div>
  )
}
