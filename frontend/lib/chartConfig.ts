/**
 * Chart tokens — KERN brand system.
 *
 * Recharts renders to SVG attributes rather than CSS properties, so several of
 * these have to be literal values instead of `var(--token)` references. They are
 * kept here, in one file, mirroring the custom properties in app/globals.css so
 * charts and chrome stay in step. Values that *are* consumed as CSS (tooltip
 * contentStyle / labelStyle) use the tokens directly.
 */

export const CHART_COLORS = {
  primary:   '#b4531f',                  // --lp-accent
  secondary: 'rgba(180,83,31,0.45)',
  muted:     'rgba(180,83,31,0.14)',
  grid:      '#e6e1da',                  // --lp-line
  axis:      '#cdc5ba',                  // --lp-line-2
  positive:  '#147a55',                  // --green
  negative:  '#b02a20',                  // --red
  warning:   '#8a6008',                  // --amber
  surface:   '#ffffff',                  // --bg-card (white cards in the app)
  elevated:  '#f7f5f2',                  // --bg-mid
}

export const tooltipStyle = {
  contentStyle: {
    backgroundColor: 'var(--bg-card)',
    border: '1px solid var(--border)',
    borderRadius: 'var(--radius)',
    color: 'var(--t1)',
    /* The readout is figures, so it stays mono and tabular. Its heading is a
       label and follows the label voice. */
    fontFamily: 'var(--font-mono)',
    fontVariantNumeric: 'tabular-nums',
    fontSize: '12px',
    boxShadow: 'var(--shadow-md)',
    padding: '10px 14px',
  },
  labelStyle: {
    color: 'var(--t1)',
    fontWeight: 600,
    fontSize: '11px',
    letterSpacing: '-0.004em',
    marginBottom: '4px',
    fontFamily: 'var(--font-heading)',
  },
  cursor: { fill: 'rgba(180,83,31,0.07)' },
}

export const axisStyle = {
  tick:     { fill: '#55504a', fontFamily: 'var(--font-mono)', fontSize: 10 }, // --t2
  axisLine: { stroke: '#cdc5ba' },                                            // --lp-line-2
  tickLine: { stroke: 'transparent' },
}
