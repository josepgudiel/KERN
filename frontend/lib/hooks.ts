import { useState, useEffect, useCallback } from 'react'
import { getCached, setCache } from '@/lib/cache'
import { useOptionalDashboardControls } from '@/context/DashboardControlsContext'

// Cache helpers live in lib/cache; re-exported here so existing imports keep working.
export { getCached, setCache, clearKernCache } from '@/lib/cache'

// ── Page data hook with optional cache key ────────────────────────────────
export function usePageData<T>(fetchFn: () => Promise<T>, cacheKey?: string) {
  const [data, setData]       = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState<string | null>(null)
  const [slow, setSlow]       = useState(false)

  // Null outside /dashboard (e.g. the landing page), so the hook stays usable there.
  const controls = useOptionalDashboardControls()
  const refreshToken = controls?.refreshToken ?? 0

  const load = useCallback(async () => {
    // Check cache first
    if (cacheKey) {
      const cached = getCached<T>(cacheKey)
      if (cached) {
        setData(cached)
        setLoading(false)
        return
      }
    }

    setLoading(true)
    setError(null)
    setSlow(false)

    const timeout = setTimeout(() => setSlow(true), 8000)

    try {
      const result = await fetchFn()
      setData(result)
      if (cacheKey) setCache(cacheKey, result)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'An unexpected error occurred.'
      if (msg.includes('500') || msg.includes('Internal')) {
        setError('The analysis ran into an issue. Check the backend terminal for details.')
      } else if (msg.includes('Failed to fetch') || msg.includes('NetworkError') || msg.includes('ERR_')) {
        setError("Couldn't reach the server. Make sure the backend is running at localhost:8000.")
      } else {
        setError(msg)
      }
    } finally {
      setLoading(false)
      clearTimeout(timeout)
    }
    // refreshToken participates so the toolbar's Refresh re-runs every mounted page.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [fetchFn, cacheKey, refreshToken])

  useEffect(() => { load() }, [load])

  return { data, loading, error, slow, retry: load }
}
