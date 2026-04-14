'use client'

interface MetricCardProps {
  label: string
  value: string | number
  delta?: string | null
  deltaPositive?: boolean
  delay?: number
  accent?: boolean
}

export default function MetricCard({
  label,
  value,
  delta,
  deltaPositive,
  delay = 0,
  accent = false,
}: MetricCardProps) {
  return (
    <div
      className="fade-up"
      style={{
        animationDelay: `${delay}ms`,
        opacity: 0,
        position: 'relative',
        overflow: 'hidden',
        backgroundColor: 'var(--bg-card)',
        border: '1px solid var(--border)',
        borderLeft: accent ? '3px solid var(--sky)' : '1px solid var(--border)',
        borderRadius: 'var(--radius-card)',
        padding: 'clamp(14px, 3vw, 20px) clamp(14px, 3vw, 22px)',
        transition: 'border-color 0.2s ease',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = 'var(--border2)'
        if (!accent) e.currentTarget.style.borderLeft = '3px solid var(--sky)'
        const line = e.currentTarget.querySelector<HTMLElement>('.scanline')
        if (line) line.style.animation = 'scanLine 600ms ease forwards'
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = 'var(--border)'
        if (!accent) e.currentTarget.style.borderLeft = '1px solid var(--border)'
        const line = e.currentTarget.querySelector<HTMLElement>('.scanline')
        if (line) { line.style.animation = 'none'; line.style.top = '0' }
      }}
    >
      {/* Scan-line overlay */}
      <div
        className="scanline"
        style={{
          position: 'absolute',
          left: 0,
          right: 0,
          top: 0,
          height: '1px',
          background: 'linear-gradient(90deg, transparent, var(--sky), transparent)',
          opacity: 0,
          pointerEvents: 'none',
        }}
      />

      {/* Label */}
      <div
        className="label-caps"
        style={{ marginBottom: '14px', color: 'var(--t3)' }}
      >
        {label}
      </div>

      {/* Value — DM Mono */}
      <div
        style={{
          fontFamily: 'var(--font-mono)',
          fontWeight: 500,
          fontSize: 'clamp(1.8rem, 3vw, 2.5rem)',
          lineHeight: 1,
          letterSpacing: '-0.02em',
          color: 'var(--t1)',
          marginBottom: delta ? '10px' : '0',
        }}
      >
        {value}
      </div>

      {/* Delta */}
      {delta && (
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '5px',
          padding: '3px 8px',
          borderRadius: '4px',
          backgroundColor:
            deltaPositive === undefined
              ? 'var(--sky-06)'
              : deltaPositive
              ? 'var(--positive-dim)'
              : 'var(--negative-dim)',
          fontFamily: 'var(--font-mono)',
          fontSize: '0.60rem',
          fontWeight: 500,
          letterSpacing: '0.04em',
          color:
            deltaPositive === undefined
              ? 'var(--t3)'
              : deltaPositive
              ? 'var(--green)'
              : 'var(--red)',
        }}>
          {deltaPositive !== undefined && (
            <span style={{ fontSize: '0.5rem' }}>{deltaPositive ? '▲' : '▼'}</span>
          )}
          {delta}
        </div>
      )}
    </div>
  )
}
