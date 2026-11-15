import { Check, Clock, Snowflake, X } from 'lucide-react'

import type { HabitDayStatus } from '@/lib/api'
import { cn } from '@/lib/utils'

import { Ring } from './Ring'

/**
 * A day's status as an icon (habits brief §13): Done a filled check in the success green; Not
 * done a quiet grey cross, never red; In progress a partial ring in the accent colour; Waiting a
 * grey clock; Frozen a grey snowflake; Open an empty circle; Blank a faint dashed circle;
 * Upcoming a dimmed dot; Not scheduled nothing.
 */
export function StatusIcon({
  status,
  share = 0,
  small = false,
}: {
  status: HabitDayStatus
  share?: number
  /** The Week tab's cells: 20px instead of 24px. */
  small?: boolean
}) {
  const box = small ? 'size-5' : 'size-6'
  switch (status) {
    case 'done':
      return (
        <span
          className={cn(
            box,
            'flex items-center justify-center rounded-full bg-good text-on-accent',
          )}
        >
          <Check className={small ? 'size-3.5' : 'size-4'} strokeWidth={3} aria-hidden />
        </span>
      )
    case 'not_done':
      return (
        <span
          className={cn(
            box,
            'flex items-center justify-center rounded-full border-2 border-line text-muted',
          )}
        >
          <X className={small ? 'size-3' : 'size-3.5'} strokeWidth={2.5} aria-hidden />
        </span>
      )
    case 'in_progress':
      return <Ring share={share} size={small ? 20 : 24} />
    case 'waiting':
      return <Clock className={cn(box, 'text-muted')} strokeWidth={1.75} aria-hidden />
    case 'frozen':
      return <Snowflake className={cn(box, 'text-muted')} strokeWidth={1.75} aria-hidden />
    case 'blank':
      return <span className={cn(box, 'block rounded-full border-2 border-dashed border-line')} />
    case 'open':
      return <span className={cn(box, 'block rounded-full border-2 border-muted/50')} />
    case 'upcoming':
      return (
        <span className={cn(box, 'flex items-center justify-center')}>
          <span className="size-1 rounded-full bg-muted/40" />
        </span>
      )
    default:
      return <span className={cn(box, 'block')} />
  }
}
