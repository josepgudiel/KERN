'use client'

import { useState } from 'react'
import { ArrowRight, Check, ChevronDown, ChevronRight } from 'lucide-react'
import { Recommendation } from '@/types'

/* ─── Urgency badge config ──────────────────────────────────────────────── */

const URGENCY_STYLES: Record<string, { bg: string; color: string; edge: string }> = {
  'Act this week': {
    bg: 'var(--accent-dim)',
    color: 'var(--accent)',
    edge: '#eccdb8',
  },
  'Worth doing soon': {
    bg: 'var(--warning-dim)',
    color: 'var(--amber)',
    edge: '#e6d3a8',
  },
  'Plan for next month': {
    bg: 'var(--bg-alt)',
    color: 'var(--t2)',
    edge: 'var(--border)',
  },
}

function getUrgencyStyle(label: string) {
  return URGENCY_STYLES[label] ?? URGENCY_STYLES['Plan for next month']
}

/* ─── Component ─────────────────────────────────────────────────────────── */

export default function RecommendationCard({
  rec,
  delay = 0,
  onDismiss,
}: {
  rec: Recommendation
  delay?: number
  onDismiss?: (id: string, status: 'done' | 'not_relevant', reason?: string) => void
}) {
  const [expanded, setExpanded] = useState(false)
  /* "Not relevant" opens a one-line reason field. The reason is optional by
     design — the field is a chance to explain, never a toll gate, so dismissing
     with it empty is a first-class path (Enter on an empty input works). */
  const [reasonOpen, setReasonOpen] = useState(false)
  const [reason, setReason] = useState('')
  const urgency = getUrgencyStyle(rec.urgency_label)

  /* Margin provenance, resolved once and shared by the dollar figure and the
     margin badge below it — the two must never disagree about whether the
     number rests on the owner's real margin or on the 65% default.
     'provided' and 'calculated' are both grounded in the owner's own numbers,
     so they share the confident treatment; only 'estimated' is a guess. */
  const marginPct = rec.margin_pct != null ? Math.round(rec.margin_pct * 100) : null
  const isRealMargin =
    rec.margin_source === 'provided' || rec.margin_source === 'calculated'
  /* A defaulted margin scales the dollar impact just as silently as a real one,
     so the figure carries the qualifier inline. A tooltip is not disclosure:
     the number has to look like an estimate without being hovered. */
  const marginIsDefault = rec.margin_pct != null && !isRealMargin

  function confirmNotRelevant() {
    onDismiss?.(rec.id, 'not_relevant', reason)
    setReasonOpen(false)
    setReason('')
  }

  return (
    <div
      className="fade-up"
      style={{
        animationDelay: `${delay}ms`,
        opacity: 0,
        backgroundColor: 'var(--bg-card)',
        /* No coloured strip down the edge: confidence is already stated in
           words in the footer, and a rule per card turns a ranked list into a
           colour chart. The card is a hairline, a shadow and its contents. */
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-card)',
        boxShadow: 'var(--shadow-xs)',
        overflow: 'hidden',
        transition: 'border-color 0.2s ease, box-shadow 0.2s ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = 'var(--border2)'
        e.currentTarget.style.boxShadow = 'var(--shadow-md)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'var(--border)'
        e.currentTarget.style.boxShadow = 'var(--shadow-xs)'
      }}
    >
      <div style={{ padding: '22px 24px' }}>
        {/* Urgency badge */}
        <div style={{ marginBottom: '14px' }}>
          <span
            style={{
              display: 'inline-block',
              padding: '3px 10px',
              borderRadius: '4px',
              backgroundColor: urgency.bg,
              border: `1px solid ${urgency.edge}`,
              color: urgency.color,
              fontFamily: 'var(--font-heading)',
              fontSize: '0.72rem',
              fontWeight: 600,
              letterSpacing: '-0.002em',
            }}
          >
            {rec.urgency_label}
          </span>
        </div>

        {/* Title */}
        <h3 style={{ marginBottom: '10px' }}>{rec.title}</h3>

        {/* Body */}
        <div
          style={{
            fontFamily: 'var(--font-body)',
            fontSize: '13px',
            color: 'var(--t2)',
            lineHeight: 1.65,
            marginBottom: rec.impact_estimate != null && rec.impact_estimate > 0 ? '10px' : '16px',
            overflow: 'hidden',
            display: '-webkit-box',
            WebkitLineClamp: 3,
            WebkitBoxOrient: 'vertical' as const,
          }}
        >
          {rec.body}
        </div>

        {/* Impact estimate */}
        {rec.impact_estimate != null && rec.impact_estimate > 0 && (
          <div style={{ marginBottom: '14px' }}>
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                padding: '3px 9px',
                backgroundColor: 'var(--positive-dim)',
                border: '1px solid #bfe0d2',
                borderRadius: '4px',
                /* A dollar figure — mono, tabular. */
                fontFamily: 'var(--font-mono)',
                fontVariantNumeric: 'tabular-nums',
                fontSize: '0.68rem',
                fontWeight: 500,
                color: 'var(--green)',
              }}
            >
              ~${rec.impact_estimate.toLocaleString(undefined, { maximumFractionDigits: 0 })}/mo potential
              {marginIsDefault && (
                <span
                  style={{ opacity: 0.75, fontWeight: 400 }}
                  title={`Scaled by a default ${marginPct}% margin, not your own. Enter your margin at upload for a precise figure.`}
                >
                  (est.)
                </span>
              )}
            </span>
            {marginPct != null && (() => {
              const marginTitle =
                rec.margin_source === 'provided'
                  ? `Profit impact using your ${marginPct}% margin`
                  : rec.margin_source === 'calculated'
                    ? `Profit impact using your ${marginPct}% margin (calculated from your cost data)`
                    : `Profit estimate using a default ${marginPct}% margin. Enter your own at upload for a precise figure.`;
              return (
                <span
                  style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '3px',
                    marginLeft: '8px',
                    fontFamily: 'var(--font-mono)',
                    fontVariantNumeric: 'tabular-nums',
                    fontSize: '0.64rem',
                    color: isRealMargin ? 'var(--green)' : 'var(--t2)',
                  }}
                  title={marginTitle}
                >
                  {isRealMargin ? <Check size={10} strokeWidth={2.5} aria-hidden /> : '~'}
                  {marginPct}% margin
                </span>
              );
            })()}
          </div>
        )}

        {/* Divider */}
        <div
          style={{
            height: '1px',
            backgroundColor: 'var(--border)',
            marginBottom: '12px',
          }}
        />

        {/* Footer: confidence + transactions + done button */}
        <div
          className="rec-footer"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '12px',
            marginBottom: '12px',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
              fontFamily: 'var(--font-heading)',
              fontSize: '0.72rem',
              color: 'var(--t2)',
            }}
          >
            {/* Confidence tag */}
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '6px',
                padding: '2px 8px',
                background: 'var(--bg-alt)',
                border: '1px solid var(--border)',
                borderRadius: '4px',
                fontFamily: 'var(--font-heading)',
                fontWeight: 500,
                fontSize: '0.72rem',
              }}
            >
              <span
                style={{
                  width: '6px',
                  height: '6px',
                  borderRadius: '50%',
                  backgroundColor:
                    rec.confidence === 'high'
                      ? 'var(--green)'
                      : 'var(--amber)',
                  flexShrink: 0,
                }}
              />
              {rec.confidence === 'high' ? 'High' : 'Moderate'} confidence
            </span>
            {/* Transactions tag — a count, so the figure keeps the mono. */}
            <span
              style={{
                padding: '2px 8px',
                background: 'var(--bg-alt)',
                border: '1px solid var(--border)',
                borderRadius: '4px',
                fontFamily: 'var(--font-mono)',
                fontVariantNumeric: 'tabular-nums',
                fontSize: '0.68rem',
              }}
            >
              {rec.transaction_count.toLocaleString()} transactions
            </span>
          </div>

          {/* Two outcomes, deliberately not interchangeable: one asserts the user
              acted, the other asserts the advice missed. Solid accent vs. ghost so
              they can't be confused at a glance or hit by muscle memory. */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexShrink: 0 }}>
            <button
              onClick={() => onDismiss?.(rec.id, 'done')}
              disabled={!onDismiss}
              style={{
                flexShrink: 0,
                padding: '8px 16px',
                minHeight: '40px',
                backgroundColor: 'var(--accent)',
                border: '1px solid var(--accent)',
                borderRadius: '6px',
                fontFamily: 'var(--font-heading)',
                fontSize: '0.84rem',
                fontWeight: 600,
                letterSpacing: '-0.005em',
                color: '#ffffff',
                cursor: onDismiss ? 'pointer' : 'default',
                transition: 'background-color 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease',
                whiteSpace: 'nowrap',
                opacity: onDismiss ? 1 : 0.5,
              }}
              onMouseEnter={(e) => {
                if (!onDismiss) return
                e.currentTarget.style.background = 'var(--lp-accent-dark)'
                e.currentTarget.style.borderColor = 'var(--lp-accent-dark)'
                e.currentTarget.style.boxShadow = '0 4px 14px rgba(180,83,31,0.26)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.background = 'var(--accent)'
                e.currentTarget.style.borderColor = 'var(--accent)'
                e.currentTarget.style.boxShadow = 'none'
              }}
            >
              I did this
            </button>

            <button
              onClick={() => setReasonOpen((open) => !open)}
              disabled={!onDismiss}
              aria-expanded={reasonOpen}
              style={{
                flexShrink: 0,
                padding: '8px 14px',
                minHeight: '40px',
                backgroundColor: reasonOpen ? 'var(--bg-alt)' : 'transparent',
                border: `1px solid ${reasonOpen ? 'var(--border2)' : 'var(--border)'}`,
                borderRadius: '6px',
                fontFamily: 'var(--font-heading)',
                fontSize: '0.84rem',
                fontWeight: 500,
                letterSpacing: '-0.005em',
                color: reasonOpen ? 'var(--t1)' : 'var(--t2)',
                cursor: onDismiss ? 'pointer' : 'default',
                transition: 'background-color 0.2s ease, border-color 0.2s ease, color 0.2s ease',
                whiteSpace: 'nowrap',
                opacity: onDismiss ? 1 : 0.5,
              }}
              onMouseEnter={(e) => {
                if (!onDismiss) return
                e.currentTarget.style.backgroundColor = 'var(--bg-alt)'
                e.currentTarget.style.borderColor = 'var(--border2)'
                e.currentTarget.style.color = 'var(--t1)'
              }}
              onMouseLeave={(e) => {
                if (reasonOpen) return
                e.currentTarget.style.backgroundColor = 'transparent'
                e.currentTarget.style.borderColor = 'var(--border)'
                e.currentTarget.style.color = 'var(--t2)'
              }}
            >
              Not relevant
            </button>
          </div>
        </div>

        {/* Optional reason — revealed by "Not relevant", never required */}
        {reasonOpen && (
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              flexWrap: 'wrap',
              marginBottom: '12px',
              padding: '10px 12px',
              backgroundColor: 'var(--bg-mid)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--radius-card)',
            }}
          >
            <input
              autoFocus
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') {
                  e.preventDefault()
                  confirmNotRelevant()
                } else if (e.key === 'Escape') {
                  setReasonOpen(false)
                  setReason('')
                }
              }}
              placeholder="Why doesn't this apply? (optional)"
              maxLength={200}
              aria-label="Reason this recommendation is not relevant (optional)"
              style={{
                flex: '1 1 220px',
                minWidth: 0,
                padding: '7px 10px',
                minHeight: '36px',
                backgroundColor: 'var(--bg-card)',
                border: '1px solid var(--border)',
                borderRadius: '6px',
                fontFamily: 'var(--font-body)',
                fontSize: '0.8rem',
                color: 'var(--t1)',
                outline: 'none',
              }}
              onFocus={(e) => { e.currentTarget.style.borderColor = 'var(--accent)' }}
              onBlur={(e) => { e.currentTarget.style.borderColor = 'var(--border)' }}
            />
            <button
              onClick={confirmNotRelevant}
              style={{
                flexShrink: 0,
                padding: '7px 14px',
                minHeight: '36px',
                backgroundColor: 'var(--bg-card)',
                border: '1px solid var(--border2)',
                borderRadius: '6px',
                fontFamily: 'var(--font-heading)',
                fontSize: '0.8rem',
                fontWeight: 600,
                color: 'var(--t1)',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              Dismiss
            </button>
            <button
              onClick={() => { setReasonOpen(false); setReason('') }}
              style={{
                flexShrink: 0,
                padding: '7px 8px',
                minHeight: '36px',
                background: 'none',
                border: 'none',
                fontFamily: 'var(--font-heading)',
                fontSize: '0.8rem',
                fontWeight: 500,
                color: 'var(--t2)',
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              Cancel
            </button>
          </div>
        )}

        {/* Proof layer toggle */}
        {rec.proof && (
          <button
            onClick={() => setExpanded(!expanded)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '4px',
              padding: 0,
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              fontFamily: 'var(--font-heading)',
              fontSize: '0.8rem',
              fontWeight: 500,
              letterSpacing: '-0.004em',
              color: 'var(--accent)',
              transition: 'opacity 0.15s ease',
              marginBottom: expanded ? '0' : undefined,
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.opacity = '0.7'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.opacity = '1'
            }}
          >
            {expanded
              ? <ChevronDown size={13} strokeWidth={2} aria-hidden />
              : <ChevronRight size={13} strokeWidth={2} aria-hidden />}
            Show the data behind this ({rec.proof.sample_size.toLocaleString()} transactions)
          </button>
        )}

        {/* Expanded proof + see_why */}
        <div
          style={{
            maxHeight: expanded ? '500px' : '0px',
            overflow: 'hidden',
            transition: 'max-height 0.35s ease',
          }}
        >
          {/* Proof data grid */}
          {rec.proof && (
            <div
              style={{
                marginTop: '10px',
                padding: '14px 16px',
                backgroundColor: 'var(--bg-mid)',
                borderRadius: 'var(--radius-card)',
                border: '1px solid var(--border)',
                display: 'flex',
                flexWrap: 'wrap',
                gap: '16px',
              }}
            >
              {/* Sample size */}
              <div style={{ minWidth: '100px' }}>
                <div
                  style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    letterSpacing: '-0.002em',
                    color: 'var(--t2)',
                    marginBottom: '3px',
                    padding: '2px 8px',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border)',
                    borderRadius: '4px',
                    display: 'inline-block',
                  }}
                >
                  Based on
                </div>
                <div
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontVariantNumeric: 'tabular-nums',
                    fontSize: '0.85rem',
                    fontWeight: 500,
                    color: 'var(--t1)',
                    marginTop: '4px',
                  }}
                >
                  {rec.proof.sample_size.toLocaleString()} transactions
                </div>
              </div>

              {/* Date range */}
              <div style={{ minWidth: '100px' }}>
                <div
                  style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    letterSpacing: '-0.002em',
                    color: 'var(--t2)',
                    marginBottom: '3px',
                    padding: '2px 8px',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border)',
                    borderRadius: '4px',
                    display: 'inline-block',
                  }}
                >
                  Date range
                </div>
                <div
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontVariantNumeric: 'tabular-nums',
                    fontSize: '0.85rem',
                    fontWeight: 500,
                    color: 'var(--t1)',
                    marginTop: '4px',
                  }}
                >
                  {rec.proof.date_range.display}
                </div>
              </div>

              {/* Key metric */}
              <div style={{ minWidth: '100px' }}>
                <div
                  style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    letterSpacing: '-0.002em',
                    color: 'var(--t2)',
                    marginBottom: '3px',
                    padding: '2px 8px',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border)',
                    borderRadius: '4px',
                    display: 'inline-block',
                  }}
                >
                  {rec.proof.key_metric.name}
                </div>
                <div
                  style={{
                    fontFamily: 'var(--font-mono)',
                    fontVariantNumeric: 'tabular-nums',
                    fontSize: '0.85rem',
                    fontWeight: 500,
                    color: 'var(--t1)',
                    marginTop: '4px',
                  }}
                >
                  {rec.proof.key_metric.value != null
                    ? rec.proof.key_metric.value.toFixed(2)
                    : 'n/a'}
                  {rec.proof.key_metric.interpretation && (
                    <span
                      style={{
                        marginLeft: '6px',
                        fontFamily: 'var(--font-body)',
                        fontSize: '0.72rem',
                        fontWeight: 400,
                        color: 'var(--t2)',
                      }}
                    >
                      ({rec.proof.key_metric.interpretation})
                    </span>
                  )}
                </div>
              </div>

              {/* Confidence */}
              <div style={{ minWidth: '80px' }}>
                <div
                  style={{
                    fontFamily: 'var(--font-heading)',
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    letterSpacing: '-0.002em',
                    color: 'var(--t2)',
                    marginBottom: '3px',
                    padding: '2px 8px',
                    background: 'var(--bg-card)',
                    border: '1px solid var(--border)',
                    borderRadius: '4px',
                    display: 'inline-block',
                  }}
                >
                  Confidence
                </div>
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    marginTop: '4px',
                  }}
                >
                  <span
                    style={{
                      width: '7px',
                      height: '7px',
                      borderRadius: '50%',
                      backgroundColor:
                        rec.proof.confidence.color === 'green'
                          ? 'var(--green)'
                          : rec.proof.confidence.color === 'amber'
                          ? 'var(--amber)'
                          : 'var(--red)',
                      flexShrink: 0,
                    }}
                  />
                  <span
                    style={{
                      fontFamily: 'var(--font-heading)',
                      fontSize: '0.85rem',
                      fontWeight: 600,
                      color:
                        rec.proof.confidence.color === 'green'
                          ? 'var(--green)'
                          : rec.proof.confidence.color === 'amber'
                          ? 'var(--amber)'
                          : 'var(--red)',
                      textTransform: 'capitalize',
                    }}
                  >
                    {rec.proof.confidence.tier}
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* See why text */}
          <div
            style={{
              marginTop: '8px',
              padding: '12px 14px',
              backgroundColor: 'var(--bg-mid)',
              borderRadius: 'var(--radius-card)',
              border: '1px solid var(--border)',
              fontFamily: 'var(--font-body)',
              fontSize: '0.76rem',
              color: 'var(--t2)',
              lineHeight: 1.6,
              whiteSpace: 'pre-line',
            }}
          >
            {rec.see_why}
          </div>
        </div>

        {/* Fallback: See why toggle if no proof */}
        {!rec.proof && (
          <>
            <button
              onClick={() => setExpanded(!expanded)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '4px',
                padding: 0,
                background: 'none',
                border: 'none',
                cursor: 'pointer',
                fontFamily: 'var(--font-heading)',
                fontSize: '0.8rem',
                fontWeight: 500,
                letterSpacing: '-0.004em',
                color: 'var(--accent)',
                transition: 'opacity 0.15s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.opacity = '0.7'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.opacity = '1'
              }}
            >
              See why
              <span
                style={{
                  display: 'inline-flex',
                  transition: 'transform 0.25s ease',
                  transform: expanded ? 'rotate(90deg)' : 'rotate(0deg)',
                }}
              >
                <ArrowRight size={13} strokeWidth={2} aria-hidden />
              </span>
            </button>
            <div
              style={{
                maxHeight: expanded ? '200px' : '0px',
                overflow: 'hidden',
                transition: 'max-height 0.3s ease',
              }}
            >
              <div
                style={{
                  marginTop: '10px',
                  padding: '12px 14px',
                  backgroundColor: 'var(--bg-mid)',
                  borderRadius: 'var(--radius-card)',
                  border: '1px solid var(--border)',
                  fontFamily: 'var(--font-body)',
                  fontSize: '0.76rem',
                  color: 'var(--t2)',
                  lineHeight: 1.6,
                  whiteSpace: 'pre-line',
                }}
              >
                {rec.see_why}
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
