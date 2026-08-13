'use client'

import { CalendarRange, GitCompareArrows, RotateCw } from 'lucide-react'
import {
  COMPARE_OPTIONS,
  RANGE_OPTIONS,
  useDashboardControls,
  type CompareKey,
  type RangeKey,
} from '@/context/DashboardControlsContext'
import { iconProps } from '@/components/ui'

/* ─── Segmented range control ────────────────────────────────────────────── */

function RangeSegments({ value, onChange }: { value: RangeKey; onChange: (k: RangeKey) => void }) {
  return (
    <div
      role="group"
      aria-label="Date range"
      style={{
        display: 'inline-flex',
        padding: '2px',
        gap: '2px',
        backgroundColor: 'var(--bg)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius)',
      }}
    >
      {RANGE_OPTIONS.map(opt => {
        const active = opt.key === value
        return (
          <button
            key={opt.key}
            type="button"
            aria-pressed={active}
            onClick={() => onChange(opt.key)}
            style={{
              padding: '5px 12px',
              minHeight: 0,
              background: active ? 'var(--accent-dim)' : 'transparent',
              border: 'none',
              borderRadius: '5px',
              cursor: 'pointer',
              fontFamily: 'var(--font-heading)',
              fontSize: '0.78rem',
              fontWeight: active ? 600 : 500,
              letterSpacing: '-0.004em',
              color: active ? 'var(--accent)' : 'var(--t2)',
              transition: 'background-color 0.15s ease, color 0.15s ease',
            }}
            onMouseEnter={(e) => { if (!active) e.currentTarget.style.color = 'var(--t1)' }}
            onMouseLeave={(e) => { if (!active) e.currentTarget.style.color = 'var(--t2)' }}
          >
            {opt.label}
          </button>
        )
      })}
    </div>
  )
}

/* ─── Comparison select ──────────────────────────────────────────────────── */

function CompareSelect({ value, onChange }: { value: CompareKey; onChange: (k: CompareKey) => void }) {
  return (
    <label style={{ display: 'inline-flex', alignItems: 'center', gap: '7px' }}>
      <GitCompareArrows {...iconProps} aria-hidden />
      <span className="sr-only-label" style={{ position: 'absolute', width: 1, height: 1, overflow: 'hidden', clip: 'rect(0 0 0 0)', whiteSpace: 'nowrap' }}>
        Comparison period
      </span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value as CompareKey)}
        style={{
          appearance: 'none',
          padding: '6px 26px 6px 10px',
          backgroundColor: 'var(--bg)',
          backgroundImage:
            "url(\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='6' viewBox='0 0 10 6'%3E%3Cpath d='M1 1l4 4 4-4' fill='none' stroke='%23b4531f' stroke-width='1.5' stroke-linecap='round'/%3E%3C/svg%3E\")",
          backgroundRepeat: 'no-repeat',
          backgroundPosition: 'right 9px center',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius)',
          fontFamily: 'var(--font-body)',
          fontSize: '0.75rem',
          color: 'var(--t1)',
          cursor: 'pointer',
        }}
      >
        {COMPARE_OPTIONS.map(opt => (
          <option key={opt.key} value={opt.key} style={{ backgroundColor: 'var(--bg-card)' }}>
            {opt.label}
          </option>
        ))}
      </select>
    </label>
  )
}

/* ─── Toolbar ────────────────────────────────────────────────────────────── */

function formatWindow(start: string | null, end: string | null): string | null {
  if (!start || !end) return null
  const fmt = (iso: string) => {
    const d = new Date(iso)
    return isNaN(d.getTime())
      ? iso
      : d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }
  return `${fmt(start)} to ${fmt(end)}`
}

/**
 * Persistent control bar above every dashboard page.
 *
 * Refresh is fully wired: it drops the session cache and re-runs every mounted
 * page's fetch. Range and comparison are persisted operator state and drive the
 * displayed window; see the note rendered below the bar for the server-side
 * caveat.
 */
