'use client'

import { useCallback } from 'react'
import { useSession } from '@/context/SessionContext'
import { getOverview } from '@/lib/api'
import { usePageData } from '@/lib/hooks'
import type { OverviewResponse } from '@/types'
import ErrorCard from '@/components/ErrorCard'
import { SkeletonMetric, SkeletonRecommendation } from '@/components/SkeletonCard'

function DeltaPill({ value, label }: { value: number; label: string }) {
  const pos = value >= 0
  return (
    <div style={{
      backgroundColor: 'var(--surface)', border: '1px solid var(--border)',
      borderRadius: '20px', padding: '20px 24px', boxShadow: 'var(--shadow-sm)',
    }}>
      <div className="label-caps" style={{ color: 'var(--accent)', marginBottom: '10px' }}>{label}</div>
      <div className="number-display" style={{
        fontSize: 'clamp(1.6rem, 3vw, 2.2rem)',
        color: pos ? '#16a34a' : '#dc2626',
      }}>
        {value > 0 ? '+' : ''}{value.toFixed(1)}%
      </div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '4px', marginTop: '6px', fontFamily: 'Raleway', fontSize: '0.68rem', fontWeight: 700, color: pos ? '#16a34a' : '#dc2626' }}>
        <span style={{ fontSize: '0.55rem' }}>{pos ? '▲' : '▼'}</span>
        vs prior 30 days
      </div>
    </div>
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

  const trendColor = data?.trend === 'upward' ? '#16a34a' : data?.trend === 'downward' ? '#dc2626' : '#1e3a5f'
  const trendLabel = data?.trend === 'upward' ? '↗ Upward trend' : data?.trend === 'downward' ? '↘ Downward trend' : '→ Stable'

  return (
    <div>
      {/* Page header */}
      <div style={{ marginBottom: 'clamp(28px, 5vw, 48px)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
          <div style={{ width: '28px', height: '1px', backgroundColor: 'var(--accent)' }} />
          <span className="label-caps" style={{ color: 'var(--t3)' }}>Performance</span>
        </div>
        <h1 style={{ color: 'var(--navy)', marginBottom: '14px' }}>Summary</h1>
        <p style={{ fontFamily: 'Raleway', fontSize: '0.92rem', color: 'var(--t2)', maxWidth: '500px', lineHeight: 1.75 }}>
          Last 30 days vs prior 30 days, plus unusual sales days.
        </p>
        <div className="divider" style={{ marginTop: '24px' }} />
      </div>

      {error && <div style={{ marginBottom: '24px' }}><ErrorCard message={error} onRetry={retry} /></div>}

      {slow && loading && (
        <div style={{
          backgroundColor: 'var(--surface)', border: '1px solid var(--border)',
          borderLeft: '4px solid #d97706', borderRadius: '20px',
          padding: '18px 22px', marginBottom: '24px', boxShadow: 'var(--shadow-xs)',
        }}>
          <p style={{ fontFamily: 'Raleway', color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
            This is taking longer than usual — try refreshing in a moment.
          </p>
        </div>
      )}

      {/* Trend pill + WoW */}
      {data && (
        <div className="fade-up" style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '32px', flexWrap: 'wrap' }}>
          <span style={{
            display: 'inline-flex', alignItems: 'center', gap: '6px',
            fontFamily: 'Raleway', fontWeight: 800, textTransform: 'uppercase',
            fontSize: '0.68rem', letterSpacing: '0.14em',
            padding: '8px 20px', borderRadius: '999px',
            color: '#ffffff', backgroundColor: trendColor,
          }}>
            {trendLabel}
          </span>
          {data.wow_pct != null && (
            <span style={{
              fontFamily: 'Raleway', fontWeight: 700, fontSize: '0.80rem',
              color: data.wow_pct >= 0 ? '#16a34a' : '#dc2626',
            }}>
              {data.wow_pct > 0 ? '+' : ''}{data.wow_pct.toFixed(1)}% week-over-week
            </span>
          )}
        </div>
      )}

      {/* Period comparison metrics */}
      {data?.period_comparison ? (
        <section style={{ marginBottom: '40px' }}>
          <h3 style={{ color: 'var(--t3)', marginBottom: '6px' }}>Period Comparison</h3>
          <p style={{ fontFamily: 'Raleway', fontSize: '0.78rem', color: 'var(--t2)', marginBottom: '20px' }}>
            {data.period_comparison!.label_b} ({fmtRev(data.period_comparison!.rev_b)}) vs {data.period_comparison!.label_a} ({fmtRev(data.period_comparison!.rev_a)})
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '24px' }}>
            <DeltaPill value={data.period_comparison!.revenue_delta_pct} label="Revenue" />
            <DeltaPill value={data.period_comparison!.orders_delta_pct} label="Orders" />
            <DeltaPill value={data.period_comparison!.aov_delta_pct} label="Avg Order Value" />
          </div>

          {/* Risers / Fallers */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            {data.period_comparison!.top_risers.length > 0 && (
              <div style={{
                backgroundColor: 'var(--surface)', border: '1px solid var(--border)',
                borderLeft: '4px solid #16a34a', borderRadius: '20px',
                padding: '20px 22px', boxShadow: 'var(--shadow-sm)',
              }}>
                <div className="label-caps" style={{ color: '#16a34a', marginBottom: '12px' }}>Rising</div>
                {data.period_comparison!.top_risers.map((r, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: i < (data.period_comparison?.top_risers?.length ?? 0) - 1 ? '1px solid var(--border)' : 'none' }}>
                    <span style={{ fontFamily: 'Raleway', fontSize: '0.85rem', color: 'var(--text-primary)' }}>{r.product}</span>
                    <span style={{ fontFamily: 'Raleway', fontWeight: 700, fontSize: '0.80rem', color: '#16a34a' }}>+{r.delta_pct.toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            )}
            {data.period_comparison!.top_fallers.length > 0 && (
              <div style={{
                backgroundColor: 'var(--surface)', border: '1px solid var(--border)',
                borderLeft: '4px solid #dc2626', borderRadius: '20px',
                padding: '20px 22px', boxShadow: 'var(--shadow-sm)',
              }}>
                <div className="label-caps" style={{ color: '#dc2626', marginBottom: '12px' }}>Falling</div>
                {data.period_comparison!.top_fallers.map((r, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '6px 0', borderBottom: i < (data.period_comparison?.top_fallers?.length ?? 0) - 1 ? '1px solid var(--border)' : 'none' }}>
                    <span style={{ fontFamily: 'Raleway', fontSize: '0.85rem', color: 'var(--text-primary)' }}>{r.product}</span>
                    <span style={{ fontFamily: 'Raleway', fontWeight: 700, fontSize: '0.80rem', color: '#dc2626' }}>{r.delta_pct.toFixed(1)}%</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* New / Dropped products */}
          {(data.period_comparison!.new_products.length > 0 || data.period_comparison!.dropped_products.length > 0) && (
            <div style={{ display: 'flex', gap: '12px', marginTop: '16px', flexWrap: 'wrap' }}>
              {data.period_comparison!.new_products.length > 0 && (
                <div style={{ backgroundColor: 'rgba(22,163,74,0.06)', border: '1px solid rgba(22,163,74,0.18)', borderRadius: '12px', padding: '10px 14px' }}>
                  <span className="label-caps" style={{ color: '#16a34a', fontSize: '0.55rem' }}>New this period · </span>
                  <span style={{ fontFamily: 'Raleway', fontSize: '0.80rem', color: 'var(--text-secondary)' }}>{data.period_comparison!.new_products.join(', ')}</span>
                </div>
              )}
              {data.period_comparison!.dropped_products.length > 0 && (
                <div style={{ backgroundColor: 'rgba(220,38,38,0.06)', border: '1px solid rgba(220,38,38,0.18)', borderRadius: '12px', padding: '10px 14px' }}>
                  <span className="label-caps" style={{ color: '#dc2626', fontSize: '0.55rem' }}>Not sold this period · </span>
                  <span style={{ fontFamily: 'Raleway', fontSize: '0.80rem', color: 'var(--text-secondary)' }}>{data.period_comparison!.dropped_products.join(', ')}</span>
                </div>
              )}
            </div>
          )}
        </section>
      ) : data && data.has_dates && (
        <div style={{
          backgroundColor: 'var(--surface)', border: '1px solid var(--border)',
          borderRadius: '20px', padding: '24px', marginBottom: '40px',
          boxShadow: 'var(--shadow-sm)',
        }}>
          <p style={{ fontFamily: 'Raleway', fontSize: '0.85rem', color: 'var(--t2)' }}>
            {data.warning ?? 'Need at least 60 days of data for period comparison.'}
          </p>
        </div>
      )}

      {/* Anomalies */}
      {data && (
        <section>
          <h3 style={{ color: 'var(--t3)', marginBottom: '6px' }}>Unusual Days</h3>
          <p style={{ fontFamily: 'Raleway', fontSize: '0.78rem', color: 'var(--t2)', marginBottom: '20px' }}>
            Days where revenue was unusually high or low.
          </p>

          {data.anomalies.length === 0 ? (
            <div style={{
              backgroundColor: 'var(--surface)', border: '1px solid var(--border)',
              borderRadius: '20px', padding: '32px', textAlign: 'center',
              boxShadow: 'var(--shadow-sm)',
            }}>
              <p style={{ fontFamily: 'Raleway', color: 'var(--t2)', fontSize: '0.85rem' }}>
                No unusual days detected — your revenue is consistent.
              </p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {data.anomalies.map((a, i) => {
                const isSpike = a.direction === 'spike'
                const color = isSpike ? '#16a34a' : '#dc2626'
                return (
                  <div
                    key={i}
                    className="fade-up anomaly-row"
                    style={{
                      animationDelay: `${i * 40}ms`, opacity: 0,
                      display: 'flex', alignItems: 'center', gap: '16px',
                      backgroundColor: 'var(--surface)', border: '1px solid var(--border)',
                      borderLeft: `4px solid ${color}`, borderRadius: '16px',
                      padding: '14px 20px', boxShadow: 'var(--shadow-xs)',
                    }}
                  >
                    <span style={{ fontSize: '1.1rem', flexShrink: 0 }}>{isSpike ? '📈' : '📉'}</span>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontFamily: 'Raleway', fontWeight: 700, fontSize: '0.85rem', color: 'var(--t2)', marginBottom: '2px' }}>
                        {a.date_label || a.date}
                        {a.auto_label && <span style={{ fontWeight: 400, color: 'var(--t2)', marginLeft: '8px', fontSize: '0.78rem' }}>· {a.auto_label}</span>}
                      </div>
                      {a.top_product && (
                        <div style={{ fontFamily: 'Raleway', fontSize: '0.75rem', color: 'var(--t2)' }}>
                          Top: {a.top_product}
                        </div>
                      )}
                    </div>
                    <div style={{ textAlign: 'right', flexShrink: 0 }}>
                      <div style={{ fontFamily: 'Cormorant, serif', fontSize: '1.3rem', fontWeight: 500, color }}>
                        {currency}{a.revenue.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
                      </div>
                      <div style={{ fontFamily: 'Raleway', fontSize: '0.68rem', color: 'var(--t2)', marginTop: '1px' }}>
                        {a.pct_above > 0 ? '+' : ''}{Math.abs(a.pct_above).toFixed(0)}% vs typical
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </section>
      )}

      {loading && !data && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '8px' }}>
            <SkeletonMetric /><SkeletonMetric /><SkeletonMetric />
          </div>
          <SkeletonRecommendation />
          <SkeletonRecommendation />
        </div>
      )}
      {!data && !loading && !error && (
        <div style={{
          backgroundColor: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: '20px',
          padding: '48px 28px',
          textAlign: 'center',
          boxShadow: 'var(--shadow-sm)',
        }}>
          <div style={{ fontSize: '2rem', marginBottom: '12px' }}>📊</div>
          <div className="label-caps" style={{ color: 'var(--accent)', marginBottom: '10px' }}>No data available</div>
          <p style={{ fontFamily: 'Raleway', color: 'var(--t2)', fontSize: '0.85rem', maxWidth: '360px', margin: '0 auto', lineHeight: 1.65 }}>
            Upload a file with at least 30 days of sales history to unlock the Overview.
          </p>
        </div>
      )}
    </div>
  )
}
