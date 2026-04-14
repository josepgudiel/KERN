const CONFIG = {
  high:         { color: 'var(--green)',  bg: 'var(--positive-dim)',  label: 'Strong Signal' },
  moderate:     { color: 'var(--amber)',  bg: 'var(--warning-dim)',   label: 'Worth Testing' },
  directional:  { color: 'var(--amber)',  bg: 'var(--warning-dim)',   label: 'Worth Testing' },
  insufficient: { color: 'var(--t3)',     bg: 'var(--sky-06)',        label: 'Need More Data' },
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
      backgroundColor: 'rgba(179,229,254,0.04)',
      border: '1px solid var(--border)',
      color: cfg.color,
      fontFamily: 'var(--font-mono)',
      fontWeight: 500,
      fontSize: '9px',
      letterSpacing: '0.10em',
      textTransform: 'uppercase',
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
