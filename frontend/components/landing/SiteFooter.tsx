'use client'

/* One product, so one row of short columns — no mega-menu, no invented
   sitemap. Every link resolves to something that exists on this page or in the
   app; the Legal column states the facts a visitor actually needs about their
   file rather than linking to policy pages that have not been written. */

const COLUMNS: { heading: string; items: { label: string; href?: string; note?: string }[] }[] = [
  {
    heading: 'Product',
    items: [
      { label: 'How Kern works', href: '#how-it-works' },
      { label: 'What you get back', href: '#features' },
      { label: 'See it in action', href: '#demo' },
      { label: 'Upload your export', href: '#start' },
    ],
  },
  {
    heading: 'Company',
    items: [
      { label: 'Built for small operators', note: 'Food service, retail, services, anything with a POS' },
      { label: 'Independent and self-serve', note: 'No sales call in the loop' },
      { label: 'One file, one session', note: 'Upload again whenever the numbers move' },
    ],
  },
  {
    heading: 'Legal',
    items: [
      { label: 'Your file stays in your session', note: 'Processed for the session, never resold' },
      { label: 'Works without an account', note: 'Sign-up is not part of the flow' },
      { label: 'Photography', note: 'Unsplash License' },
    ],
  },
]

export default function SiteFooter() {
  return (
    <footer style={{ backgroundColor: 'var(--lp-shell)', borderTop: '1px solid var(--lp-line)' }}>
      <div className="lp-wrap" style={{ paddingTop: '56px', paddingBottom: '40px' }}>
        <div
          className="lp-footer-grid"
          style={{
            display: 'grid',
            gridTemplateColumns: 'minmax(0, 1.2fr) repeat(3, minmax(0, 1fr))',
            gap: '48px',
            alignItems: 'start',
            paddingBottom: '40px',
          }}
        >
          <div>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '14px' }}>
              <span
                style={{
                  fontFamily: 'var(--font-heading)',
                  fontSize: '1.12rem',
                  fontWeight: 700,
                  letterSpacing: '-0.01em',
                  color: 'var(--lp-ink)',
                }}
              >
                Kern
              </span>
            </div>
            <p style={{ margin: 0, maxWidth: '30ch', fontSize: '0.88rem' }}>
              Sales intelligence for independent operators. Upload the export
              your register already makes.
            </p>
          </div>

          {COLUMNS.map(col => (
            <div key={col.heading}>
              <div className="lp-label" style={{ marginBottom: '16px' }}>
                {col.heading}
              </div>
              <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
                {col.items.map(item => (
                  <li key={item.label} style={{ marginBottom: '14px' }}>
                    {item.href ? (
                      <a
                        href={item.href}
                        className="lp-footlink"
                        style={{
                          fontFamily: 'var(--font-body)',
                          fontSize: '0.88rem',
                          color: 'var(--lp-ink)',
                          textDecoration: 'none',
                        }}
                      >
                        {item.label}
                      </a>
                    ) : (
                      <>
                        <span
                          style={{
                            display: 'block',
                            fontFamily: 'var(--font-body)',
                            fontSize: '0.88rem',
                            color: 'var(--lp-ink)',
                          }}
                        >
                          {item.label}
                        </span>
                        {item.note && (
                          <span
                            style={{
                              display: 'block',
                              marginTop: '3px',
                              fontFamily: 'var(--font-body)',
                              fontSize: '0.79rem',
                              lineHeight: 1.5,
                              color: 'var(--lp-ink-3)',
                            }}
                          >
                            {item.note}
                          </span>
                        )}
                      </>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div
          className="lp-footer"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '20px',
            paddingTop: '24px',
            borderTop: '1px solid var(--lp-line-2)',
          }}
        >
          <span style={{ fontFamily: 'var(--font-body)', fontSize: '0.82rem', color: 'var(--lp-ink-3)' }}>
            Kern
          </span>
          <a href="#start" className="lp-link">
            Upload sales export
          </a>
        </div>
      </div>
    </footer>
  )
}
