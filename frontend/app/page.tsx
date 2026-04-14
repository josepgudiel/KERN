'use client'
import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useSession } from '@/context/SessionContext'
import UploadZone from '@/components/UploadZone'
import { uploadFile } from '@/lib/api'
import type { UploadResponse } from '@/types'

/* ── Static content ── */

const MOCK_RECS = [
  {
    rank: 1,
    category: 'BUNDLING',
    title: 'Bundle "Oat Milk Latte" + "Croissant"',
    action: 'Create a "Morning Ritual" combo at $8.49',
    impact: '+$1,840/mo',
    reason:
      'These items appear together in 38% of transactions but have never been promoted together.',
    confidence: 'HIGH CONFIDENCE',
    transactions: '2,847 transactions analyzed',
  },
  {
    rank: 2,
    category: 'PRICING',
    title: 'Raise price on "Cold Brew 16oz"',
    action: 'Increase from $4.50 to $4.95',
    impact: '+$920/mo',
    reason: 'Price elasticity is low — demand held steady during your last increase.',
    confidence: 'HIGH CONFIDENCE',
    transactions: '1,523 transactions analyzed',
  },
  {
    rank: 3,
    category: 'INVENTORY',
    title: 'Discontinue "Chai Tea Bag" in-store',
    action: 'Move to online-only or replace with Dirty Chai',
    impact: 'Save $340/mo',
    reason: 'Only 12 units sold in 90 days. Shelf space is better used for top sellers.',
    confidence: 'DIRECTIONAL',
    transactions: '12 transactions analyzed',
  },
]

const STEPS = [
  {
    num: '01',
    title: 'Upload your file',
    desc: 'CSV or Excel from any POS system. No formatting required.',
  },
  {
    num: '02',
    title: 'We analyze everything',
    desc: 'Pricing, bundling, forecasting, anomalies, staffing — 8+ analyses run in seconds.',
  },
  {
    num: '03',
    title: 'You get a ranked plan',
    desc: 'Plain-English actions with dollar estimates. Ready to execute today.',
  },
]

const FEATURES = [
  {
    title: 'Ranked Recommendations',
    desc: 'Every action ranked by estimated dollar impact. Biggest wins surface first.',
  },
  {
    title: 'Revenue Forecasting',
    desc: '8-week revenue projections with confidence bands. See where you\'re heading.',
  },
  {
    title: 'AI Business Advisor',
    desc: 'Ask anything about your business in plain English. It knows your actual numbers.',
  },
  {
    title: 'Product Breakdown',
    desc: 'Growth trends, declining products, and bundle and pricing opportunities.',
  },
  {
    title: 'Anomaly Detection',
    desc: 'Automatic spike and dip detection. Know when something unusual happened and why.',
  },
  {
    title: 'Staffing Guide',
    desc: 'Peak days, slow days, and staffing recommendations based on your actual traffic.',
  },
]

const STATS = [
  { value: '< 5s', label: 'Analysis time' },
  { value: '8+', label: 'Analysis modules' },
  { value: '200K', label: 'Rows supported' },
  { value: '100%', label: 'Private & secure' },
]

/* ── Page ── */

