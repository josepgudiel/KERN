'use client'
import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useSession } from '@/context/SessionContext'
import Sidebar from '@/components/Sidebar'
import MobileNav from '@/components/MobileNav'

const NAV_MAIN = [
  { href: '/dashboard/action-center', label: 'Actions' },
  { href: '/dashboard/whats-selling', label: 'Selling' },
  { href: '/dashboard/forecast',      label: 'Expect' },
  { href: '/dashboard/ai-advisor',    label: 'Advisor' },
]

const NAV_MORE = [
  { href: '/dashboard/report',        label: 'Report' },
  { href: '/dashboard/pricing',       label: 'Pricing Check' },
  { href: '/dashboard/overview',      label: 'Summary' },
  { href: '/dashboard/when-to-staff', label: 'When to Staff' },
]

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { sessionId, uploadMeta } = useSession()
  const router = useRouter()
  const pathname = usePathname()
  const [warningDismissed, setWarningDismissed] = useState(false)
  const [drawerOpen, setDrawerOpen] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)

  useEffect(() => {
    if (!sessionId) router.replace('/')
  }, [sessionId, router])

  // Reset dismissal when a new file is uploaded
  useEffect(() => {
    setWarningDismissed(false)
  }, [uploadMeta?.session_id])

  // Close drawer and sidebar on route change
  useEffect(() => {
    setDrawerOpen(false)
    setSidebarOpen(false)
  }, [pathname])

  if (!sessionId) return null

  const warning = uploadMeta?.warning
  const showWarning = !!warning && !warningDismissed

  const isMoreActive = NAV_MORE.some(item => pathname === item.href)

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: 'var(--bg)' }}>
      {/* Mobile top nav with hamburger */}
      <MobileNav
        isSidebarOpen={sidebarOpen}
        onToggleSidebar={() => setSidebarOpen(v => !v)}
      />

      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Overlay when sidebar is open on mobile */}
      {sidebarOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setSidebarOpen(false)}
          style={{
            display: 'none', // shown via CSS on mobile
            position: 'fixed',
            inset: 0,
            zIndex: 44,
            backgroundColor: 'rgba(0,0,0,0.55)',
            transition: 'opacity 0.25s ease',
          }}
        />
      )}

      {/* Mobile bottom nav — hidden on desktop via CSS */}
      <nav style={{
        display: 'none',
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 50,
        backgroundColor: 'var(--bg-card)',
        borderTop: '1px solid var(--border)',
        padding: '8px 0 env(safe-area-inset-bottom, 8px)',
      }} className="mobile-bottom-nav">
        {NAV_MAIN.map((item) => (
          <button
            key={item.href}
            onClick={() => router.push(item.href)}
            style={{
              flex: 1,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '3px',
              padding: '10px 4px',
              minHeight: '48px',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.56rem',
              fontWeight: pathname === item.href ? 500 : 400,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: pathname === item.href ? 'var(--sky)' : 'var(--t3)',
            }}
          >
            <div style={{
              width: '4px',
              height: '4px',
              borderRadius: '50%',
              backgroundColor: pathname === item.href ? 'var(--sky)' : 'transparent',
              marginBottom: '2px',
            }} />
            {item.label}
          </button>
        ))}

        {/* More button */}
        <button
          onClick={() => setDrawerOpen(v => !v)}
          style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '3px',
            padding: '10px 4px',
            minHeight: '48px',
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.56rem',
            fontWeight: (isMoreActive || drawerOpen) ? 500 : 400,
            letterSpacing: '0.08em',
            textTransform: 'uppercase',
            color: (isMoreActive || drawerOpen) ? 'var(--sky)' : 'var(--t3)',
          }}
        >
          <div style={{
            width: '4px',
            height: '4px',
            borderRadius: '50%',
            backgroundColor: (isMoreActive || drawerOpen) ? 'var(--sky)' : 'transparent',
            marginBottom: '2px',
          }} />
          More
        </button>
      </nav>

      {/* More drawer overlay */}
      {drawerOpen && (
        <div
          className="more-drawer-overlay"
          onClick={() => setDrawerOpen(false)}
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 49,
            backgroundColor: 'rgba(0,0,0,0.5)',
          }}
        />
      )}

      {/* More drawer */}
      <div
        className={`more-drawer${drawerOpen ? ' more-drawer--open' : ''}`}
        style={{
          position: 'fixed',
          bottom: 'calc(57px + env(safe-area-inset-bottom, 0px))',
          left: 0,
          right: 0,
          zIndex: 50,
          backgroundColor: 'var(--bg-card)',
          borderTop: '1px solid var(--border)',
          borderRadius: '16px 16px 0 0',
          padding: '8px 0',
          transform: drawerOpen ? 'translateY(0)' : 'translateY(100%)',
          transition: 'transform 0.25s ease',
        }}
      >
        {NAV_MORE.map((item) => (
          <button
            key={item.href}
            onClick={() => { router.push(item.href); setDrawerOpen(false); }}
            style={{
              display: 'flex',
              alignItems: 'center',
              width: '100%',
              padding: '16px 24px',
              minHeight: '52px',
              background: 'none',
              border: 'none',
              borderBottom: '1px solid var(--border)',
              cursor: 'pointer',
              fontFamily: 'var(--font-body)',
              fontSize: '0.92rem',
              fontWeight: pathname === item.href ? 600 : 400,
              color: pathname === item.href ? 'var(--sky)' : 'var(--t1)',
              textAlign: 'left',
            }}
          >
            {item.label}
            {pathname === item.href && (
              <div style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                backgroundColor: 'var(--sky)',
                marginLeft: 'auto',
              }} />
            )}
          </button>
        ))}
      </div>

      <main style={{
        flex: 1,
        minWidth: 0,
        overflowY: 'auto',
        padding: '44px 48px',
      }}>
        <div style={{ maxWidth: '1100px', margin: '0 auto', width: '100%' }}>
          {showWarning && (
            <div style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px',
              backgroundColor: '#fffbeb',
              border: '1px solid #fde68a',
              borderLeft: '4px solid #d97706',
              borderRadius: 'var(--radius-card)',
              padding: '14px 18px',
              marginBottom: '28px',
            }}>
              <span style={{ fontSize: '1rem', flexShrink: 0, marginTop: '1px' }}>⚠️</span>
              <div style={{ flex: 1 }}>
                <div style={{ fontFamily: 'Raleway', fontWeight: 700, fontSize: '0.78rem', color: '#92400e', marginBottom: '2px' }}>
                  Data notice
                </div>
                <p style={{ fontFamily: 'Raleway', fontSize: '0.80rem', color: '#92400e', lineHeight: 1.55, margin: 0 }}>
                  {warning}
                </p>
              </div>
              <button
                onClick={() => setWarningDismissed(true)}
                style={{
                  flexShrink: 0,
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: '#92400e',
                  fontSize: '1rem',
                  lineHeight: 1,
                  padding: '2px 4px',
                  opacity: 0.6,
                }}
                aria-label="Dismiss"
              >
                ×
              </button>
            </div>
          )}
          {children}
        </div>
      </main>
    </div>
  )
}
