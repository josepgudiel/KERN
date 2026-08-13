'use client'
import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { AlertTriangle, X } from 'lucide-react'
import { useSession } from '@/context/SessionContext'
import { DashboardControlsProvider } from '@/context/DashboardControlsContext'
import Sidebar from '@/components/Sidebar'
import MobileNav from '@/components/MobileNav'
import DashboardToolbar from '@/components/DashboardToolbar'
import { tone } from '@/components/ui'

/** Pages driven by a period of sales data — these get the control bar.
 *  The advisor (chat) and report (one-shot generation) do not. */
const TOOLBAR_EXCLUDED = ['/dashboard/ai-advisor', '/dashboard/report']

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
  const showToolbar = !TOOLBAR_EXCLUDED.includes(pathname)

  return (
    <DashboardControlsProvider>
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
            backgroundColor: 'rgba(28,26,23,0.42)',
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
              fontFamily: 'var(--font-heading)',
              fontSize: '0.7rem',
              fontWeight: pathname === item.href ? 600 : 500,
              letterSpacing: '-0.002em',
              color: pathname === item.href ? 'var(--accent)' : 'var(--t2)',
            }}
          >
            <div style={{
              width: '4px',
              height: '4px',
              borderRadius: '50%',
              backgroundColor: pathname === item.href ? 'var(--accent)' : 'transparent',
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
            fontFamily: 'var(--font-heading)',
            fontSize: '0.7rem',
            fontWeight: (isMoreActive || drawerOpen) ? 600 : 500,
            letterSpacing: '-0.002em',
            color: (isMoreActive || drawerOpen) ? 'var(--accent)' : 'var(--t2)',
          }}
        >
          <div style={{
            width: '4px',
            height: '4px',
            borderRadius: '50%',
            backgroundColor: (isMoreActive || drawerOpen) ? 'var(--accent)' : 'transparent',
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
            backgroundColor: 'rgba(28,26,23,0.38)',
          }}
        />
      )}

      {/* More drawer — mobile only, revealed by the media query in globals.css
          alongside the bottom nav it belongs to. It parks itself off-screen with
          translateY(100%), but `bottom` lifts it 57px first, so ~57px of the
          panel still sat inside a desktop viewport. On the old navy surface that
          strip was the same colour as the page and nobody saw it; on white it
          reads as a stray card pinned to the bottom of every screen. */}
      <div
        className={`more-drawer${drawerOpen ? ' more-drawer--open' : ''}`}
        style={{
          display: 'none',
          position: 'fixed',
          bottom: 'calc(57px + env(safe-area-inset-bottom, 0px))',
          left: 0,
          right: 0,
          zIndex: 50,
          backgroundColor: 'var(--bg-card)',
          borderTop: '1px solid var(--border)',
          borderRadius: '16px 16px 0 0',
          padding: '8px 0',
          /* Closing has to clear the panel's own height *and* the 57px it is
             lifted off the bottom, or it parks with a strip still showing —
             which on mobile lands exactly on top of the bottom nav and covers
             the first tab. translateY(100%) alone only accounts for the height. */
          transform: drawerOpen
            ? 'translateY(0)'
            : 'translateY(calc(100% + 57px + env(safe-area-inset-bottom, 0px)))',
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
              color: pathname === item.href ? 'var(--accent)' : 'var(--t1)',
              textAlign: 'left',
            }}
          >
            {item.label}
            {pathname === item.href && (
              <div style={{
                width: '6px',
                height: '6px',
                borderRadius: '50%',
                backgroundColor: 'var(--accent)',
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
        padding: '32px 40px',
      }}>
        <div style={{ maxWidth: '1440px', margin: '0 auto', width: '100%' }}>
          {showWarning && (
            <div style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: '12px',
              backgroundColor: 'var(--warning-dim)',
              border: `1px solid ${tone('warning').edge}`,
              borderRadius: 'var(--radius-card)',
              padding: '13px 16px',
              marginBottom: '20px',
            }}>
              <AlertTriangle
                size={16}
                strokeWidth={1.75}
                style={{ color: 'var(--amber)', flexShrink: 0, marginTop: '2px' }}
                aria-hidden
              />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{
                  fontFamily: 'var(--font-heading)',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  color: 'var(--amber)',
                  marginBottom: '2px',
                }}>
                  Check your data
                </div>
                <p style={{ fontFamily: 'var(--font-body)', fontSize: '0.80rem', color: 'var(--t2)', lineHeight: 1.55, margin: 0 }}>
                  {warning}
                </p>
              </div>
              <button
                onClick={() => setWarningDismissed(true)}
                style={{
                  flexShrink: 0,
                  display: 'inline-flex',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  color: 'var(--t2)',
                  lineHeight: 1,
                  padding: '2px',
                }}
                aria-label="Dismiss data notice"
              >
                <X size={15} strokeWidth={1.75} aria-hidden />
              </button>
            </div>
          )}
          {showToolbar && <DashboardToolbar />}
          {children}
        </div>
      </main>
    </div>
    </DashboardControlsProvider>
  )
}
