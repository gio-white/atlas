import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { HabitWeekRow, WEEK_CELLS } from '@/components/habits/HabitWeekRow'
import { useDayActions } from '@/components/habits/useDayActions'
import { PageError, PageHeader, PageLoading } from '@/components/PageState'
import { Button } from '@/components/ui/button'
import {
  ApiError,
  getHabitsWeek,
  type Habit,
  type HabitFreeze,
  type HabitsWeek,
  listFreezes,
  listHabits,
} from '@/lib/api'
import { useAsOf } from '@/lib/asOf'
import { parseIsoDate } from '@/lib/dates'
import { dayGroups, keptFigure, ruleSummary, weekOfLabel } from '@/lib/habits'
import { weekSteps } from '@/lib/thisWeek'
import { cn, todayIso } from '@/lib/utils'

type Loaded = { view: HabitsWeek; freezes: HabitFreeze[]; archived: Habit[] }

/**
 * Habits → Week (habits brief §8): every active habit's Monday to Sunday, grouped like the Day
 * tab, with Habits kept this week and last week, then the archived habits. The week is the one
 * holding the shell's `?on=` date; ‹ › move a whole week.
 */
export function HabitsWeekPage() {
  const asOf = useAsOf()
  const [params, setParams] = useSearchParams()
  const [loaded, setLoaded] = useState<Loaded | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async (day: string): Promise<Loaded> => {
    const [view, freezes, habits] = await Promise.all([
      getHabitsWeek(day),
      listFreezes(),
      listHabits(),
    ])
    return { view, freezes, archived: habits.filter((habit) => habit.archived_at !== null) }
  }, [])

  useEffect(() => {
    let cancelled = false
    load(asOf)
      .then((next) => {
        if (!cancelled) {
          setLoaded(next)
          setError(null)
        }
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setError(caught instanceof ApiError ? caught.message : 'Couldn’t load your habits.')
        }
      })
    return () => {
      cancelled = true
    }
  }, [asOf, load])

  const actions = useDayActions(async () => {
    setLoaded(await load(asOf))
  })

  if (error !== null) return <PageError message={error} />
  if (loaded === null) return <PageLoading />

  const { view, freezes, archived } = loaded
  const today = todayIso()
  const steps = weekSteps(view.week_start, today)
  const on = params.get('on')
  const search = on === null ? '' : new URLSearchParams({ on }).toString()
  const groups = dayGroups(view.rows)
  const weekDays = view.rows[0]?.days.map((result) => result.day) ?? []

  function goTo(day: string | null) {
    const next = new URLSearchParams(params)
    if (day === null) next.delete('on')
    else next.set('on', day)
    setParams(next)
  }

  return (
    <div className="flex flex-col gap-5">
      <PageHeader title="Week" tab />
      <div className="flex items-center justify-between gap-3">
        <h2 className="text-base font-semibold text-ink">{weekOfLabel(view.week_start)}</h2>
        <nav aria-label="Week" className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="size-11"
            aria-label="Previous week"
            onClick={() => goTo(steps.previous)}
          >
            <ChevronLeft className="size-4" aria-hidden />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className="size-11"
            aria-label="Next week"
            disabled={steps.next === undefined}
            onClick={() => steps.next !== undefined && goTo(steps.next)}
          >
            <ChevronRight className="size-4" aria-hidden />
          </Button>
        </nav>
      </div>

      {actions.error !== null && <PageError message={actions.error} />}

      {view.rows.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-line bg-raised/70 px-4 py-8 text-center">
          <p className="font-medium text-ink">No habits yet</p>
        </div>
      ) : (
        <div className="flex flex-col gap-4">
          <div
            aria-hidden
            className="sticky top-0 z-10 -mb-2 flex bg-canvas/95 py-1 backdrop-blur md:gap-3"
          >
            <span className="hidden md:block md:flex-1" />
            <div className={WEEK_CELLS}>
              {weekDays.map((day) => (
                <span
                  key={day}
                  className={cn(
                    'flex flex-col items-center text-xs text-muted',
                    day === today && 'font-semibold text-accent',
                  )}
                >
                  <span>
                    {parseIsoDate(day).toLocaleDateString('en-GB', { weekday: 'short' }).charAt(0)}
                  </span>
                  <span className="tabular-nums">{parseIsoDate(day).getDate()}</span>
                </span>
              ))}
            </div>
            <span className="hidden md:block md:w-40" />
          </div>
          {groups.map((group) => (
            <section key={group.id} aria-label={group.label ?? 'Habits'} className="flex flex-col">
              {group.label !== null && (
                <h3 className="px-1 text-xs font-semibold tracking-wide text-muted uppercase">
                  {group.label}
                </h3>
              )}
              <ul className="flex flex-col divide-y divide-line md:divide-y-0">
                {group.rows.map((row) => (
                  <HabitWeekRow
                    key={row.habit.slug}
                    row={row}
                    freezes={freezes}
                    search={search}
                    isBusy={(day) => actions.isBusy(row.habit.slug, day)}
                    onToggle={(result) => actions.toggle(row.habit.slug, result)}
                    onAction={(day, action) => actions.act(row.habit.slug, day, action, freezes)}
                  />
                ))}
              </ul>
            </section>
          ))}
        </div>
      )}

      <p className="flex flex-wrap items-baseline gap-x-2 border-t border-line pt-4 text-sm text-muted">
        <span>
          Habits kept this week{' '}
          <span className="font-semibold text-ink tabular-nums">{keptFigure(view.kept)}</span>
        </span>
        <span aria-hidden>·</span>
        <span>
          last week <span className="tabular-nums">{keptFigure(view.kept_last_week)}</span>
        </span>
      </p>

      {archived.length > 0 && (
        <section aria-label="Archived" className="flex flex-col gap-2">
          <h3 className="px-1 text-xs font-semibold tracking-wide text-muted uppercase">
            Archived
          </h3>
          <ul className="flex flex-col">
            {archived.map((habit) => (
              <li key={habit.slug}>
                <Link
                  to={{ pathname: `/habit/${habit.slug}`, search }}
                  className="flex min-h-11 flex-col justify-center rounded-xl px-1 py-1.5 hover:bg-raised focus-visible:ring-2 focus-visible:ring-accent focus-visible:outline-none"
                >
                  <span className="font-medium text-muted">{habit.name}</span>
                  <span className="text-xs text-muted">{ruleSummary(habit)}</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  )
}
