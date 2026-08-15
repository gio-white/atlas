import { Check, Minus, X } from 'lucide-react'
import { Link } from 'react-router-dom'

import type { WeekDayCell, WeekHabit } from '@/lib/api'
import { weekdayLabel } from '@/lib/dates'
import { formatComparator } from '@/lib/format'
import { HABIT_PERIOD_META } from '@/lib/habitsSummary'

export function WeekGrid({
  habits,
  search,
  compact = false,
}: {
  habits: WeekHabit[]
  search: string
  compact?: boolean
}) {
  const headings = habits[0]?.days ?? []

  if (habits.length === 0) {
    return (
      <p className="text-sm text-muted">
        No habits in this window. Add one on the Habits board to see the grid fill in.
      </p>
    )
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[40rem] border-collapse text-sm">
        <thead>
          <tr>
            <th className="pb-2 pr-3 text-left font-medium text-muted">Habit</th>
            {headings.map((cell) => (
              <th
                key={cell.day}
                className="px-1 pb-2 text-center font-mono text-xs font-medium text-muted"
              >
                {compact ? (
                  <div>{cell.day.slice(8)}</div>
                ) : (
                  <>
                    <div>{weekdayLabel(cell.day)}</div>
                    <div>{cell.day.slice(8)}</div>
                  </>
                )}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {habits.map((habit) => (
            <tr key={habit.slug} className="border-t border-line">
              <td className="py-3 pr-3">
                <Link
                  to={{ pathname: `/habit/${habit.slug}`, search }}
                  className="font-medium hover:text-warn"
                >
                  {habit.name}
                </Link>
                <div className="font-mono text-xs text-muted">
                  {formatComparator(habit.comparator)} {habit.target_value} ·{' '}
                  {HABIT_PERIOD_META[habit.period].label} · streak {habit.current_streak}
                </div>
              </td>
              {habit.days.map((cell) => (
                <td key={cell.day} className="px-1 py-3 text-center">
                  <DayDot cell={cell} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export function DayDot({ cell }: { cell: WeekDayCell }) {
  if (!cell.scheduled) {
    return (
      <span
        className="inline-flex size-7 items-center justify-center rounded-full bg-raised text-muted"
        title="off"
      >
        <Minus className="size-3.5" aria-hidden />
        <span className="sr-only">off</span>
      </span>
    )
  }
  if (cell.satisfied === true) {
    return (
      <span
        className="inline-flex size-7 items-center justify-center rounded-full bg-good/15 text-good"
        title={cell.value === null ? 'done' : String(cell.value)}
      >
        <Check className="size-3.5" aria-hidden />
        <span className="sr-only">{cell.value === null ? 'done' : String(cell.value)}</span>
      </span>
    )
  }
  if (cell.satisfied === false) {
    return (
      <span className="inline-flex size-7 items-center justify-center rounded-full bg-bad/15 text-bad">
        <X className="size-3.5" aria-hidden />
        <span className="sr-only">missed</span>
      </span>
    )
  }
  return (
    <span className="inline-flex size-7 items-center justify-center rounded-full border border-line text-muted">
      <span className="sr-only">open</span>
    </span>
  )
}
