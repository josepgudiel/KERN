'use client'

import { useState } from 'react'
import { Recommendation } from '@/types'

/* ─── Urgency badge config ──────────────────────────────────────────────── */

const URGENCY_STYLES: Record<string, { bg: string; color: string }> = {
  'Act this week': {
    bg: 'rgba(248,113,113,0.15)',
    color: 'var(--red)',
  },
  'Worth doing soon': {
    bg: 'rgba(251,191,36,0.15)',
    color: 'var(--amber)',
  },
  'Plan for next month': {
    bg: 'var(--sky-06)',
    color: 'var(--t3)',
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
  onDismiss?: (id: string) => void
}) {
  const [expanded, setExpanded] = useState(false)
  const urgency = getUrgencyStyle(rec.urgency_label)

  return (
    <div
      className="fade-up"
      style={{
        animationDelay: `${delay}ms`,
        opacity: 0,
        backgroundColor: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderRadius: 'var(--radius-card)',
        overflow: 'hidden',
        transition: 'border-color 0.2s ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = 'var(--border2)'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'var(--border)'
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
              color: urgency.color,
              fontFamily: 'var(--font-mono)',
              fontSize: '0.58rem',
              fontWeight: 500,
              letterSpacing: '0.10em',
              textTransform: 'uppercase',
            }}
          >
            {rec.urgency_label}
          </span>
        </div>

        {/* Title */}
        <div
          style={{
            fontFamily: 'var(--font-display)',
            fontWeight: 800,
            fontSize: '1rem',
            color: 'var(--t1)',
            lineHeight: 1.4,
            marginBottom: '10px',
            letterSpacing: '0.04em',
            textTransform: 'uppercase',
          }}
        >
          {rec.title}
        </div>

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
                borderRadius: '4px',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.6rem',
                fontWeight: 500,
                color: 'var(--green)',
                letterSpacing: '0.04em',
              }}
            >
              ~${rec.impact_estimate.toLocaleString(undefined, { maximumFractionDigits: 0 })}/mo potential
            </span>
            {rec.margin_pct != null && (
              <span
                style={{
                  marginLeft: '6px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.55rem',
                  color: rec.margin_source === 'provided' ? 'var(--green)' : 'var(--t3)',
                  letterSpacing: '0.04em',
                }}
                title={
                  rec.margin_source === 'provided'
                    ? `Profit impact using your ${Math.round(rec.margin_pct * 100)}% margin`
                    : `Profit estimate using default 65% margin — enter your actual margin at upload for accuracy`
                }
              >
                {rec.margin_source === 'provided' ? '✓' : '~'}{Math.round(rec.margin_pct * 100)}% margin
              </span>
            )}
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
              gap: '12px',
              fontFamily: 'var(--font-mono)',
              fontSize: '0.6rem',
              color: 'var(--t3)',
              letterSpacing: '0.04em',
            }}
          >
            {/* Confidence tag */}
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                padding: '2px 8px',
                background: 'rgba(179,229,254,0.04)',
                border: '1px solid var(--border)',
                borderRadius: '4px',
                fontFamily: 'var(--font-mono)',
                fontSize: '9px',
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
            <span style={{ color: 'var(--border2)' }}>&middot;</span>
            {/* Transactions tag */}
            <span
              style={{
                padding: '2px 8px',
                background: 'rgba(179,229,254,0.04)',
                border: '1px solid var(--border)',
                borderRadius: '4px',
                fontFamily: 'var(--font-mono)',
                fontSize: '9px',
              }}
            >
              {rec.transaction_count.toLocaleString()} transactions
            </span>
          </div>

          <button
            onClick={() => onDismiss?.(rec.id)}
            style={{
              flexShrink: 0,
              padding: '8px 16px',
              minHeight: '40px',
              backgroundColor: 'var(--blue)',
              border: 'none',
              borderRadius: 'var(--radius)',
              fontFamily: 'var(--font-display)',
              fontSize: '0.58rem',
              fontWeight: 700,
              letterSpacing: '0.10em',
              textTransform: 'uppercase',
              color: 'var(--t1)',
              cursor: onDismiss ? 'pointer' : 'default',
              transition: 'all 0.15s ease',
              whiteSpace: 'nowrap',
              opacity: onDismiss ? 1 : 0.5,
            }}
            onMouseEnter={(e) => {
              if (!onDismiss) return
              e.currentTarget.style.background = '#4762b8'
              e.currentTarget.style.boxShadow = '0 0 20px rgba(57,79,154,0.4)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'var(--blue)'
              e.currentTarget.style.boxShadow = 'none'
            }}
          >
            Done
          </button>
        </div>

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
              fontFamily: 'var(--font-mono)',
              fontSize: '0.62rem',
              fontWeight: 500,
              letterSpacing: '0.06em',
              color: 'var(--sky)',
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
            {expanded ? '▼' : '▶'} Show data behind this ({rec.proof.sample_size.toLocaleString()} txns)
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
                    fontFamily: 'var(--font-mono)',
                    fontSize: '9px',
                    fontWeight: 500,
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase',
                    color: 'var(--t3)',
                    marginBottom: '3px',
                    padding: '2px 8px',
                    background: 'rgba(179,229,254,0.04)',
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
                    fontFamily: 'var(--font-mono)',
                    fontSize: '9px',
                    fontWeight: 500,
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase',
                    color: 'var(--t3)',
                    marginBottom: '3px',
                    padding: '2px 8px',
                    background: 'rgba(179,229,254,0.04)',
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
                    fontFamily: 'var(--font-mono)',
                    fontSize: '9px',
                    fontWeight: 500,
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase',
                    color: 'var(--t3)',
                    marginBottom: '3px',
                    padding: '2px 8px',
                    background: 'rgba(179,229,254,0.04)',
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
                    fontSize: '0.85rem',
                    fontWeight: 500,
                    color: 'var(--t1)',
                    marginTop: '4px',
                  }}
                >
                  {rec.proof.key_metric.value != null
                    ? rec.proof.key_metric.value.toFixed(2)
                    : '—'}
                  {rec.proof.key_metric.interpretation && (
                    <span
                      style={{
                        marginLeft: '6px',
                        fontFamily: 'var(--font-body)',
                        fontSize: '0.72rem',
                        fontWeight: 400,
                        color: 'var(--t3)',
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
                    fontFamily: 'var(--font-mono)',
                    fontSize: '9px',
                    fontWeight: 500,
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase',
                    color: 'var(--t3)',
                    marginBottom: '3px',
                    padding: '2px 8px',
                    background: 'rgba(179,229,254,0.04)',
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
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.85rem',
                      fontWeight: 500,
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
                fontFamily: 'var(--font-mono)',
                fontSize: '0.62rem',
                fontWeight: 500,
                letterSpacing: '0.06em',
                color: 'var(--sky)',
                transition: 'opacity 0.15s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.opacity = '0.7'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.opacity = '1'
              }}
            >
              See why{' '}
              <span
                style={{
                  display: 'inline-block',
                  transition: 'transform 0.25s ease',
                  transform: expanded ? 'rotate(90deg)' : 'rotate(0deg)',
                  fontSize: '0.72rem',
                }}
              >
                &rarr;
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
