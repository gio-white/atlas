import { Check, ListChecks, Minus, SkipForward, X } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'

import { LogForm } from '@/components/LogForm'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  ApiError,
  type HabitsCalendar,
  type Metric,
  setHabitDay,
  type WeekDayCell,
  type WeekHabit,
} from '@/lib/api'
import { shortDateLabel, weekdayLabel } from '@/lib/dates'
import { frequencyLabel } from '@/lib/habits'
import { type HabitCellState, habitCellState, habitWeekSummary } from '@/lib/home'
import { cn } from '@/lib/utils'

export function HabitsWeekCard({
  calendar,
  metrics,
  asOf,
  search,
  onChanged,
}: {
  calendar: HabitsCalendar | null
  metrics: Metric[]
  asOf: string
  search: string
  onChanged: () => Promise<void>
}) {
  const [pending, setPending] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [logTarget, setLogTarget] = useState<{ habit: WeekHabit; day: string } | null>(null)
  const metricBySlug = new Map(metrics.map((metric) => [metric.slug, metric]))
  const habits = calendar?.habits ?? []
  const headings = habits[0]?.days ?? []
  const scroller = useRef<HTMLDivElement>(null)

  // On a narrow screen the day columns scroll; bring today into view instead of Monday.
  useEffect(() => {
    const box = scroller.current
    if (calendar === null || !box) return
    const today = box.querySelector<HTMLElement>(`[data-day="${asOf}"]`)
    if (!today) return
    const overflow = today.offsetLeft + today.offsetWidth + 4 - box.clientWidth
    if (overflow > 0) box.scrollLeft = overflow
  }, [calendar, asOf])

  async function onCell(habit: WeekHabit, cell: WeekDayCell, state: HabitCellState) {
    if (state === 'off' || state === 'future') return
    if (metricBySlug.get(habit.metric_slug)?.value_type !== 'bool') {
      setLogTarget({ habit, day: cell.day })
      return
    }
    const key = `${habit.slug}:${cell.day}`
    setPending(key)
    setError(null)
    try {
      await setHabitDay(habit.slug, cell.day, state !== 'done', asOf)
      await onChanged()
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Could not update habit')
    } finally {
      setPending(null)
    }
  }

  return (
    <Card className="flex flex-col">
      <CardHeader>
        <div>
          <CardTitle className="flex items-center gap-2 text-base">
            <ListChecks className="size-4 text-iris" aria-hidden />
            Habits
          </CardTitle>
          <CardDescription>
            {calendar === null
              ? 'This week'
              : `Week of ${shortDateLabel(calendar.range_start)} · tap a day to confirm`}
          </CardDescription>
        </div>
        <Link
          to={{ pathname: '/habit', search }}
          className="text-xs font-medium text-iris hover:underline"
        >
          View all
        </Link>
      </CardHeader>
      {calendar === null ? (
        <p className="text-sm text-muted">Habits are unavailable right now.</p>
      ) : habits.length === 0 ? (
        <p className="text-sm text-muted">
          No habits scheduled. Define one on the{' '}
          <Link to={{ pathname: '/habit', search }} className="underline hover:text-ink">
            Habits
          </Link>{' '}
          board.
        </p>
      ) : (
        <div ref={scroller} className="-mx-1 overflow-x-auto px-1">
          <table className="w-full min-w-[24rem] border-collapse text-sm">
            <thead>
              <tr>
                <th className="sticky left-0 z-10 bg-surface pb-2 pr-2 text-left text-xs font-medium text-muted">
                  Habit
                </th>
                {headings.map((cell) => (
                  <th
                    key={cell.day}
                    data-day={cell.day}
                    className={cn(
                      'px-0.5 pb-2 text-center text-[11px] font-medium',
                      cell.day === asOf ? 'text-ink' : 'text-muted',
                    )}
                  >
                    {weekdayLabel(cell.day).slice(0, 2)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {habits.map((habit) => (
                <tr key={habit.slug} className="border-t border-line">
                  <td className="sticky left-0 z-10 max-w-36 bg-surface py-2 pr-2 sm:max-w-48">
                    <Link
                      to={{ pathname: `/habit/${habit.slug}`, search }}
                      className="block truncate font-medium hover:underline"
                    >
                      {habit.name}
                    </Link>
                    <span className="block truncate text-xs text-muted">
                      {habit.period === 'day' ? `${frequencyLabel(habit)} · ` : ''}
                      {habitWeekSummary(habit, asOf)}
                    </span>
                  </td>
                  {habit.days.map((cell) => {
                    const state = habitCellState(habit, cell, asOf)
                    return (
                      <td key={cell.day} className="px-0.5 py-2 text-center">
                        <HabitCell
                          state={state}
                          today={cell.day === asOf}
                          pending={pending === `${habit.slug}:${cell.day}`}
                          label={`${habit.name} ${weekdayLabel(cell.day)} ${cell.day.slice(8)}`}
                          onClick={() => void onCell(habit, cell, state)}
                        />
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {error !== null && (
        <p className="mt-2 text-xs text-bad" role="alert">
          {error}
        </p>
      )}
      <Dialog open={logTarget !== null} onOpenChange={(open) => !open && setLogTarget(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{logTarget?.habit.name}</DialogTitle>
            <DialogDescription>
              Log a value for {logTarget === null ? '' : shortDateLabel(logTarget.day)}.
            </DialogDescription>
          </DialogHeader>
          {logTarget !== null && (
            <LogForm
              metrics={metrics.filter((metric) => metric.slug === logTarget.habit.metric_slug)}
              occurredOn={logTarget.day}
              initialMetric={logTarget.habit.metric_slug}
              onLogged={async () => {
                setLogTarget(null)
                await onChanged()
              }}
            />
          )}
        </DialogContent>
      </Dialog>
    </Card>
  )
}

const CELL_STYLE: Record<HabitCellState, string> = {
  done: 'bg-good/15 text-good hover:bg-good/25',
  missed: 'bg-bad/10 text-bad hover:bg-bad/20',
  open: 'border border-line text-muted hover:border-good hover:text-good',
  future: 'border border-dashed border-line text-muted',
  skipped: 'bg-warn/10 text-warn',
  off: 'bg-raised text-muted',
}

const CELL_LABEL: Record<HabitCellState, string> = {
  done: 'done',
  missed: 'missed',
  open: 'not yet',
  future: 'upcoming',
  skipped: 'skipped',
  off: 'not scheduled',
}

function HabitCell({
  state,
  today,
  pending,
  label,
  onClick,
}: {
  state: HabitCellState
  today: boolean
  pending: boolean
  label: string
  onClick: () => void
}) {
  const interactive = state !== 'off' && state !== 'future' && state !== 'skipped'
  return (
    <button
      type="button"
      className={cn(
        'inline-flex size-8 items-center justify-center rounded-full disabled:cursor-default',
        CELL_STYLE[state],
        today && 'ring-2 ring-iris/40',
        pending && 'opacity-50',
      )}
      disabled={!interactive || pending}
      aria-pressed={interactive ? state === 'done' : undefined}
      aria-label={`${label}: ${CELL_LABEL[state]}`}
      title={CELL_LABEL[state]}
      onClick={onClick}
    >
      {state === 'done' && <Check className="size-4" aria-hidden />}
      {state === 'missed' && <X className="size-3.5" aria-hidden />}
      {state === 'off' && <Minus className="size-3.5" aria-hidden />}
      {state === 'skipped' && <SkipForward className="size-3.5" aria-hidden />}
    </button>
  )
}
