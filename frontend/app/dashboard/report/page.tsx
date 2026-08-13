'use client'

import { useState, useEffect } from 'react'
import { useSession } from '@/context/SessionContext'
import { postReport } from '@/lib/api'
import type { ReportResponse } from '@/types'
import ErrorCard from '@/components/ErrorCard'
import { Card, PageHeader } from '@/components/ui'
import { Check } from 'lucide-react'

export default function ReportPage() {
  const { sessionId } = useSession()
  const [data, setData]       = useState<ReportResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState<string | null>(null)
  const [copied, setCopied]   = useState(false)

  async function generate() {
    if (!sessionId) return
    setLoading(true)
    setError(null)
    setData(null)
    try {
      const result = await postReport(sessionId)
      setData(result)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'An unexpected error occurred.'
      if (msg.includes('503') || msg.includes('GROQ_API_KEY')) {
        setError('Report generation is unavailable right now. Check that the backend is configured, then try again.')
      } else {
        setError(msg)
      }
    } finally {
      setLoading(false)
    }
  }

  async function copyReport() {
    if (!data?.report) return
    await navigator.clipboard.writeText(data.report)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  useEffect(() => {
    if (sessionId) generate()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  function downloadReport() {
    if (!data?.report) return
    const blob = new Blob([data.report], { type: 'text/plain' })
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `analytic-report-${data.period_label.replace(/\s/g, '-')}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div>
      <PageHeader
        title="Report"
        context="A plain-English write-up of the period, ready to send to an accountant, a partner or a lender."
      />

      {error && <div style={{ marginBottom: '20px' }}><ErrorCard message={error} onRetry={generate} /></div>}

      {/* Generate button */}
      {!data && !loading && (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '16px' }}>
          <button onClick={generate} className="btn-primary">
            Write the report
          </button>
          <p style={{ fontFamily: 'var(--font-body)', fontSize: '0.78rem', color: 'var(--t2)', lineHeight: 1.6, maxWidth: '420px' }}>
            Takes about ten seconds. Each one is written fresh from the data you have loaded.
          </p>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <Card padding="24px 28px">
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{
              width: '20px', height: '20px', borderRadius: '50%',
              border: '2px solid var(--accent)', borderTopColor: 'transparent',
              animation: 'spin 0.8s linear infinite',
              flexShrink: 0,
            }} />
            <p style={{ fontFamily: 'var(--font-body)', color: 'var(--t2)', fontSize: '0.88rem' }}>
              Writing your report. This takes about ten seconds.
            </p>
          </div>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </Card>
      )}

      {/* Report display */}
      {data && (
        <div className="fade-up">
          {/* Period label + actions */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', marginBottom: '24px' }}>
            <div>
              <div className="ui-label" style={{ marginBottom: '4px' }}>Period covered</div>
              <div style={{ fontFamily: 'var(--font-body)', fontWeight: 600, fontSize: '0.92rem', color: 'var(--t1)' }}>
                {data.period_label}
              </div>
            </div>
            <div className="report-actions" style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <button onClick={copyReport} className="btn-ghost no-print">
                {copied ? <><Check size={14} strokeWidth={2} aria-hidden /> Copied</> : 'Copy'}
              </button>
              <button onClick={downloadReport} className="btn-ghost no-print">
                Download
              </button>
              <button onClick={() => window.print()} className="btn-ghost no-print">
                Print
              </button>
              <button onClick={generate} className="btn-ghost no-print">
                Write it again
              </button>
            </div>
          </div>

          {/* Report body */}
          <Card className="report-body" padding="32px 36px" style={{ maxWidth: '72ch' }}>
            {data.report.split('\n\n').filter(Boolean).map((para, i) => (
              <p key={i} style={{
                fontFamily: 'var(--font-body)', fontSize: '0.95rem',
                color: 'var(--t1)', lineHeight: 1.85,
                marginBottom: i < data.report.split('\n\n').length - 1 ? '1.4em' : 0,
              }}>
                {para.trim()}
              </p>
            ))}
          </Card>

          <p style={{
            fontFamily: 'var(--font-body)', fontSize: '0.68rem', color: 'var(--t2)',
            textAlign: 'left', marginTop: '14px',
          }}>
            Written from the sales data you uploaded. Check the figures before you send this on.
          </p>
        </div>
      )}
    </div>
  )
}