export default function DashboardToolbar() {
  const { range, setRange, compare, setCompare, resolved, datasetRange, refresh, refreshing } =
    useDashboardControls()

  const windowLabel = formatWindow(resolved.start, resolved.end)
  const isSubsetSelected = resolved.days != null && !!datasetRange && range !== 'all' && !resolved.clampedToDataset

  return (
    <div style={{ marginBottom: '20px' }}>
      <div
        className="toolbar"
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px',
          padding: '10px 16px',
          backgroundColor: 'var(--bg-card)',
          border: '1px solid var(--border)',
          borderRadius: 'var(--radius-card)',
        }}
      >
        {/* Left: the window currently in view */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '9px', minWidth: 0 }}>
          <CalendarRange {...iconProps} aria-hidden />
          <div style={{ minWidth: 0 }}>
            {/* A date span is data, so it keeps the mono. */}
            <div style={{
              fontFamily: 'var(--font-mono)',
              fontVariantNumeric: 'tabular-nums',
              fontSize: '0.74rem',
              color: 'var(--t1)',
              whiteSpace: 'nowrap',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
            }}>
              {windowLabel ?? 'No dated records'}
            </div>
            <div style={{
              fontFamily: 'var(--font-body)',
              fontSize: '0.64rem',
              color: 'var(--t2)',
            }}>
              {resolved.days != null
                ? `${resolved.days.toLocaleString()} days${resolved.clampedToDataset ? ' · full dataset' : ''}`
                : 'Upload data with a date column to filter by period'}
            </div>
          </div>
        </div>

        {/* Right: controls */}
        <div
          className="toolbar-controls"
          style={{ display: 'flex', alignItems: 'center', gap: '10px', flexShrink: 0 }}
        >
          <RangeSegments value={range} onChange={setRange} />
          <CompareSelect value={compare} onChange={setCompare} />
          <button
            type="button"
            onClick={refresh}
            disabled={refreshing}
            title="Clear cached results and re-run every page"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '7px',
              padding: '6px 12px',
              backgroundColor: 'transparent',
              border: '1px solid var(--border2)',
              borderRadius: '6px',
              cursor: refreshing ? 'default' : 'pointer',
              fontFamily: 'var(--font-heading)',
              fontSize: '0.78rem',
              fontWeight: 500,
              letterSpacing: '-0.004em',
              color: 'var(--t1)',
              opacity: refreshing ? 0.55 : 1,
              transition: 'border-color 0.15s ease, background-color 0.15s ease',
            }}
            onMouseEnter={(e) => {
              if (refreshing) return
              e.currentTarget.style.borderColor = 'var(--t1)'
              e.currentTarget.style.backgroundColor = 'var(--bg-alt)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--border2)'
              e.currentTarget.style.backgroundColor = 'transparent'
            }}
          >
            <RotateCw
              size={14}
              strokeWidth={1.75}
              style={{
                color: 'var(--accent)',
                opacity: 0.85,
                animation: refreshing ? 'toolbarSpin 0.7s linear infinite' : 'none',
              }}
              aria-hidden
            />
            {refreshing ? 'Refreshing' : 'Refresh'}
          </button>
        </div>
      </div>

      {/* Honest about what the range control does today. The endpoints in
          lib/api.ts take a session id only (no date parameters exist yet), so
          a narrower window must not be presented as if it filtered the figures. */}
      {isSubsetSelected && (
        <p style={{
          margin: '7px 2px 0',
          fontFamily: 'var(--font-body)',
          fontSize: '0.66rem',
          color: 'var(--t2)',
          lineHeight: 1.5,
        }}>
          Figures below still cover the whole file. Filtering by date range is not switched on yet.
        </p>
      )}

      <style>{`@keyframes toolbarSpin { to { transform: rotate(360deg); } }`}</style>
    </div>
  )
}
