'use client'

import { usePathname } from 'next/navigation'

interface MobileNavProps {
  isSidebarOpen: boolean
  onToggleSidebar: () => void
}

const PAGE_TITLES: Record<string, string> = {
  '/dashboard/upload': 'Upload',
  '/dashboard/action-center': 'Action Center',
  '/dashboard/whats-selling': "What's Selling",
  '/dashboard/when-to-staff': 'When to Staff',
  '/dashboard/forecast': 'What to Expect',
  '/dashboard/overview': 'Summary',
  '/dashboard/pricing': 'Pricing Check',
  '/dashboard/ai-advisor': 'Business Advisor',
  '/dashboard/report': 'Report',
}

export default function MobileNav({ isSidebarOpen, onToggleSidebar }: MobileNavProps) {
  const pathname = usePathname()
  const pageTitle = PAGE_TITLES[pathname] || 'KERN'

  return (
    <nav
      className="mobile-top-nav"
      style={{
        display: 'none',
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        zIndex: 60,
        height: '56px',
        alignItems: 'center',
        padding: '0 16px',
        gap: '12px',
        backgroundColor: 'var(--bg-card)',
        borderBottom: '1px solid var(--border)',
        boxShadow: '0 2px 12px rgba(0,0,0,0.3)',
      }}
    >
      {/* Hamburger / Close button */}
      <button
        onClick={onToggleSidebar}
        aria-label={isSidebarOpen ? 'Close navigation' : 'Open navigation'}
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '40px',
          height: '40px',
          flexShrink: 0,
          background: isSidebarOpen ? 'var(--sky-10)' : 'var(--bg-mid)',
          border: `1px solid ${isSidebarOpen ? 'var(--sky-20)' : 'var(--border)'}`,
          borderRadius: 'var(--radius)',
          cursor: 'pointer',
          color: isSidebarOpen ? 'var(--sky)' : 'var(--t2)',
          transition: 'all 0.15s ease',
        }}
      >
        {isSidebarOpen ? (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
            <path d="M18 6L6 18M6 6l12 12" />
          </svg>
        ) : (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round">
            <path d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        )}
      </button>

      {/* Page title */}
      <div style={{
        flex: 1,
        textAlign: 'center',
        fontFamily: 'var(--font-display)',
        fontWeight: 800,
        fontSize: '0.82rem',
        color: 'var(--t1)',
        letterSpacing: '0.16em',
        textTransform: 'uppercase',
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
      }}>
        {pageTitle}
      </div>

      {/* Spacer for alignment */}
      <div style={{ width: '40px', height: '40px', flexShrink: 0 }} />
    </nav>
  )
}
