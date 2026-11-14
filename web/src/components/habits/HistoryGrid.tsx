import { Snowflake } from 'lucide-react'

import type { HabitPeriod, HabitPeriodState } from '@/lib/api'
import { shiftPeriodDate } from '@/lib/dates'
import { historyWeeks, mondayOf, periodLabel, periodStateLabel, shortDay } from '@/lib/habits'
import { cn } from '@/lib/utils'

/** Every other weekday is named down the calendar's side: Mon, Wed, Fri, Sun. */
const WEEKDAY_ROWS = [
  { id: 'mon', letter: 'M' },
  { id: 'tue', letter: '' },
  { id: 'wed', letter: 'W' },
  { id: 'thu', letter: '' },
  { id: 'fri', letter: 'F' },
  { id: 'sat', letter: '' },
  { id: 'sun', letter: 'S' },
]

const STATE_ORDER: HabitPeriodState[] = ['kept', 'missed', 'running', 'waiting', 'frozen']

/** A square's look by its period's state (habits brief §13): kept in the success green, missed
 * a quiet grey (never red), running an accent outline, waiting a dashed grey outline, frozen a
 * grey snowflake, upcoming a faint outline. */
function Square({
  state,
  label,
  size = 'size-4',
}: {
  state: HabitPeriodState | null
  label?: string
  size?: string
}) {
  return (
    <span
      title={label}
      className={cn(
        size,
        'flex items-center justify-center rounded-[4px]',
        state === 'kept' && 'bg-good',
        state === 'missed' && 'bg-muted/30',
        state === 'running' && 'border-2 border-accent',
        state === 'waiting' && 'border border-dashed border-muted',
        state === 'frozen' && 'bg-raised text-muted',
        state === 'upcoming' && 'border border-line',
      )}
    >
      {state === 'frozen' && <Snowflake className="size-3" aria-hidden />}
    </span>
  )
}

/**
 * The last 12 weeks of a habit (habits brief §8): for a habit judged per day, a calendar of one
 * square per day (columns are Monday–Sunday weeks from the habit's first week; days it was not
 * scheduled stay empty); for a weekly or monthly habit, one square per period. A legend names
 * the states shown.
 */
export function HistoryGrid({ history, asOf }: { history: HabitPeriod[]; asOf: string }) {
  const daily = history.every((period) => period.period === 'day')
  const judged = history.filter((period) => period.state === 'kept' || period.state === 'missed')
  const kept = judged.filter((period) => period.state === 'kept').length
  const unit = daily ? 'days' : history[0]?.period === 'month' ? 'months' : 'weeks'
  const summary =
    judged.length === 0
      ? 'Nothing judged yet in the last 12 weeks.'
      : `${kept} of ${judged.length} ${unit} kept in the last 12 weeks.`
  const states = STATE_ORDER.filter((state) => history.some((period) => period.state === state))

  if (history.length === 0) {
    return <p className="text-sm text-muted">No history yet.</p>
  }

  return (
    <div className="flex flex-col gap-3">
      <p className="sr-only">{summary}</p>
      {daily ? (
        <div className="flex gap-2" aria-hidden>
          <div className="flex flex-col gap-1 text-[10px] leading-4 text-muted">
            {WEEKDAY_ROWS.map(({ id, letter }) => (
              <span key={id} className="h-4">
                {letter}
              </span>
            ))}
          </div>
          <div className="flex gap-1 overflow-x-auto">
            {historyWeeks(history, firstMonday(history, asOf), asOf).map((column) => (
              <div key={column[0].day} className="flex flex-col gap-1">
                {column.map(({ day, period }) => (
                  <Square
                    key={day}
                    state={period?.state ?? null}
                    label={period === null ? shortDay(day) : periodLabel(period)}
                  />
                ))}
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="flex w-fit max-w-full flex-col gap-1" aria-hidden>
          <div className="flex flex-wrap gap-1.5">
            {history.map((period) => (
              <Square
                key={`${period.period}-${period.start}`}
                state={period.state}
                label={periodLabel(period)}
                size="size-6"
              />
            ))}
          </div>
          {history.length > 1 && (
            <div className="flex justify-between gap-4 text-xs text-muted">
              <span>{shortDay(history[0].start)}</span>
              <span>{shortDay(history[history.length - 1].start)}</span>
            </div>
          )}
        </div>
      )}
      <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted" aria-label="Legend">
        {states.map((state) => (
          <li key={state} className="inline-flex items-center gap-1.5">
            <Square state={state} size="size-3" />
            {periodStateLabel({ period: daily ? 'day' : 'week', state })}
          </li>
        ))}
      </ul>
    </div>
  )
}

/** The calendar's first column: 12 weeks back, or the week of the first period if later. */
function firstMonday(history: HabitPeriod[], asOf: string): string {
  const twelveWeeks = shiftPeriodDate(mondayOf(asOf), 'week', -11)
  const first = history[0] === undefined ? twelveWeeks : mondayOf(history[0].start)
  return first > twelveWeeks ? first : twelveWeeks
}
