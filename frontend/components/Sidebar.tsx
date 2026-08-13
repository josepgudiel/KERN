'use client'
import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { Upload } from 'lucide-react'
import { useSession } from '@/context/SessionContext'
import { tone } from '@/components/ui'

/* One line each, and no two say the same thing. The old set had "Pricing
   Check / Price check" and three separate items describing themselves as a
   summary, which tells a reader nothing about where to click. */
const NAV = [
  { href: '/dashboard/action-center', label: 'Action Center',    sub: "Today's priorities" },
  { href: '/dashboard/whats-selling', label: "What's Selling",   sub: 'Products and groups' },
  { href: '/dashboard/pricing',       label: 'Pricing Check',    sub: 'Under and over-priced items' },
  { href: '/dashboard/overview',      label: 'Summary',          sub: 'Last 30 days at a glance' },
  { href: '/dashboard/when-to-staff', label: 'When to Staff',    sub: 'Busiest days of the week' },
  { href: '/dashboard/forecast',      label: 'What to Expect',   sub: 'Revenue outlook' },
  { href: '/dashboard/report',        label: 'Report',           sub: 'A write-up you can send' },
  { href: '/dashboard/ai-advisor',    label: 'Business Advisor', sub: 'Ask about your numbers' },
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

      {/* Brand — text wordmark, matching the marketing nav. At this size a mark
          beside the name adds a second thing to read and nothing to recognise. */}
      <div style={{
        padding: '24px 20px 20px',
        borderBottom: '1px solid var(--border)',
      }}>
        <span style={{
          fontFamily: 'var(--font-heading)',
          fontWeight: 700,
          fontSize: '1.15rem',
          letterSpacing: '-0.01em',
          color: 'var(--t1)',
          display: 'block',
          lineHeight: 1.1,
        }}>
          Kern
        </span>
        <span style={{
          fontFamily: 'var(--font-heading)',
          fontSize: '0.62rem',
          fontWeight: 600,
          letterSpacing: '0.14em',
          textTransform: 'uppercase',
          color: 'var(--t3)',
          display: 'block',
          marginTop: '4px',
        }}>
          by Analytic
        </span>
      </div>

      {/* Dataset info — the label is words, the figures are figures. */}
      {uploadMeta && (
        <div style={{
          padding: '14px 20px',
          borderBottom: '1px solid var(--border)',
        }}>
          <div className="ui-label" style={{ marginBottom: '7px' }}>
            Active dataset
          </div>
          <div style={{
            fontFamily: 'var(--font-mono)',
            fontWeight: 500,
            fontVariantNumeric: 'tabular-nums',
            fontSize: '0.74rem',
            color: 'var(--t1)',
            marginBottom: '3px',
          }}>
            {uploadMeta.rows.toLocaleString()} rows &middot; {uploadMeta.products.length} products
          </div>
          {uploadMeta.date_range && (
            <div style={{
              fontFamily: 'var(--font-mono)',
              fontVariantNumeric: 'tabular-nums',
              fontSize: '0.64rem',
              color: 'var(--t2)',
            }}>
              {uploadMeta.date_range.min} → {uploadMeta.date_range.max}
            </div>
          )}
          {uploadMeta.filename?.toLowerCase().match(/demo|sample/) && (
            <span style={{
              display: 'inline-block',
              marginTop: '9px',
              padding: '2px 8px',
              backgroundColor: 'var(--accent-dim)',
              border: '1px solid var(--sky-20)',
              borderRadius: '4px',
              fontFamily: 'var(--font-heading)',
              fontWeight: 600,
              fontSize: '0.66rem',
              color: 'var(--accent)',
            }}>
              Demo data
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
          border: `1px solid ${tone('warning').edge}`,
          borderRadius: 'var(--radius-card)',
        }}>
          <div style={{
            fontFamily: 'var(--font-heading)',
            fontSize: '0.72rem',
            fontWeight: 600,
            color: 'var(--amber)',
            marginBottom: '2px',
          }}>
            Ageing data
          </div>
          <div style={{
            fontFamily: 'var(--font-body)',
            fontSize: '0.7rem',
            color: 'var(--t2)',
            lineHeight: 1.45,
          }}>
            The newest sale in this file is {daysStale} days old.
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
                borderRadius: 'var(--radius)',
                textDecoration: 'none',
                /* The active item is a filled row, not a row wearing a rule
                   down its side. One decoration is enough to find it. */
                backgroundColor: active ? 'var(--accent-dim)' : 'transparent',
                transition: 'background-color 0.15s ease',
              }}
              onMouseEnter={(e) => {
                if (!active) e.currentTarget.style.backgroundColor = 'var(--bg-alt)'
              }}
              onMouseLeave={(e) => {
                if (!active) e.currentTarget.style.backgroundColor = 'transparent'
              }}
            >
              <div style={{
                fontFamily: 'var(--font-heading)',
                fontWeight: active ? 600 : 500,
                fontSize: '0.86rem',
                color: active ? 'var(--accent)' : 'var(--t1)',
                letterSpacing: '-0.004em',
                lineHeight: 1.35,
              }}>
                {item.label}
              </div>
              <div style={{
                fontFamily: 'var(--font-body)',
                fontSize: '0.68rem',
                color: active ? 'var(--accent)' : 'var(--t2)',
                opacity: active ? 0.78 : 1,
                marginTop: '1px',
                lineHeight: 1.35,
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
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '7px',
            padding: '9px 14px',
            backgroundColor: 'transparent',
            border: '1px solid var(--border2)',
            borderRadius: '6px',
            fontFamily: 'var(--font-heading)',
            fontWeight: 500,
            fontSize: '0.82rem',
            letterSpacing: '-0.005em',
            color: 'var(--t1)',
            cursor: 'pointer',
            transition: 'border-color 0.15s ease, background-color 0.15s ease',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.borderColor = 'var(--t1)'
            e.currentTarget.style.backgroundColor = 'var(--bg-alt)'
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.borderColor = 'var(--border2)'
            e.currentTarget.style.backgroundColor = 'transparent'
          }}
        >
          <Upload size={14} strokeWidth={1.75} aria-hidden />
          Upload a new file
        </button>
      </div>
    </aside>
  )
}
