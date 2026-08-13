'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useSession } from '@/context/SessionContext'
import { uploadFile } from '@/lib/api'
import type { UploadResponse } from '@/types'
import LandingNav from '@/components/landing/LandingNav'
import Hero from '@/components/landing/Hero'
import HowKernWorks from '@/components/landing/HowKernWorks'
import CompatibilityStrip from '@/components/landing/CompatibilityStrip'
import FeatureShowcase from '@/components/landing/FeatureShowcase'
import AudienceSplit from '@/components/landing/AudienceSplit'
import SeeItInAction from '@/components/landing/SeeItInAction'
import FinalCTA from '@/components/landing/FinalCTA'
import SiteFooter from '@/components/landing/SiteFooter'

export default function LandingPage() {
  const router = useRouter()
  const { setSessionId, setUploadMeta } = useSession()
  const [demoLoading, setDemoLoading] = useState<string | null>(null)
  const [demoError, setDemoError] = useState<string | null>(null)

  function handleUploadSuccess(meta: UploadResponse) {
    setSessionId(meta.session_id)
    setUploadMeta(meta)
    router.push('/dashboard/action-center')
  }

  async function handleDemo(dataset: 'coffee_shop' | 'retail') {
    setDemoLoading(dataset)
    setDemoError(null)
    try {
      const res = await fetch(`/api/demo-data/${dataset}`)
      if (!res.ok) throw new Error(`Demo request failed (${res.status})`)
      const blob = await res.blob()
      const filename = dataset === 'retail' ? 'demo_retail_store.csv' : 'demo_coffee_shop.csv'
      const file = new File([blob], filename, { type: 'text/csv' })
      const meta = await uploadFile(file)
      setSessionId(meta.session_id)
      setUploadMeta(meta)
      router.push('/dashboard/action-center')
    } catch (e) {
      console.error('[landing] demo load failed', e)
      setDemoError("Couldn't load the demo dataset. Make sure the backend is running, then try again.")
    } finally {
      setDemoLoading(null)
    }
  }

  return (
    <div className="landing-page" style={{ backgroundColor: 'var(--bg)', minHeight: '100vh' }}>
      {/* Scroll reveals ship hidden and are released by useReveal() as each
          section enters the viewport, so with scripting off nothing would ever
          release them. This cancels the hidden state outright.

          It is inert today: SessionProvider returns null until its hydration
          effect runs (context/SessionContext.tsx), so the page renders nothing
          without JS regardless. The rule stays because it costs one line and
          it is the difference between "degrades" and "blank" the moment that
          guard is lifted — motion should never be what a page depends on. */}
      <noscript>
        <style>{`.lp-reveal, .lp-reveal-group > * { opacity: 1 !important; transform: none !important; }`}</style>
      </noscript>

      <LandingNav onDemo={() => handleDemo('coffee_shop')} demoLoading={!!demoLoading} />

      {/* Raised out of the hero's stacking context: the hero is pulled up under
          the nav, so a banner left flat in normal flow would be painted over by
          the photograph the moment it appeared. */}
      {demoError && (
        <div
          role="alert"
          className="lp-wrap"
          style={{ position: 'relative', zIndex: 40, paddingTop: '14px' }}
        >
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '14px',
            flexWrap: 'wrap',
            padding: '12px 16px',
            backgroundColor: 'var(--negative-dim)',
            borderLeft: '3px solid var(--red)',
            borderRadius: '6px',
            boxShadow: 'var(--shadow-md)',
          }}>
            <span style={{ fontFamily: 'var(--font-body)', fontSize: '0.88rem', color: 'var(--lp-ink)' }}>
              {demoError}
            </span>
            <button
              onClick={() => setDemoError(null)}
              className="lp-link"
              style={{ borderBottomColor: 'transparent' }}
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {/* Section order is deliberate: photograph → mechanism → compatibility →
          capability → audience → proof → conversion. The page only asks for
          the file once it has shown what comes back. */}
      <Hero onDemo={() => handleDemo('coffee_shop')} demoLoading={!!demoLoading} />
      <HowKernWorks />
      <CompatibilityStrip />
      <FeatureShowcase />
      <AudienceSplit />
      <SeeItInAction onDemo={() => handleDemo('coffee_shop')} demoLoading={!!demoLoading} />
      <FinalCTA
        onUploadSuccess={handleUploadSuccess}
        onDemo={handleDemo}
        demoLoading={demoLoading}
      />
      <SiteFooter />
    </div>
  )
}
