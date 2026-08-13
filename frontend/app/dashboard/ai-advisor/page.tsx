'use client'

import { useState, useEffect } from 'react'
import { useSession } from '@/context/SessionContext'
import AdvisorChat from '@/components/AdvisorChat'
import { getDataSummary } from '@/lib/api'
import type { DataSummaryResponse } from '@/types'
import { PageHeader } from '@/components/ui'

export default function AIAdvisorPage() {
  const { sessionId, businessProfile } = useSession()
  const [summary, setSummary] = useState<DataSummaryResponse | null>(null)
  const [summaryLoading, setSummaryLoading] = useState(false)

  useEffect(() => {
    if (!sessionId) return
    setSummaryLoading(true)
    getDataSummary(sessionId)
      .then(setSummary)
      .catch(() => setSummary(null))
      .finally(() => setSummaryLoading(false))
  }, [sessionId])

  const top3 = summary?.top_products?.slice(0, 3) ?? []

  return (
    <div>
      <PageHeader
        title="Business Advisor"
        context="Ask a question in plain English. The answers come from the file you uploaded."
      />

      <div className="fade-up advisor-layout" style={{ display: 'flex', gap: '20px', height: 'calc(100vh - 190px)', minHeight: '400px' }}>
        {/* Left: Your data panel */}
        <div className="advisor-profile-panel" style={{ width: '35%', flexShrink: 0 }}>
          <div style={{
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-card)',
            padding: '24px 22px',
            height: '100%',
            display: 'flex',
            flexDirection: 'column',
            gap: '0',
          }}>
            <h3 style={{ marginBottom: '18px' }}>Your data</h3>

            {summaryLoading && (
              <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {[80, 60, 100, 70].map((w, i) => (
                  <div key={i} className="skeleton" style={{ height: '14px', width: `${w}%`, borderRadius: '2px' }} />
                ))}
              </div>
            )}

            {!summaryLoading && !summary && (
              <p style={{
                fontFamily: 'var(--font-body)',
                fontSize: '0.82rem',
                color: 'var(--text-muted)',
                lineHeight: 1.65,
                flex: 1,
              }}>
                Load a sales file and the answers here will be about your own numbers.
              </p>
            )}

            {!summaryLoading && summary && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '18px', flex: 1 }}>
                {/* Date range */}
                <div>
                  <div className="ui-label" style={{ marginBottom: '4px' }}>
                    Date range
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontVariantNumeric: 'tabular-nums', fontSize: '0.78rem', color: 'var(--text-primary)' }}>
                    {summary.date_range}
                  </div>
                </div>

                {/* Total transactions */}
                <div>
                  <div className="ui-label" style={{ marginBottom: '4px' }}>
                    Transactions
                  </div>
                  <div style={{ fontFamily: 'var(--font-mono)', fontVariantNumeric: 'tabular-nums', fontSize: '0.78rem', color: 'var(--text-primary)' }}>
                    {summary.total_transactions.toLocaleString()}
                  </div>
                </div>

                {/* Top 3 products */}
                {top3.length > 0 && (
                  <div>
                    <div className="ui-label" style={{ marginBottom: '8px' }}>
                      Top products
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                      {top3.map((p, i) => (
                        <div key={i} style={{ display: 'flex', alignItems: 'baseline', gap: '8px' }}>
                          <div style={{
                            fontFamily: 'var(--font-mono)',
                            fontVariantNumeric: 'tabular-nums',
                            fontSize: '0.66rem',
                            color: 'var(--accent)',
                            width: '14px',
                            flexShrink: 0,
                          }}>
                            {i + 1}
                          </div>
                          <div style={{
                            fontFamily: 'var(--font-body)',
                            fontSize: '0.78rem',
                            color: 'var(--text-secondary)',
                            lineHeight: 1.4,
                          }}>
                            {p}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Best day */}
                {summary.best_dow && summary.best_dow !== 'unknown' && (
                  <div>
                    <div className="ui-label" style={{ marginBottom: '4px' }}>
                      Best day
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono)', fontVariantNumeric: 'tabular-nums', fontSize: '0.78rem', color: 'var(--text-primary)' }}>
                      {summary.best_dow}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right: Chat */}
        <div style={{
          flex: 1,
          backgroundColor: 'var(--bg-surface)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-card)',
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
        }}>
          <AdvisorChat businessProfile={businessProfile} />
        </div>
      </div>
    </div>
  )
}
