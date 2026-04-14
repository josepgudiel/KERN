'use client'

import { useCallback } from 'react'
import { useSession } from '@/context/SessionContext'
import { getWhatsSelling } from '@/lib/api'
import { usePageData } from '@/lib/hooks'
import type { WhatsSelling } from '@/types'
import ClusterCard from '@/components/ClusterCard'
import ErrorCard from '@/components/ErrorCard'
import { SkeletonRecommendation } from '@/components/SkeletonCard'
import { TrendingUp, TrendingDown } from 'lucide-react'

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

  const { data, loading, error, slow, retry } = usePageData<WhatsSelling>(fetchData, sessionId ? `kern_cache_selling_${sessionId}` : undefined)

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
            Products
          </span>
        </div>
        <h1 style={{ color: 'var(--navy)', marginBottom: '14px' }}>
          What&apos;s Selling
        </h1>
        <p style={{
          fontFamily: 'Raleway',
          fontSize: '0.92rem',
          color: 'var(--text-muted)',
          maxWidth: '500px',
          lineHeight: 1.75,
        }}>
          How your products are performing &mdash; grouped, ranked, and trending.
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

      {data ? (
        <>
          <h3 style={{ color: 'var(--accent)', marginBottom: '18px' }}>Your Product Groups</h3>
          {data.clusters.length === 0 ? (
            <div style={{
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: '20px',
              padding: '40px 28px',
              textAlign: 'center',
              marginBottom: '24px',
              boxShadow: 'var(--shadow-sm)',
            }}>
              <div style={{ fontSize: '2rem', marginBottom: '12px' }}>{'\uD83D\uDCE6'}</div>
              <div className="label-caps" style={{ color: 'var(--accent)', marginBottom: '10px' }}>Need More Products</div>
              <p style={{
                fontFamily: 'Raleway',
                color: 'var(--text-muted)',
                fontSize: '0.85rem',
                maxWidth: '380px',
                margin: '0 auto',
                lineHeight: 1.65,
              }}>
                We need at least 4 different products to create performance groups.
                Your data has fewer than 4 products.
              </p>
            </div>
          ) : (
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(2, 1fr)',
              gap: '16px',
              marginBottom: '40px',
            }} className="grid-keep-2 lg:!grid-cols-4">
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
              <h3 style={{ color: 'var(--accent)', marginBottom: '18px' }}>Rising Stars</h3>
              <div style={{
                display: 'flex',
                gap: '16px',
                overflowX: 'auto',
                paddingBottom: '12px',
                marginBottom: '40px',
              }}>
                {data.rising_stars.map((p, i) => (
                  <div
                    key={p.product}
                    className={`card-navy fade-up fade-up-delay-${Math.min(i + 1, 4)}`}
                    style={{
                      minWidth: 'min(210px, 70vw)',
                      padding: 'clamp(14px, 3vw, 20px)',
                      flexShrink: 0,
                    }}
                  >
                    <p style={{ fontFamily: 'Raleway', fontWeight: 600, fontSize: '0.88rem', color: '#ffffff', marginBottom: '6px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '100%' }}>
                      {p.product}
                    </p>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      color: '#16a34a',
                      fontSize: '0.82rem',
                      fontFamily: 'Raleway',
                      marginBottom: '6px',
                    }}>
                      <TrendingUp size={14} /> +{p.growth_pct.toFixed(1)}%
                    </div>
                    <p className="number-display" style={{ color: '#93c5fd', fontSize: '1.2rem' }}>
                      {currency}{p.recent_revenue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </p>
                  </div>
                ))}
              </div>
            </>
          )}

          {/* Declining */}
          {data.declining_products.length > 0 && (
            <>
              <h3 style={{ color: 'var(--accent)', marginBottom: '18px' }}>Declining Products</h3>
              <div style={{
                display: 'flex',
                gap: '16px',
                overflowX: 'auto',
                paddingBottom: '12px',
                marginBottom: '40px',
              }}>
                {data.declining_products.map((p, i) => (
                  <div
                    key={p.product}
                    className={`card-navy fade-up fade-up-delay-${Math.min(i + 1, 4)}`}
                    style={{
                      minWidth: 'min(210px, 70vw)',
                      padding: 'clamp(14px, 3vw, 20px)',
                      flexShrink: 0,
                    }}
                  >
                    <p style={{ fontFamily: 'Raleway', fontWeight: 600, fontSize: '0.88rem', color: '#ffffff', marginBottom: '6px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', maxWidth: '100%' }}>
                      {p.product}
                    </p>
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '4px',
                      color: '#dc2626',
                      fontSize: '0.82rem',
                      fontFamily: 'Raleway',
                      marginBottom: '6px',
                    }}>
                      <TrendingDown size={14} /> {p.decline_pct.toFixed(1)}%
                    </div>
                    <p className="number-display" style={{ color: '#93c5fd', fontSize: '1.2rem' }}>
                      {currency}{p.recent_revenue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </p>
                  </div>
                ))}
              </div>
            </>
          )}

          {/* Basket info — shown when single-item transactions dominate */}
          {data.basket_info && data.basket_rules.length === 0 && (
            <div style={{
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: '20px',
              padding: '20px 24px',
              marginBottom: '40px',
              boxShadow: 'var(--shadow-sm)',
            }}>
              <div className="label-caps" style={{ color: 'var(--accent)', marginBottom: '8px' }}>Bundle Suggestions</div>
              <p style={{ fontFamily: 'Raleway', color: 'var(--text-muted)', fontSize: '0.85rem', lineHeight: 1.65, margin: 0 }}>
                {data.basket_info}
              </p>
            </div>
          )}

          {/* Basket Rules */}
          {data.basket_rules.length > 0 && (
            <>
              <h3 style={{ color: 'var(--accent)', marginBottom: '18px' }}>Frequently Bought Together</h3>
              <div className="overflow-x-mobile" style={{
                backgroundColor: 'var(--surface)',
                border: '1px solid var(--border)',
                borderRadius: '20px',
                overflow: 'hidden',
                boxShadow: 'var(--shadow-sm)',
              }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: '500px' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid var(--border)' }}>
                      <th className="label-caps" style={{ textAlign: 'left', color: 'var(--accent)', padding: '14px 18px' }}>Item A</th>
                      <th className="label-caps" style={{ textAlign: 'left', color: 'var(--accent)', padding: '14px 18px' }}>Item B</th>
                      <th className="label-caps" style={{ textAlign: 'right', color: 'var(--accent)', padding: '14px 18px' }} title="When Item A is sold, how often Item B is also sold">How Often Together</th>
                      <th className="label-caps" style={{ textAlign: 'right', color: 'var(--accent)', padding: '14px 18px' }} title="How strong the pairing is — Strong means much more likely than chance">Signal</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.basket_rules.slice(0, 10).map((r, i) => {
                      const signalLabel = r.lift >= 2 ? 'Strong' : r.lift >= 1.5 ? 'Moderate' : 'Weak'
                      const signalColor = r.lift >= 2 ? '#16a34a' : r.lift >= 1.5 ? '#d97706' : 'var(--text-muted)'
                      return (
                        <tr key={i} style={{
                          borderBottom: i < Math.min(data.basket_rules.length, 10) - 1 ? '1px solid var(--border)' : 'none',
                          transition: 'background-color 0.15s ease',
                        }}
                          onMouseEnter={(e) => { e.currentTarget.style.backgroundColor = 'var(--bg-alt)' }}
                          onMouseLeave={(e) => { e.currentTarget.style.backgroundColor = 'transparent' }}
                        >
                          <td style={{ fontFamily: 'Raleway', color: 'var(--text-primary)', fontSize: '0.82rem', padding: '12px 18px' }}>{r.antecedent}</td>
                          <td style={{ fontFamily: 'Raleway', color: 'var(--text-primary)', fontSize: '0.82rem', padding: '12px 18px' }}>{r.consequent}</td>
                          <td style={{ fontFamily: 'Raleway', color: 'var(--text-primary)', fontSize: '0.82rem', padding: '12px 18px', textAlign: 'right' }}>{r.confidence_pct.toFixed(0)}% of the time</td>
                          <td style={{ fontFamily: 'Raleway', fontSize: '0.82rem', padding: '12px 18px', textAlign: 'right', fontWeight: 600, color: signalColor }}>
                            {signalLabel}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </>
      ) : (
        loading && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <SkeletonRecommendation />
            <SkeletonRecommendation />
          </div>
        )
      )}
    </div>
  )
}
