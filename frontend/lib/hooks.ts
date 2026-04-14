import { useState, useEffect, useCallback } from 'react'

// ── Session cache (5-minute TTL) ──────────────────────────────────────────
const CACHE_TTL = 5 * 60 * 1000 // 5 minutes

export function getCached<T>(key: string): T | null {
  try {
    const raw = sessionStorage.getItem(key)
    if (!raw) return null
    const { data, timestamp } = JSON.parse(raw)
    if (Date.now() - timestamp > CACHE_TTL) {
      sessionStorage.removeItem(key)
      return null
    }
    return data as T
  } catch {
    return null
  }
}

export function setCache(key: string, data: unknown): void {
  try {
    sessionStorage.setItem(key, JSON.stringify({ data, timestamp: Date.now() }))
  } catch { /* quota exceeded — ignore */ }
}

export function clearKernCache(): void {
  const keys = Object.keys(sessionStorage)
  for (const key of keys) {
    if (key.startsWith('kern_cache_')) {
      sessionStorage.removeItem(key)
    }
  }
}

// ── Page data hook with optional cache key ────────────────────────────────
export function usePageData<T>(fetchFn: () => Promise<T>, cacheKey?: string) {
  const [data, setData]       = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError]     = useState<string | null>(null)
  const [slow, setSlow]       = useState(false)

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
  }, [fetchFn, cacheKey])

  useEffect(() => { load() }, [load])

  return { data, loading, error, slow, retry: load }
}
