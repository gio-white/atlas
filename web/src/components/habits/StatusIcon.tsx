import { Check, Clock, Snowflake, X } from 'lucide-react'

import type { HabitDayStatus } from '@/lib/api'

import { Ring } from './Ring'

/**
 * A day's status as an icon (habits brief §13): Done a filled check in the success green; Not
 * done a quiet grey cross, never red; In progress a partial ring in the accent colour; Waiting a
 * grey clock; Frozen a grey snowflake; Open an empty circle; Blank a faint dashed circle.
 */
export function StatusIcon({ status, share = 0 }: { status: HabitDayStatus; share?: number }) {
  switch (status) {
    case 'done':
      return (
        <span className="flex size-6 items-center justify-center rounded-full bg-good text-on-accent">
          <Check className="size-4" strokeWidth={3} aria-hidden />
        </span>
      )
    case 'not_done':
      return (
        <span className="flex size-6 items-center justify-center rounded-full border-2 border-line text-muted">
          <X className="size-3.5" strokeWidth={2.5} aria-hidden />
        </span>
      )
    case 'in_progress':
      return <Ring share={share} size={24} />
    case 'waiting':
      return <Clock className="size-6 text-muted" strokeWidth={1.75} aria-hidden />
    case 'frozen':
      return <Snowflake className="size-6 text-muted" strokeWidth={1.75} aria-hidden />
    case 'blank':
      return <span className="block size-6 rounded-full border-2 border-dashed border-line" />
    case 'open':
      return <span className="block size-6 rounded-full border-2 border-muted/50" />
    default:
      return <span className="block size-6" />
  }
}
