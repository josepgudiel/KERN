'use client'

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '50vh', padding: '2rem' }}>
      <h2 style={{ marginBottom: '0.75rem' }}>Dashboard error</h2>
      <p style={{ color: 'var(--t2)', marginBottom: '1.5rem', textAlign: 'center', maxWidth: '46ch' }}>
        {error.message || 'Failed to load dashboard data.'}
      </p>
      <button onClick={() => reset()} className="btn-primary">
        Try again
      </button>
    </div>
  )
}
