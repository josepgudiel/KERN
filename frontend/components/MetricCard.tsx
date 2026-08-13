'use client'

import { TrendingDown, TrendingUp } from 'lucide-react'
import { Badge, StatTile } from '@/components/ui'

interface MetricCardProps {
  label: string
  value: string | number
  delta?: string | null
  deltaPositive?: boolean
  delay?: number
}

/**
 * Headline metric tile. A thin wrapper over <StatTile> so metric density,
 * padding and value sizing stay defined in exactly one place.
 *
 * There is no "highlight this one" flag: in a row of four figures, singling
 * one out with colour tells the reader nothing the layout order doesn't
 * already say.
 */
export default function MetricCard({
  label,
  value,
  delta,
  deltaPositive,
  delay = 0,
}: MetricCardProps) {
  const deltaTone = deltaPositive === undefined ? 'neutral' : deltaPositive ? 'positive' : 'negative'
  const DeltaIcon = deltaPositive ? TrendingUp : TrendingDown

  return (
    <StatTile
      className="fade-up"
      style={{ animationDelay: `${delay}ms`, opacity: 0 }}
      label={label}
      value={value}
      footer={delta ? (
        <Badge
          toneName={deltaTone}
          shape="tag"
          icon={deltaPositive !== undefined
            ? <DeltaIcon size={12} strokeWidth={2} aria-hidden />
            : undefined}
        >
          {delta}
        </Badge>
      ) : undefined}
    />
  )
}