export default function LandingPage() {
  const router = useRouter()
  const { setSessionId, setUploadMeta } = useSession()
  const [demoLoading, setDemoLoading] = useState<string | null>(null)

  function handleUploadSuccess(meta: UploadResponse) {
    setSessionId(meta.session_id)
    setUploadMeta(meta)
    router.push('/dashboard/action-center')
  }

  async function handleDemo(dataset: 'coffee_shop' | 'retail') {
    setDemoLoading(dataset)
    try {
      const res = await fetch(`/api/demo-data/${dataset}`)
      if (!res.ok) throw new Error()
      const blob = await res.blob()
      const filename =
        dataset === 'retail' ? 'demo_retail_store.csv' : 'demo_coffee_shop.csv'
      const file = new File([blob], filename, { type: 'text/csv' })
      const meta = await uploadFile(file)
      setSessionId(meta.session_id)
      setUploadMeta(meta)
      router.push('/dashboard/action-center')
    } catch {
      alert('Could not load demo. Make sure the backend is running.')
    } finally {
      setDemoLoading(null)
    }
  }

  return (
    <div style={{ backgroundColor: 'var(--bg-base)', minHeight: '100vh' }}>

      {/* ════════════════════════════════════════════
          NAV
         ════════════════════════════════════════════ */}
      <nav
        className="landing-nav"
        style={{
          padding: '18px 48px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid var(--border)',
          position: 'sticky',
          top: 0,
          backgroundColor: 'rgba(10,10,15,0.88)',
          backdropFilter: 'blur(14px)',
          WebkitBackdropFilter: 'blur(14px)',
          zIndex: 50,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px' }}>
          <span
            className="font-display"
            style={{
              fontSize: '1.35rem',
              fontWeight: 700,
              color: 'var(--text-primary)',
              letterSpacing: '0.14em',
              textTransform: 'uppercase',
            }}
          >
            KERN
          </span>
          <span
            className="label-caps"
            style={{ color: 'var(--text-muted)', fontSize: '0.55rem' }}
          >
            Business Intelligence
          </span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <button
            className="btn-ghost"
            onClick={() => handleDemo('coffee_shop')}
            disabled={!!demoLoading}
          >
            {demoLoading === 'coffee_shop' ? 'Loading...' : 'View Demo'}
          </button>
          <a href="#upload" className="btn-primary">
            Get Started &rarr;
          </a>
        </div>
      </nav>

      {/* ════════════════════════════════════════════
          HERO
         ════════════════════════════════════════════ */}
      <section
        className="landing-hero"
        style={{
          maxWidth: '1320px',
          margin: '0 auto',
          width: '100%',
          padding: '100px 48px 80px',
          display: 'grid',
          gridTemplateColumns: '1fr 440px',
          gap: '80px',
          alignItems: 'center',
        }}
      >
        {/* Left — Copy */}
        <div className="fade-up">
          <div className="section-eyebrow">
            <span className="label-caps" style={{ color: 'var(--accent)' }}>
              Business Intelligence
            </span>
          </div>

          <h1 style={{ marginBottom: '28px' }}>
            Your sales data
            <br />
            <span
              className="gradient-text"
              style={{ fontStyle: 'italic', fontWeight: 600 }}
            >
              already knows
            </span>
            <br />
            what to do next.
          </h1>

          <p
            style={{
              fontSize: '1.05rem',
              lineHeight: 1.8,
              color: 'var(--text-secondary)',
              maxWidth: '480px',
              marginBottom: '40px',
            }}
          >
            Upload your sales file. Get a ranked list of actions &mdash; in under
            10&nbsp;seconds. No account. No setup. Works with any POS system.
          </p>

          <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap' }}>
            <a href="#upload" className="btn-primary" style={{ fontSize: '0.72rem' }}>
              Upload your sales file &mdash; it&apos;s free
            </a>
            <button
              className="btn-ghost"
              onClick={() => handleDemo('coffee_shop')}
              disabled={!!demoLoading}
              style={{ fontSize: '0.72rem' }}
            >
              {demoLoading === 'coffee_shop'
                ? 'Loading...'
                : 'See it with sample data \u2192'}
            </button>
          </div>
        </div>

        {/* Right — Mock recommendation card */}
        <div className="fade-up-delay-2 landing-float" style={{ position: 'relative' }}>
          {/* Primary card */}
          <div
            className="mock-card-glow"
            style={{
              backgroundColor: 'var(--bg-elevated)',
              border: '1px solid var(--border-strong)',
              borderRadius: 'var(--radius-card)',
              overflow: 'hidden',
            }}
          >
            {/* Urgency bar */}
            <div
              style={{
                display: 'flex',
                gap: '0',
              }}
            >
              <div
                style={{
                  width: '4px',
                  flexShrink: 0,
                  backgroundColor: 'var(--accent)',
                }}
              />
              <div style={{ flex: 1, padding: '22px 24px' }}>
                {/* Header */}
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    marginBottom: '14px',
                  }}
                >
                  <span
                    style={{
                      fontFamily: 'var(--font-body)',
                      fontSize: '0.60rem',
                      fontWeight: 500,
                      textTransform: 'uppercase',
                      letterSpacing: '0.12em',
                      color: 'var(--accent)',
                      opacity: 0.8,
                    }}
                  >
                    {MOCK_RECS[0].category}
                  </span>
                  <span
                    style={{
                      display: 'inline-flex',
                      alignItems: 'center',
                      gap: '5px',
                      padding: '3px 8px',
                      borderRadius: 'var(--radius)',
                      backgroundColor: 'var(--positive-dim)',
                      color: 'var(--positive)',
                      fontFamily: 'var(--font-mono)',
                      fontWeight: 700,
                      fontSize: '0.54rem',
                      letterSpacing: '0.10em',
                      textTransform: 'uppercase',
                    }}
                  >
                    <span
                      style={{
                        width: '5px',
                        height: '5px',
                        borderRadius: '50%',
                        backgroundColor: 'var(--positive)',
                      }}
                    />
                    {MOCK_RECS[0].confidence}
                  </span>
                </div>

                {/* Title */}
                <div
                  style={{
                    fontFamily: 'var(--font-display)',
                    fontWeight: 600,
                    fontSize: '0.95rem',
                    color: 'var(--text-primary)',
                    lineHeight: 1.4,
                    marginBottom: '12px',
                  }}
                >
                  {MOCK_RECS[0].title}
                </div>

                {/* Big number */}
                <div
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 700,
                    fontSize: '1.8rem',
                    color: 'var(--accent)',
                    marginBottom: '12px',
                    lineHeight: 1,
                    letterSpacing: '-0.02em',
                  }}
                >
                  {MOCK_RECS[0].impact}
                </div>

                {/* Action */}
                <div
                  style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: '0.82rem',
                    color: 'var(--text-secondary)',
                    lineHeight: 1.65,
                    marginBottom: '14px',
                  }}
                >
                  {MOCK_RECS[0].action}
                </div>

                {/* Divider */}
                <div
                  style={{
                    height: '1px',
                    backgroundColor: 'var(--border)',
                    marginBottom: '12px',
                  }}
                />

                {/* Reason */}
                <div
                  style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: '0.72rem',
                    color: 'var(--text-muted)',
                    lineHeight: 1.55,
                    marginBottom: '6px',
                  }}
                >
                  {MOCK_RECS[0].reason}
                </div>
                <div
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.56rem',
                    color: 'var(--text-muted)',
                    letterSpacing: '0.06em',
                    textTransform: 'uppercase',
                  }}
                >
                  {MOCK_RECS[0].transactions}
                </div>
              </div>
            </div>
          </div>

          {/* Peek cards below */}
          <div
            className="grid-keep-2"
            style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '8px',
              marginTop: '8px',
            }}
          >
            {MOCK_RECS.slice(1).map((r) => (
              <div
                key={r.rank}
                style={{
                  backgroundColor: 'var(--bg-surface)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius-card)',
                  padding: '14px 16px',
                  overflow: 'hidden',
                }}
              >
                <div
                  style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: '0.55rem',
                    fontWeight: 500,
                    textTransform: 'uppercase',
                    letterSpacing: '0.12em',
                    color: r.rank === 2 ? 'var(--accent)' : 'var(--warning)',
                    opacity: 0.7,
                    marginBottom: '6px',
                  }}
                >
                  #{r.rank} &middot; {r.category}
                </div>
                <div
                  style={{
                    fontFamily: 'var(--font-body)',
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    color: 'var(--text-primary)',
                    lineHeight: 1.35,
                    marginBottom: '8px',
                  }}
                >
                  {r.title}
                </div>
                <div
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 700,
                    fontSize: '1rem',
                    color: r.rank === 2 ? 'var(--accent)' : 'var(--warning)',
                    lineHeight: 1,
                    letterSpacing: '-0.02em',
                  }}
                >
                  {r.impact}
                </div>
              </div>
            ))}
          </div>

          {/* "Sample output" label */}
          <div
            style={{
              textAlign: 'center',
              marginTop: '12px',
            }}
          >
            <span
              className="label-caps"
              style={{ fontSize: '0.50rem', color: 'var(--text-muted)' }}
            >
              Sample output from a coffee shop dataset
            </span>
          </div>
        </div>
      </section>

      {/* ════════════════════════════════════════════
          STATS BAR
         ════════════════════════════════════════════ */}
      <div
        className="landing-stats-wrapper"
        style={{
          borderTop: '1px solid var(--border)',
          borderBottom: '1px solid var(--border)',
          backgroundColor: 'var(--bg-surface)',
          padding: '28px 48px',
        }}
      >
        <div
          className="landing-stats-bar"
          style={{
            maxWidth: '1320px',
            margin: '0 auto',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            flexWrap: 'wrap',
            gap: '24px',
          }}
        >
          {STATS.map((s) => (
            <div
              key={s.label}
              style={{ display: 'flex', alignItems: 'baseline', gap: '10px' }}
            >
              <span
                className="number-display"
                style={{ fontSize: '2.2rem', color: 'var(--text-primary)' }}
              >
                {s.value}
              </span>
              <span className="label-caps" style={{ color: 'var(--text-muted)' }}>
                {s.label}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* ════════════════════════════════════════════
          HOW IT WORKS
         ════════════════════════════════════════════ */}
      <section
        className="landing-section"
        style={{
          maxWidth: '1320px',
          margin: '0 auto',
          padding: '100px 48px',
        }}
      >
        <div className="section-eyebrow" style={{ marginBottom: '16px' }}>
          <span className="label-caps" style={{ color: 'var(--accent)' }}>
            How It Works
          </span>
        </div>
        <h2 style={{ marginBottom: '60px', maxWidth: '500px' }}>
          Three steps.
          <br />
          <span className="gradient-text" style={{ fontWeight: 600 }}>
            Ten seconds.
          </span>
        </h2>

        <div
          className="landing-steps"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '48px',
          }}
        >
          {STEPS.map((step, i) => (
            <div key={step.num} className={`fade-up-delay-${i + 1}`}>
              <div className="step-number" style={{ marginBottom: '16px' }}>
                {step.num}
              </div>
              <div
                style={{
                  fontFamily: 'var(--font-display)',
                  fontWeight: 700,
                  fontSize: '1.1rem',
                  color: 'var(--text-primary)',
                  marginBottom: '10px',
                }}
              >
                {step.title}
              </div>
              <p
                style={{
                  fontSize: '0.88rem',
                  color: 'var(--text-secondary)',
                  lineHeight: 1.7,
                  maxWidth: '320px',
                }}
              >
                {step.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Divider */}
      <div
        className="landing-divider"
        style={{
          maxWidth: '1320px',
          margin: '0 auto',
          padding: '0 48px',
        }}
      >
        <div className="divider" />
      </div>

      {/* ════════════════════════════════════════════
          FEATURES
         ════════════════════════════════════════════ */}
      <section
        className="landing-section"
        style={{
          maxWidth: '1320px',
          margin: '0 auto',
          padding: '100px 48px',
        }}
      >
        <div className="section-eyebrow" style={{ marginBottom: '16px' }}>
          <span className="label-caps" style={{ color: 'var(--accent)' }}>
            What You Get
          </span>
        </div>
        <h2 style={{ marginBottom: '60px', maxWidth: '540px' }}>
          Everything a data team would tell you &mdash;{' '}
          <span className="gradient-text" style={{ fontWeight: 600 }}>
            without the data team.
          </span>
        </h2>

        <div
          className="landing-features"
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '16px',
          }}
        >
          {FEATURES.map((f, i) => (
            <div
              key={f.title}
              className={`fade-up-delay-${Math.min(i + 1, 6)}`}
              style={{
                backgroundColor: 'var(--bg-surface)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-card)',
                padding: '28px 24px',
                transition: 'border-color 0.2s ease',
                cursor: 'default',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = 'var(--border-strong)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--border)'
              }}
            >
              <div
                style={{
                  fontFamily: 'var(--font-display)',
                  fontWeight: 700,
                  fontSize: '0.92rem',
                  color: 'var(--text-primary)',
                  marginBottom: '10px',
                }}
              >
                {f.title}
              </div>
              <p
                style={{
                  fontSize: '0.82rem',
                  color: 'var(--text-secondary)',
                  lineHeight: 1.65,
                }}
              >
                {f.desc}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Divider */}
      <div
        className="landing-divider"
        style={{
          maxWidth: '1320px',
          margin: '0 auto',
          padding: '0 48px',
        }}
      >
        <div className="divider" />
      </div>

      {/* ════════════════════════════════════════════
          UPLOAD CTA SECTION
         ════════════════════════════════════════════ */}
      <section
        id="upload"
        className="landing-section"
        style={{
          maxWidth: '1320px',
          margin: '0 auto',
          padding: '100px 48px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <div className="section-eyebrow" style={{ marginBottom: '16px' }}>
          <span className="label-caps" style={{ color: 'var(--accent)' }}>
            Get Started
          </span>
        </div>
        <h2
          style={{
            textAlign: 'center',
            marginBottom: '16px',
          }}
        >
          Ready to see what your data knows?
        </h2>
        <p
          style={{
            textAlign: 'center',
            fontSize: '0.95rem',
            color: 'var(--text-secondary)',
            maxWidth: '460px',
            marginBottom: '48px',
            lineHeight: 1.7,
          }}
        >
          Upload your sales CSV or Excel file. You&apos;ll have ranked recommendations
          in under 10&nbsp;seconds.
        </p>

        <a href="#upload" className="btn-primary" style={{ fontSize: '0.72rem', marginBottom: '32px' }}>
          Upload your sales file &mdash; it&apos;s free
        </a>

        {/* Upload card */}
        <div
          className="landing-upload-card"
          style={{
            width: '100%',
            maxWidth: '520px',
            backgroundColor: 'var(--bg-surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-card)',
            padding: '36px 32px',
            boxShadow: '0 25px 60px rgba(0,0,0,0.4)',
          }}
        >
          <UploadZone onSuccess={handleUploadSuccess} />

          {/* Divider */}
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              margin: '24px 0',
            }}
          >
            <div
              style={{
                flex: 1,
                height: '1px',
                backgroundColor: 'var(--border)',
              }}
            />
            <span
              className="label-caps"
              style={{ color: 'var(--text-muted)', fontSize: '0.55rem' }}
            >
              Or try with sample data
            </span>
            <div
              style={{
                flex: 1,
                height: '1px',
                backgroundColor: 'var(--border)',
              }}
            />
          </div>

          {/* Demo buttons */}
          <div className="grid-keep-2" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
            {[
              { id: 'coffee_shop' as const, label: 'Coffee Shop' },
              { id: 'retail' as const, label: 'Retail Store' },
            ].map((d) => (
              <button
                key={d.id}
                onClick={() => handleDemo(d.id)}
                disabled={!!demoLoading}
                className="btn-ghost"
                style={{
                  justifyContent: 'center',
                  padding: '10px 12px',
                  opacity: demoLoading && demoLoading !== d.id ? 0.5 : 1,
                }}
              >
                {demoLoading === d.id ? 'Loading...' : d.label}
              </button>
            ))}
          </div>

          <p
            className="label-caps"
            style={{
              textAlign: 'center',
              marginTop: '20px',
              fontSize: '0.55rem',
              color: 'var(--text-muted)',
            }}
          >
            No account required &middot; Data stays private &middot; Free to use
          </p>
        </div>
      </section>

      {/* ════════════════════════════════════════════
          FOOTER
         ════════════════════════════════════════════ */}
      <footer
        className="landing-footer"
        style={{
          borderTop: '1px solid var(--border)',
          padding: '20px 48px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <span
          className="label-caps"
          style={{ color: 'var(--text-muted)', fontSize: '0.55rem' }}
        >
          KERN &mdash; Business Intelligence
        </span>
        <a href="#upload" className="btn-primary" style={{ fontSize: '0.55rem', padding: '6px 16px' }}>
          Upload your sales file &mdash; it&apos;s free
        </a>
        <span
          className="label-caps"
          style={{ color: 'var(--text-muted)', fontSize: '0.55rem' }}
        >
          Built for small business owners
        </span>
      </footer>
    </div>
  )
}
