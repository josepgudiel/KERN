'use client'

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react'
import { useSession } from '@/context/SessionContext'
import { clearKernCache } from '@/lib/cache'

/* ─── Range presets ──────────────────────────────────────────────────────── */

export type RangeKey = '30d' | '90d' | '12m' | 'all'
export type CompareKey = 'prior_period' | 'prior_year' | 'none'

export const RANGE_OPTIONS: { key: RangeKey; label: string; days: number | null }[] = [
  { key: '30d', label: '30D',  days: 30 },
  { key: '90d', label: '90D',  days: 90 },
  { key: '12m', label: '12M',  days: 365 },
  { key: 'all', label: 'All',  days: null },
]

export const COMPARE_OPTIONS: { key: CompareKey; label: string }[] = [
  { key: 'prior_period', label: 'vs prior period' },
  { key: 'prior_year',   label: 'vs same period last year' },
  { key: 'none',         label: 'No comparison' },
]

/* ─── Resolved window ────────────────────────────────────────────────────── */

export interface ResolvedRange {
  /** ISO date (YYYY-MM-DD) or null when the dataset has no usable dates. */
  start: string | null
  end: string | null
  /** Days covered by the resolved window, or null when unknown. */
  days: number | null
  /** True when the selected preset is wider than the data actually on hand. */
  clampedToDataset: boolean
}

interface DashboardControlsValue {
  range: RangeKey
  setRange: (key: RangeKey) => void
  compare: CompareKey
  setCompare: (key: CompareKey) => void
  resolved: ResolvedRange
  /** Full extent of the uploaded dataset, from the upload response. */
  datasetRange: { min: string; max: string } | null
  /** Increments on every manual refresh; page data hooks re-run when it changes. */
  refreshToken: number
  refresh: () => void
  refreshing: boolean
}

const DashboardControlsContext = createContext<DashboardControlsValue | null>(null)

const STORAGE_KEY = 'kern_dashboard_controls'

function isRangeKey(v: unknown): v is RangeKey {
  return typeof v === 'string' && RANGE_OPTIONS.some(o => o.key === v)
}

function isCompareKey(v: unknown): v is CompareKey {
  return typeof v === 'string' && COMPARE_OPTIONS.some(o => o.key === v)
}

function toISODate(d: Date): string {
  return d.toISOString().slice(0, 10)
}

function parseDate(value: string | undefined | null): Date | null {
  if (!value) return null
  const d = new Date(value)
  return isNaN(d.getTime()) ? null : d
}

/**
 * Resolves a preset against the dataset's real extent, so the toolbar can never
 * advertise a window the data does not cover.
 */
function resolveRange(
  key: RangeKey,
  datasetRange: { min: string; max: string } | null,
): ResolvedRange {
  const min = parseDate(datasetRange?.min)
  const max = parseDate(datasetRange?.max)
  if (!min || !max) return { start: null, end: null, days: null, clampedToDataset: false }

  const preset = RANGE_OPTIONS.find(o => o.key === key)
  const datasetDays = Math.floor((max.getTime() - min.getTime()) / 86_400_000) + 1

  if (!preset?.days) {
    return { start: toISODate(min), end: toISODate(max), days: datasetDays, clampedToDataset: false }
  }

  const wanted = new Date(max.getTime() - (preset.days - 1) * 86_400_000)
  const clamped = wanted < min
  const start = clamped ? min : wanted
  const days = Math.floor((max.getTime() - start.getTime()) / 86_400_000) + 1

  return { start: toISODate(start), end: toISODate(max), days, clampedToDataset: clamped }
}

export function DashboardControlsProvider({ children }: { children: ReactNode }) {
  const { uploadMeta } = useSession()
  const [range, setRangeState] = useState<RangeKey>('all')
  const [compare, setCompareState] = useState<CompareKey>('prior_period')
  const [refreshToken, setRefreshToken] = useState(0)
  const [refreshing, setRefreshing] = useState(false)

  // Restore the operator's last selection for the tab.
  useEffect(() => {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEY)
      if (!raw) return
      const parsed = JSON.parse(raw) as { range?: unknown; compare?: unknown }
      if (isRangeKey(parsed.range)) setRangeState(parsed.range)
      if (isCompareKey(parsed.compare)) setCompareState(parsed.compare)
    } catch { /* corrupt entry — fall back to defaults */ }
  }, [])

  const persist = useCallback((next: { range: RangeKey; compare: CompareKey }) => {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next))
    } catch { /* private mode / quota — selection still applies for this view */ }
  }, [])

  const setRange = useCallback((key: RangeKey) => {
    setRangeState(key)
    setCompareState(current => { persist({ range: key, compare: current }); return current })
  }, [persist])

  const setCompare = useCallback((key: CompareKey) => {
    setCompareState(key)
    setRangeState(current => { persist({ range: current, compare: key }); return current })
  }, [persist])

  const refresh = useCallback(() => {
    setRefreshing(true)
    clearKernCache()
    setRefreshToken(t => t + 1)
    // The spinner is a UI affordance only; each page owns its own load state.
    window.setTimeout(() => setRefreshing(false), 600)
  }, [])

  const datasetRange = uploadMeta?.date_range ?? null
  const resolved = useMemo(() => resolveRange(range, datasetRange), [range, datasetRange])

  const value = useMemo<DashboardControlsValue>(() => ({
    range, setRange, compare, setCompare, resolved, datasetRange, refreshToken, refresh, refreshing,
  }), [range, setRange, compare, setCompare, resolved, datasetRange, refreshToken, refresh, refreshing])

  return (
    <DashboardControlsContext.Provider value={value}>
      {children}
    </DashboardControlsContext.Provider>
  )
}

export function useDashboardControls(): DashboardControlsValue {
  const ctx = useContext(DashboardControlsContext)
  if (!ctx) throw new Error('useDashboardControls must be used within DashboardControlsProvider')
  return ctx
}

/** Null-safe variant for shared code that also runs outside /dashboard. */
export function useOptionalDashboardControls(): DashboardControlsValue | null {
  return useContext(DashboardControlsContext)
}
