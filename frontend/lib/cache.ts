/**
 * Session-scoped response cache (5-minute TTL).
 *
 * Split out from lib/hooks so that context providers can clear the cache
 * without importing the hook module — which would create an import cycle
 * between the hooks and the contexts they read.
 */

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
