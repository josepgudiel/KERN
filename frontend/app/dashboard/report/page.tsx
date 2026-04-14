'use client'

import { useState, useEffect } from 'react'
import { useSession } from '@/context/SessionContext'
import { postReport } from '@/lib/api'
import type { ReportResponse } from '@/types'
import ErrorCard from '@/components/ErrorCard'

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
        setError('AI report unavailable — make sure GROQ_API_KEY is set in the backend .env file.')
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
      {/* Page header */}
      <div style={{ marginBottom: 'clamp(28px, 5vw, 48px)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
          <div style={{ width: '28px', height: '1px', backgroundColor: 'var(--accent)' }} />
          <span className="label-caps" style={{ color: 'var(--accent)' }}>Summary</span>
        </div>
        <h1 style={{ color: 'var(--navy)', marginBottom: '14px' }}>Report</h1>
        <p style={{ fontFamily: 'Raleway', fontSize: '0.92rem', color: 'var(--text-muted)', maxWidth: '500px', lineHeight: 1.75 }}>
          A plain-English business performance summary you can share with your accountant, partner, or investor.
        </p>
        <div className="divider" style={{ marginTop: '24px' }} />
      </div>

      {error && <div style={{ marginBottom: '24px' }}><ErrorCard message={error} onRetry={generate} /></div>}

      {/* Generate button */}
      {!data && !loading && (
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start', gap: '16px' }}>
          <button onClick={generate} className="btn-primary">
            Generate Report
          </button>
          <p style={{ fontFamily: 'Raleway', fontSize: '0.78rem', color: 'var(--text-muted)', lineHeight: 1.6, maxWidth: '420px' }}>
            Takes about 5–10 seconds. The report is generated fresh each time from your current data.
          </p>
        </div>
      )}

      {/* Loading state */}
      {loading && (
        <div style={{
          backgroundColor: 'var(--surface)', border: '1px solid var(--border)',
          borderLeft: '4px solid var(--accent)', borderRadius: '20px',
          padding: '28px 32px', boxShadow: 'var(--shadow-sm)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <div style={{
              width: '20px', height: '20px', borderRadius: '50%',
              border: '2px solid var(--accent)', borderTopColor: 'transparent',
              animation: 'spin 0.8s linear infinite',
              flexShrink: 0,
            }} />
            <p style={{ fontFamily: 'Raleway', color: 'var(--text-secondary)', fontSize: '0.88rem' }}>
              Writing your report — this takes about 10 seconds…
            </p>
          </div>
          <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
        </div>
      )}

      {/* Report display */}
      {data && (
        <div className="fade-up">
          {/* Period label + actions */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px', marginBottom: '24px' }}>
            <div>
              <div className="label-caps" style={{ color: 'var(--accent)', marginBottom: '4px' }}>Period</div>
              <div style={{ fontFamily: 'Raleway', fontWeight: 600, fontSize: '0.92rem', color: 'var(--t2)' }}>
                {data.period_label}
              </div>
            </div>
            <div className="report-actions" style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <button onClick={copyReport} className="btn-ghost no-print" style={{ fontSize: '0.68rem' }}>
                {copied ? '✓ Copied' : 'Copy'}
              </button>
              <button onClick={downloadReport} className="btn-ghost no-print" style={{ fontSize: '0.68rem' }}>
                Download .txt
              </button>
              <button onClick={() => window.print()} className="btn-ghost no-print" style={{ fontSize: '0.68rem' }}>
                Print
              </button>
              <button onClick={generate} className="btn-ghost no-print" style={{ fontSize: '0.68rem' }}>
                Regenerate
              </button>
            </div>
          </div>

          {/* Report body */}
          <div className="report-body" style={{
            backgroundColor: 'var(--surface)', border: '1px solid var(--border)',
            borderRadius: '20px', padding: '36px 40px', boxShadow: 'var(--shadow-md)',
          }}>
            {data.report.split('\n\n').filter(Boolean).map((para, i) => (
              <p key={i} style={{
                fontFamily: 'Raleway', fontSize: '0.95rem',
                color: 'var(--text-primary)', lineHeight: 1.85,
                marginBottom: i < data.report.split('\n\n').length - 1 ? '1.4em' : 0,
              }}>
                {para.trim()}
              </p>
            ))}
          </div>

          <p style={{
            fontFamily: 'Raleway', fontSize: '0.68rem', color: 'var(--text-muted)',
            textAlign: 'center', marginTop: '16px',
          }}>
            AI-generated from your sales data · Always verify numbers before sharing externally
          </p>
        </div>
      )}
    </div>
  )
}
