/**
 * Shared semantic tokens for the UI primitives.
 *
 * Every colour here resolves to a custom property declared in app/globals.css.
 * Components must reference these rather than literal hex values — that is what
 * keeps a palette change to a single file.
 */

export type Tone = 'positive' | 'negative' | 'warning' | 'info' | 'neutral'

export interface ToneTokens {
  /** Foreground: text, icon, rule. */
  fg: string
  /** Low-alpha background wash for pills and tinted panels. */
  dim: string
  /** Border colour for tinted panels. */
  edge: string
}

export const TONES: Record<Tone, ToneTokens> = {
  positive: { fg: 'var(--green)', dim: 'var(--positive-dim)', edge: '#bfe0d2' },
  negative: { fg: 'var(--red)',   dim: 'var(--negative-dim)', edge: '#efc9c4' },
  warning:  { fg: 'var(--amber)', dim: 'var(--warning-dim)',  edge: '#e6d3a8' },
  info:     { fg: 'var(--accent)', dim: 'var(--accent-dim)',  edge: '#eccdb8' },
  neutral:  { fg: 'var(--t2)',    dim: 'var(--bg-alt)',       edge: 'var(--border)' },
}

export function tone(t: Tone): ToneTokens {
  return TONES[t]
}

/** Delta sign → tone. Keeps "up is green" logic in one place. */
export function deltaTone(value: number): Tone {
  return value >= 0 ? 'positive' : 'negative'
}

/**
 * House style for inline lucide icons: 16px in the accent, held back slightly
 * so an icon reads as annotation rather than competing with the figure it
 * labels. On a light ground the accent needs more of itself than it did on
 * navy — at 60% terracotta goes pink against paper.
 */
export const ICON_SIZE = 16

export const iconProps = {
  size: ICON_SIZE,
  strokeWidth: 1.75,
  style: { color: 'var(--accent)', opacity: 0.85, flexShrink: 0 } as const,
}

/** Same treatment at display scale, for empty states. */
export const emptyIconProps = {
  size: 28,
  strokeWidth: 1.25,
  style: { color: 'var(--accent)', opacity: 0.85, flexShrink: 0 } as const,
}
