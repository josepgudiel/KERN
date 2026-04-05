'use client'

import { useState, useRef, useEffect, type DragEvent, type ChangeEvent } from 'react'
import { Upload, FileSpreadsheet, Loader2, CheckCircle } from 'lucide-react'
import { uploadFile } from '@/lib/api'
import { useSession } from '@/context/SessionContext'
import { useRouter } from 'next/navigation'
import type { UploadResponse } from '@/types'

interface UploadZoneProps {
  onSuccess?: (meta: UploadResponse) => void
}

const PROGRESS_MESSAGES = [
  'Reading your file...',
  'Detecting columns...',
  'Running analysis...',
  'Building recommendations...',
]

export default function UploadZone({ onSuccess }: UploadZoneProps) {
  const [file, setFile] = useState<File | null>(null)
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [progressIdx, setProgressIdx] = useState(0)
  const [success, setSuccess] = useState(false)
  const [warningMessage, setWarningMessage] = useState<string | null>(null)
  const [marginPct, setMarginPct] = useState<string>('')
  const inputRef = useRef<HTMLInputElement>(null)
  const { setSessionId, setUploadMeta } = useSession()
  const router = useRouter()

  const accept = '.csv,.xlsx,.xls'

  // Cycle progress messages during upload
  useEffect(() => {
    if (!loading) return
    setProgressIdx(0)
    const interval = setInterval(() => {
      setProgressIdx((prev) => (prev + 1) % PROGRESS_MESSAGES.length)
    }, 1500)
    return () => clearInterval(interval)
  }, [loading])

  function handleFile(f: File) {
    setError(null)
    setSuccess(false)
    const ext = f.name.split('.').pop()?.toLowerCase()
    if (!ext || !['csv', 'xlsx', 'xls'].includes(ext)) {
      setError('Please upload a CSV or Excel file (.csv, .xlsx, .xls)')
      return
    }
    setFile(f)
  }

  function onDrop(e: DragEvent) {
    e.preventDefault()
    setDragging(false)
    if (loading) return
    const f = e.dataTransfer.files[0]
    if (f) handleFile(f)
  }

  function onChange(e: ChangeEvent<HTMLInputElement>) {
    if (loading) return
    const f = e.target.files?.[0]
    if (f) handleFile(f)
  }

  function resetZone() {
    setFile(null)
    setError(null)
    setSuccess(false)
    if (inputRef.current) inputRef.current.value = ''
  }

  async function onAnalyze() {
    if (!file) return
    setLoading(true)
    setError(null)
    setSuccess(false)
    try {
      const marginDecimal = marginPct !== '' ? parseFloat(marginPct) / 100 : undefined
      const res = await uploadFile(file, marginDecimal)
      setSessionId(res.session_id)
      setUploadMeta(res)

      // Show success flash then redirect
      setSuccess(true)
      setLoading(false)

      if (res.warning) {
        setWarningMessage(res.warning)
        await new Promise((r) => setTimeout(r, 2500))
      } else {
        await new Promise((r) => setTimeout(r, 600))
      }

      if (onSuccess) {
        onSuccess(res)
      } else {
        router.push('/dashboard/action-center')
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : ''
      const detail = msg.match(/"detail"\s*:\s*"([^"]+)"/)?.[1]
      setError(detail || "Couldn't read this file. Make sure it has at least a product column and a revenue or quantity column.")
      setLoading(false)
    }
  }

  return (
    <div style={{ width: '100%' }}>
      <div
        onDragOver={(e) => { e.preventDefault(); if (!loading) setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        onClick={() => { if (!loading) inputRef.current?.click() }}
        style={{
          border: '2px dashed',
          borderColor: dragging ? 'var(--accent)' : 'var(--border-warm)',
          borderRadius: '20px',
          padding: 'clamp(24px, 5vw, 40px) clamp(16px, 3vw, 24px)',
          textAlign: 'center',
          transition: 'all 0.2s ease',
          cursor: loading ? 'default' : 'pointer',
          opacity: loading ? 0.8 : 1,
          backgroundColor: dragging ? 'rgba(37,99,235,0.04)' : 'var(--surface-warm)',
          transform: dragging ? 'scale(1.01)' : 'scale(1)',
        }}
        onMouseEnter={(e) => {
          if (!loading && !dragging) {
            e.currentTarget.style.borderColor = 'var(--border-accent)'
            e.currentTarget.style.backgroundColor = 'var(--bg-alt)'
          }
        }}
        onMouseLeave={(e) => {
          if (!dragging) {
            e.currentTarget.style.borderColor = 'var(--border-warm)'
            e.currentTarget.style.backgroundColor = 'var(--surface-warm)'
          }
        }}
      >
        <input ref={inputRef} type="file" accept={accept} onChange={onChange} style={{ display: 'none' }} disabled={loading} />

        {success ? (
          <>
            <CheckCircle style={{ margin: '0 auto 12px', color: '#16a34a' }} size={40} strokeWidth={1.5} />
            <p style={{ fontFamily: 'Raleway', fontWeight: 700, color: '#16a34a', fontSize: '1.05rem', marginBottom: '4px' }}>
              Analysis complete &mdash; loading your dashboard
            </p>
          </>
        ) : !file ? (
          <>
            <Upload style={{ margin: '0 auto 12px', color: 'var(--accent)' }} size={40} strokeWidth={1.5} />
            <p style={{ fontFamily: 'Raleway', fontWeight: 700, color: 'var(--navy)', fontSize: '1.05rem', marginBottom: '4px' }}>
              Drag &amp; drop your file here
            </p>
            <p style={{ fontFamily: 'Raleway', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
              or click to browse &mdash; CSV, XLSX, XLS
            </p>
          </>
        ) : (
          <>
            <FileSpreadsheet style={{ margin: '0 auto 12px', color: 'var(--accent)' }} size={40} strokeWidth={1.5} />
            <p style={{ fontFamily: 'Raleway', fontWeight: 700, color: 'var(--navy)', fontSize: '1.05rem', marginBottom: '4px' }}>{file.name}</p>
            <p style={{ fontFamily: 'Raleway', color: 'var(--text-muted)', fontSize: '0.82rem' }}>
              {(file.size / 1024).toFixed(1)} KB
            </p>
          </>
        )}
      </div>

      {error && (
        <div style={{
          marginTop: '16px',
          borderLeft: '4px solid #dc2626',
          backgroundColor: 'var(--surface)',
          borderRadius: '14px',
          padding: '14px 16px',
          boxShadow: 'var(--shadow-xs)',
        }}>
          <p style={{ fontFamily: 'Raleway', color: '#dc2626', fontSize: '0.82rem', marginBottom: '8px' }}>{error}</p>
          <button
            onClick={resetZone}
            className="label-caps"
            style={{
              color: 'var(--accent)',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              transition: 'color 0.15s ease',
            }}
            onMouseEnter={(e) => { e.currentTarget.style.color = 'var(--navy)' }}
            onMouseLeave={(e) => { e.currentTarget.style.color = 'var(--accent)' }}
          >
            Try another file &rarr;
          </button>
        </div>
      )}

      {file && !success && (
        <div style={{
          marginTop: '16px',
          padding: '14px 16px',
          borderRadius: '14px',
          backgroundColor: 'var(--surface-warm)',
          border: '1px solid var(--border-warm)',
        }}>
          <label style={{
            display: 'block',
            fontFamily: 'Raleway',
            fontWeight: 600,
            fontSize: '0.82rem',
            color: 'var(--navy)',
            marginBottom: '6px',
          }}>
            Your gross margin % <span style={{ fontWeight: 400, color: 'var(--text-muted)' }}>(optional)</span>
          </label>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <input
              type="number"
              min="5"
              max="99"
              step="1"
              placeholder="e.g. 65"
              value={marginPct}
              onChange={(e) => setMarginPct(e.target.value)}
              disabled={loading}
              style={{
                width: '90px',
                padding: '8px 10px',
                borderRadius: '8px',
                border: '1px solid var(--border-warm)',
                backgroundColor: 'var(--bg)',
                fontFamily: 'Raleway',
                fontSize: '0.88rem',
                color: 'var(--navy)',
                outline: 'none',
              }}
            />
            <span style={{ fontFamily: 'Raleway', fontSize: '0.82rem', color: 'var(--text-muted)' }}>%</span>
          </div>
          <p style={{ fontFamily: 'Raleway', fontSize: '0.72rem', color: 'var(--text-muted)', marginTop: '6px' }}>
            Leave blank to use the 65% default — enter your actual margin for accurate dollar impacts.
          </p>
        </div>
      )}

      {file && !success && (
        <button
          onClick={onAnalyze}
          disabled={loading}
          className="btn-primary"
          style={{
            marginTop: '20px',
            width: '100%',
            justifyContent: 'center',
            padding: '14px 24px',
            minHeight: '48px',
            opacity: loading ? 0.6 : 1,
          }}
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin" size={18} />
              Analyzing your data&hellip;
            </>
          ) : (
            'Analyze'
          )}
        </button>
      )}

      {loading && (
        <p className="animate-pulse" style={{
          textAlign: 'center',
          fontFamily: 'Raleway',
          color: 'var(--text-muted)',
          fontSize: '0.82rem',
          marginTop: '12px',
        }}>
          {PROGRESS_MESSAGES[progressIdx]}
        </p>
      )}

      {warningMessage && (
        <div style={{
          marginTop: '12px',
          padding: '12px 14px',
          borderRadius: '14px',
          backgroundColor: 'rgba(217,119,6,0.06)',
          border: '1px solid rgba(217,119,6,0.20)',
        }}>
          <p style={{ fontFamily: 'Raleway', color: '#92400e', fontSize: '0.78rem' }}>
            {'\u26A0\uFE0F'} {warningMessage}
          </p>
        </div>
      )}
    </div>
  )
}
