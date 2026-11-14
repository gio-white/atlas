import { ChevronLeft, ChevronRight } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { parseIsoDate } from '@/lib/dates'
import { cn } from '@/lib/utils'

import { Ring } from './Ring'

export type StripDay = { day: string; done: number; total: number }

/**
 * Monday to Sunday of the selected day's week, each day with a ring of the share of its
 * scheduled habits that are done (habits brief §7). Days after today are dimmed and cannot be
 * picked; ‹ › move a week.
 */
export function WeekStrip({
  week,
  selected,
  today,
  onSelect,
  previous,
  next,
}: {
  week: StripDay[]
  selected: string
  today: string
  onSelect: (day: string) => void
  previous: string
  next: string | undefined
}) {
  return (
    <div className="flex items-center gap-1">
      <Button
        variant="ghost"
        size="icon"
        className="size-11 shrink-0"
        aria-label="Previous week"
        onClick={() => onSelect(previous)}
      >
        <ChevronLeft className="size-4" aria-hidden />
      </Button>
      <ol aria-label="Week" className="grid flex-1 grid-cols-7 gap-0.5">
        {week.map((entry) => {
          const date = parseIsoDate(entry.day)
          const future = entry.day > today
          const isSelected = entry.day === selected
          const weekday = date.toLocaleDateString('en-GB', { weekday: 'short' })
          const share = entry.total === 0 ? 0 : entry.done / entry.total
          return (
            <li key={entry.day} className="flex">
              <button
                type="button"
                disabled={future}
                aria-current={isSelected ? 'date' : undefined}
                aria-label={`${date.toLocaleDateString('en-GB', {
                  weekday: 'long',
                  day: 'numeric',
                  month: 'long',
                })}${future ? '' : `, ${entry.done} of ${entry.total} done`}`}
                onClick={() => onSelect(entry.day)}
                className={cn(
                  'flex min-h-11 flex-1 flex-col items-center gap-1 rounded-xl py-1.5 text-xs motion-safe:transition-colors motion-safe:duration-200 focus-visible:ring-2 focus-visible:ring-accent focus-visible:outline-none',
                  isSelected ? 'bg-raised text-ink' : 'text-muted hover:bg-raised/60',
                  future && 'cursor-default opacity-40 hover:bg-transparent',
                )}
              >
                <span aria-hidden>{weekday.charAt(0)}</span>
                <span
                  aria-hidden
                  className={cn(
                    'text-sm tabular-nums',
                    isSelected ? 'font-semibold text-ink' : 'text-ink',
                    entry.day === today && !isSelected && 'text-accent',
                  )}
                >
                  {date.getDate()}
                </span>
                {future ? <span className="size-4" /> : <Ring share={share} size={16} />}
              </button>
            </li>
          )
        })}
      </ol>
      <Button
        variant="ghost"
        size="icon"
        className="size-11 shrink-0"
        aria-label="Next week"
        disabled={next === undefined}
        onClick={() => next !== undefined && onSelect(next)}
      >
        <ChevronRight className="size-4" aria-hidden />
      </Button>
    </div>
  )
}
