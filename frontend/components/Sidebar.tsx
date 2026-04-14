'use client'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { useSession } from '@/context/SessionContext'

const NAV = [
  { href: '/dashboard/action-center', label: 'Action Center',    sub: 'Top priorities' },
  { href: '/dashboard/whats-selling', label: "What's Selling",   sub: 'Products & groups' },
  { href: '/dashboard/pricing',       label: 'Pricing Check',    sub: 'Price check' },
  { href: '/dashboard/overview',      label: 'Summary',          sub: 'Performance snapshot' },
  { href: '/dashboard/when-to-staff', label: 'When to Staff',    sub: 'Day-of-week patterns' },
  { href: '/dashboard/forecast',      label: 'What to Expect',   sub: 'Revenue outlook' },
  { href: '/dashboard/report',        label: 'Report',           sub: 'Monthly summary' },
  { href: '/dashboard/ai-advisor',    label: 'Business Advisor', sub: 'Ask about your data' },
]

interface SidebarProps {
  isOpen?: boolean
  onClose?: () => void
}

export default function Sidebar({ isOpen = false, onClose }: SidebarProps) {
  const pathname = usePathname()
  const router   = useRouter()
  const { uploadMeta, clearSession, daysStale } = useSession()

  return (
    <aside
      className={`sidebar ${isOpen ? 'sidebar--open' : ''}`}
      style={{
        width: 'var(--sidebar-width)',
        minHeight: '100vh',
        flexShrink: 0,
        display: 'flex',
        flexDirection: 'column',
        backgroundColor: 'var(--bg-card)',
        borderRight: '1px solid var(--border)',
      }}
    >

      {/* Brand — KERN N mark + wordmark */}
      <div style={{
        padding: '28px 20px 22px',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
      }}>
        {/* N Mark SVG */}
        <svg width="36" height="36" viewBox="0 0 100 100" fill="none" style={{ flexShrink: 0 }}>
          {/* Main N body — filled, rounded terminals */}
          <path
            d="M14 88 L14 14 Q14 10 18 10 L26 10 Q30 10 32 14 L60 62 L60 14 Q60 10 64 10 L72 10 Q76 10 76 14 L76 88 Q76 92 72 92 L64 92 Q60 92 58 88 L30 40 L30 88 Q30 92 26 92 L18 92 Q14 92 14 88 Z"
            fill="#f0f1f6"
          />
          {/* Right diagonal accent — sky blue overlay */}
          <path
            d="M60 62 L86 14 Q88 10 84 10 L76 10 Q72 10 70 14 L60 32 Z"
            fill="#b3e5fe"
            opacity="0.85"
          />
        </svg>

        {/* Wordmark */}
        <div>
          <span style={{
            fontFamily: 'var(--font-display)',
            fontWeight: 800,
            fontSize: '18px',
            letterSpacing: '0.22em',
            color: 'var(--t1)',
            textTransform: 'uppercase',
            display: 'block',
            lineHeight: 1,
          }}>
            KERN
          </span>
          <span style={{
            fontFamily: 'var(--font-body)',
            fontSize: '8px',
            letterSpacing: '0.26em',
            color: 'var(--sky)',
            opacity: 0.75,
            textTransform: 'uppercase',
            fontWeight: 500,
            display: 'block',
            marginTop: '3px',
          }}>
            by Analytic
          </span>
        </div>
      </div>

      {/* Dataset info */}
      {uploadMeta && (
        <div style={{
          padding: '14px 20px',
          borderBottom: '1px solid var(--border)',
        }}>
          <div style={{
            fontFamily: 'var(--font-display)',
            fontSize: '0.60rem',
            fontWeight: 800,
            textTransform: 'uppercase',
            letterSpacing: '0.16em',
            color: 'var(--t3)',
            marginBottom: '8px',
          }}>
            Active Dataset
          </div>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontWeight: 500,
            fontSize: '0.72rem',
            color: 'var(--t1)',
            marginBottom: '3px',
          }}>
            {uploadMeta.rows.toLocaleString()} rows &middot; {uploadMeta.products.length} products
          </div>
          {uploadMeta.date_range && (
            <div style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.60rem',
              color: 'var(--t3)',
              letterSpacing: '0.02em',
            }}>
              {uploadMeta.date_range.min} → {uploadMeta.date_range.max}
            </div>
          )}
          {uploadMeta.filename?.toLowerCase().match(/demo|sample/) && (
            <span style={{
              display: 'inline-block',
              marginTop: '8px',
              padding: '3px 8px',
              backgroundColor: 'var(--sky-10)',
              border: '1px solid var(--sky-20)',
              borderRadius: '4px',
              fontFamily: 'var(--font-mono)',
              fontWeight: 500,
              fontSize: '0.52rem',
              letterSpacing: '0.12em',
              textTransform: 'uppercase',
              color: 'var(--sky)',
            }}>
              Demo
            </span>
          )}
        </div>
      )}

      {/* Stale data warning */}
      {daysStale !== null && daysStale > 60 && (
        <div style={{
          margin: '10px 12px 0',
          padding: '10px 12px',
          backgroundColor: 'var(--warning-dim)',
          border: '1px solid rgba(251,191,36,0.20)',
          borderLeft: '3px solid var(--amber)',
          borderRadius: 'var(--radius-card)',
        }}>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontSize: '0.56rem',
            fontWeight: 500,
            letterSpacing: '0.10em',
            textTransform: 'uppercase',
            color: 'var(--amber)',
            marginBottom: '3px',
          }}>
            Stale Data
          </div>
          <div style={{
            fontFamily: 'var(--font-body)',
            fontSize: '0.68rem',
            color: 'var(--t2)',
          }}>
            Most recent data is {daysStale} days old
          </div>
        </div>
      )}

      {/* Nav */}
      <nav style={{ flex: 1, padding: '12px 8px', display: 'flex', flexDirection: 'column', gap: '1px' }}>
        {NAV.map((item) => {
          const active = pathname === item.href
          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onClose}
              style={{
                display: 'flex',
                flexDirection: 'column',
                padding: '9px 12px',
                borderRadius: 'var(--radius-card)',
                textDecoration: 'none',
                backgroundColor: active ? 'var(--sky-10)' : 'transparent',
                borderLeft: active ? '2px solid var(--sky)' : '2px solid transparent',
                paddingLeft: '12px',
                transition: 'background-color 0.15s ease',
              }}
              onMouseEnter={(e) => {
                if (!active) e.currentTarget.style.backgroundColor = 'var(--sky-06)'
              }}
              onMouseLeave={(e) => {
                if (!active) e.currentTarget.style.backgroundColor = 'transparent'
              }}
            >
              <div style={{
                fontFamily: 'var(--font-body)',
                fontWeight: active ? 600 : 400,
                fontSize: '0.80rem',
                color: active ? 'var(--sky)' : 'var(--t2)',
                letterSpacing: '0.01em',
                lineHeight: 1.3,
              }}>
                {item.label}
              </div>
              <div style={{
                fontFamily: 'var(--font-body)',
                fontSize: '0.62rem',
                color: active ? 'var(--sky)' : 'var(--t3)',
                marginTop: '1px',
                opacity: active ? 0.6 : 0.6,
              }}>
                {item.sub}
              </div>
            </Link>
          )
        })}
      </nav>

      {/* Bottom */}
      <div style={{
        padding: '14px 12px 20px',
        borderTop: '1px solid var(--border)',
      }}>
        <button
          onClick={() => { onClose?.(); clearSession(); router.push('/') }}
          style={{
            width: '100%',
            padding: '9px 14px',
            backgroundColor: 'transparent',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius)',
            fontFamily: 'var(--font-body)',
            fontWeight: 500,
            fontSize: '0.62rem',
            letterSpacing: '0.10em',
            textTransform: 'uppercase',
            color: 'var(--t3)',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = 'var(--border2)'
            e.currentTarget.style.color = 'var(--t2)'
            e.currentTarget.style.backgroundColor = 'var(--sky-06)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'var(--border)'
            e.currentTarget.style.color = 'var(--t3)'
            e.currentTarget.style.backgroundColor = 'transparent'
          }}
        >
          ↑ Upload New File
        </button>
      </div>
    </aside>
  )
}
