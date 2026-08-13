'use client'

import { Coins, Gem, Star, TrendingDown, Package } from 'lucide-react'
import type { Cluster } from '@/types'
import { Card, iconProps, tone, type Tone } from '@/components/ui'

/* Stars = healthy, Cash Cows = steady, Hidden Gems = upside, Low Activity =
   needs attention. The tone colours the icon only. Tinting four cards four
   ways would turn a group of peers into a traffic light, and none of these is
   an alert — they are just categories. */
const CLUSTER_META: Record<string, { tone: Tone; Icon: typeof Star }> = {
  'Stars':        { tone: 'positive', Icon: Star },
  'Cash Cows':    { tone: 'info',     Icon: Coins },
  'Hidden Gems':  { tone: 'info',     Icon: Gem },
  'Low Activity': { tone: 'warning',  Icon: TrendingDown },
}

const FALLBACK = { tone: 'neutral' as Tone, Icon: Package }

interface ClusterCardProps {
  cluster: Cluster
  currency?: string
}

export default function ClusterCard({ cluster, currency = '$' }: ClusterCardProps) {
  const { tone: clusterTone, Icon } = CLUSTER_META[cluster.label] ?? FALLBACK

  return (
    <Card interactive padding="18px 20px">
      {/* Heading */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '14px' }}>
        <Icon {...iconProps} style={{ ...iconProps.style, color: tone(clusterTone).fg }} aria-hidden />
        <h3 className="cluster-heading" style={{ margin: 0 }}>{cluster.label}</h3>
      </div>

      {/* Figures */}
      <div style={{ display: 'flex', gap: '22px', marginBottom: '14px' }}>
        <div>
          <div className="ui-label">Average revenue</div>
          <p className="number-display" style={{ fontSize: '1.25rem', marginTop: '5px' }}>
            {currency}{cluster.avg_revenue.toLocaleString(undefined, { maximumFractionDigits: 0 })}
          </p>
        </div>
        <div>
          <div className="ui-label">Average quantity</div>
          <p className="number-display" style={{ fontSize: '1.25rem', marginTop: '5px' }}>
            {cluster.avg_quantity.toLocaleString()}
          </p>
        </div>
      </div>

      {/* Members */}
      <ul style={{
        fontFamily: 'var(--font-body)',
        fontSize: '0.78rem',
        color: 'var(--t2)',
        marginBottom: '12px',
        listStyle: 'none',
        padding: 0,
        display: 'flex',
        flexDirection: 'column',
        gap: '3px',
      }}>
        {cluster.products.slice(0, 6).map((p) => (
          <li key={p} style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {p}
          </li>
        ))}
        {cluster.products.length > 6 && (
          <li style={{ color: 'var(--t2)' }}>+{cluster.products.length - 6} more</li>
        )}
      </ul>

      {/* Recommended action */}
      <p style={{
        paddingTop: '12px',
        borderTop: '1px solid var(--border)',
        fontFamily: 'var(--font-body)',
        fontSize: '0.78rem',
        color: 'var(--t2)',
        lineHeight: 1.6,
        margin: 0,
      }}>
        {cluster.action}
      </p>
    </Card>
  )
}
