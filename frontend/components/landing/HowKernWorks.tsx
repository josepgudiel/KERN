'use client'

import { FileUp, Cpu, ListChecks } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useReveal } from './useReveal'

interface Step {
  num: string
  Icon: LucideIcon
  title: string
  claim: string
  detail: string
}

/* Three claims, each of which is a fact about the build rather than a
   statistic about customers Kern does not have yet:
   — columns are matched against candidate lists in engine/data_loader.py, so
     no mapping step is exposed to the user;
   — the analysis pass is local pandas/numpy work over a few thousand rows;
   — every recommendation carries its sample size, window and confidence tier,
     which is the product's actual differentiator. */
const STEPS: Step[] = [
  {
    num: '01',
    Icon: FileUp,
    title: 'Upload',
    claim: 'Any POS export, columns auto-detected',
    detail:
      'Drop in a CSV or XLSX straight from the register. Kern matches your column names against the formats the major POS systems emit, so you skip the mapping screen entirely.',
  },
  {
    num: '02',
    Icon: Cpu,
    title: 'Analyze',
    claim: 'Runs in under 2 seconds',
    detail:
      'One pass covers product clustering, price positioning, momentum, day-of-week patterns and a revenue forecast. It finishes while you wait, and your file stays inside your session the whole time.',
  },
  {
    num: '03',
    Icon: ListChecks,
    title: 'Decide',
    claim: 'Ranked actions, each one explained',
    detail:
      'Every recommendation says in plain English why it is there, with the sample size, date window and confidence behind it. Where the data will not support a call, Kern says so instead of making one.',
  },
]

export default function HowKernWorks() {
  /* The heading block and the three steps are revealed separately: the section
     head arrives first and the sequence follows under it, which is the order a
     reader takes them in anyway. */
  const head = useReveal<HTMLDivElement>()
  const steps = useReveal<HTMLOListElement>()

  return (
    <section id="how-it-works" className="lp-band-shell">
      <div className="lp-wrap" style={{ paddingTop: '76px', paddingBottom: '76px' }}>
        <div
          ref={head.ref}
          className={head.className}
          style={{
            display: 'flex',
            alignItems: 'flex-end',
            justifyContent: 'space-between',
            gap: '40px',
            flexWrap: 'wrap',
            paddingBottom: '28px',
            marginBottom: '44px',
            borderBottom: '1px solid var(--lp-line-2)',
          }}
        >
          <div>
            <span className="lp-eyebrow" style={{ marginBottom: '14px' }}>
              How Kern works
            </span>
            <h2 style={{ maxWidth: '18ch' }}>From export to decision in one pass</h2>
          </div>
          <p style={{ maxWidth: '32ch', fontSize: '0.92rem', margin: 0 }}>
            Three stages, all of them automatic. You go straight from file to
            decisions without a setup step in between or an analyst on the other
            end.
          </p>
        </div>

        {/* Horizontal band. The icon and the step number carry the sequence on
            their own; a rule over each column only added a decorative edge
            three abreast, directly under the section rule above it. */}
        <ol
          ref={steps.ref}
          className={`lp-steps-3 lp-reveal-group ${steps.className}`}
          style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(3, minmax(0, 1fr))',
            gap: '40px',
            listStyle: 'none',
            margin: 0,
            padding: 0,
          }}
        >
          {STEPS.map(({ num, Icon, title, claim, detail }) => (
            <li key={num}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '11px', marginBottom: '16px' }}>
                <Icon size={19} strokeWidth={1.9} style={{ color: 'var(--lp-accent)' }} aria-hidden />
                <span className="lp-label" style={{ color: 'var(--lp-ink-3)' }}>
                  Step {num}
                </span>
              </div>

              <h3 style={{ margin: '0 0 8px', fontSize: '1.24rem' }}>{title}</h3>

              <p
                style={{
                  margin: '0 0 12px',
                  fontFamily: 'var(--font-heading)',
                  fontSize: '0.98rem',
                  fontWeight: 600,
                  lineHeight: 1.45,
                  color: 'var(--lp-ink)',
                }}
              >
                {claim}
              </p>

              <p style={{ margin: 0, fontSize: '0.9rem', lineHeight: 1.65 }}>{detail}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  )
}
