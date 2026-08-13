import type { PaceStatus } from '@/lib/api'
import { formatPace } from '@/lib/format'
import { Badge } from '@/components/ui/badge'

const tone: Record<PaceStatus, 'good' | 'warn' | 'bad' | 'default' | 'accent'> = {
  achieved: 'good',
  ahead: 'good',
  on_track: 'accent',
  behind: 'warn',
  overdue: 'bad',
  no_data: 'default',
}

export function PaceBadge({ pace }: { pace: PaceStatus }) {
  return <Badge tone={tone[pace]}>{formatPace(pace)}</Badge>
}
