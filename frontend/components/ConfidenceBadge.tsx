const CONFIG = {
  high:         { color: 'var(--green)',  bg: 'var(--positive-dim)',  label: 'Strong signal' },
  moderate:     { color: 'var(--amber)',  bg: 'var(--warning-dim)',   label: 'Worth testing' },
  directional:  { color: 'var(--amber)',  bg: 'var(--warning-dim)',   label: 'Worth testing' },
  insufficient: { color: 'var(--t2)',     bg: 'var(--bg-alt)',        label: 'Needs more data' },
} as const

export default function ConfidenceBadge({
  confidence,
  label,
}: {
  confidence: 'high' | 'moderate' | 'directional' | 'insufficient'
  label?: string
}) {
  const cfg = CONFIG[confidence] ?? CONFIG.moderate
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '5px',
      padding: '2px 8px',
      borderRadius: '4px',
      backgroundColor: cfg.bg,
      border: '1px solid var(--border)',
      color: cfg.color,
      fontFamily: 'var(--font-heading)',
      fontWeight: 600,
      fontSize: '0.72rem',
      letterSpacing: '-0.002em',
      flexShrink: 0,
      whiteSpace: 'nowrap',
    }}>
      <span style={{
        width: '5px',
        height: '5px',
        borderRadius: '50%',
        backgroundColor: cfg.color,
        flexShrink: 0,
      }} />
      {label ?? cfg.label}
    </span>
  )
}
