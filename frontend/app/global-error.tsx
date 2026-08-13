'use client'

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <html>
      <body>
        {/* This boundary replaces the root layout, so the stylesheet and the
            font variables are gone by the time it renders — every value here
            has to be a literal. They mirror the palette in globals.css. */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', fontFamily: 'sans-serif', background: '#f7f5f2', color: '#1c1a17' }}>
          <h2 style={{ fontSize: '1.5rem', marginBottom: '1rem' }}>Something went wrong</h2>
          <p style={{ color: '#55504a', marginBottom: '1.5rem' }}>{error.message || 'An unexpected error occurred.'}</p>
          <button
            onClick={() => reset()}
            style={{ padding: '0.6rem 1.5rem', background: '#b4531f', color: '#ffffff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 600 }}
          >
            Try again
          </button>
        </div>
      </body>
    </html>
  )
}
