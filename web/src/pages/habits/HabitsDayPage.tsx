import { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { HabitDayList } from '@/components/habits/HabitDayList'
import { NewHabitButton } from '@/components/habits/NewHabitButton'
import { useDayActions } from '@/components/habits/useDayActions'
import { WeekStrip } from '@/components/habits/WeekStrip'
import { PageError, PageHeader, PageLoading } from '@/components/PageState'
import {
  ApiError,
  getHabitsDay,
  type HabitFreeze,
  type HabitsDay,
  listFreezes,
  listHabits,
} from '@/lib/api'
import { useAsOf } from '@/lib/asOf'
import { dayCountLabel, dayHeading, HABITS_CHANGED_EVENT, stripSteps } from '@/lib/habits'
import { todayIso } from '@/lib/utils'

type Loaded = { view: HabitsDay; freezes: HabitFreeze[]; hasHabits: boolean }

function message(caught: unknown, fallback: string): string {
  return caught instanceof ApiError ? caught.message : fallback
}

/**
 * Habits → Day (habits brief §7): the selected day's scheduled habits by time of day, under a
 * Monday–Sunday strip. The day is the shell's `?on=` date; picking a day in the strip moves it.
 * Ticking, the row menu's answers, and freezes write through the API, then the day reloads.
 */
export function HabitsDayPage() {
  const asOf = useAsOf()
  const [params, setParams] = useSearchParams()
  const [loaded, setLoaded] = useState<Loaded | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async (day: string): Promise<Loaded> => {
    const [view, freezes, habits] = await Promise.all([
      getHabitsDay(day),
      listFreezes(),
      listHabits(),
    ])
    return { view, freezes, hasHabits: habits.some((habit) => habit.archived_at === null) }
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
        if (!cancelled) setError(message(caught, 'Couldn’t load your habits.'))
      })
    return () => {
      cancelled = true
    }
  }, [asOf, load])

  useEffect(() => {
    function refresh() {
      load(asOf)
        .then(setLoaded)
        .catch(() => undefined)
    }
    window.addEventListener(HABITS_CHANGED_EVENT, refresh)
    return () => window.removeEventListener(HABITS_CHANGED_EVENT, refresh)
  }, [asOf, load])

  const actions = useDayActions(async () => {
    setLoaded(await load(asOf))
  })

  if (error !== null) return <PageError message={error} />
  if (loaded === null) return <PageLoading />

  const { view, freezes, hasHabits } = loaded
  const today = todayIso()
  const steps = stripSteps(view.day, view.week[0]?.day ?? view.day, today)

  function select(day: string) {
    const next = new URLSearchParams(params)
    if (day === today) next.delete('on')
    else next.set('on', day)
    setParams(next)
  }

  return (
    <div className="flex flex-col gap-5">
      <PageHeader title="Day" tab />
      <div className="-mx-2 border-b border-line pb-3 md:mx-0">
        <WeekStrip
          week={view.week}
          selected={view.day}
          today={today}
          onSelect={select}
          previous={steps.previous}
          next={steps.next}
        />
      </div>

      <div className="flex items-baseline justify-between gap-3">
        <h2 className="text-base font-semibold text-ink">{dayHeading(view.day)}</h2>
        {view.total > 0 && (
          <p className="text-sm text-muted tabular-nums">{dayCountLabel(view.done, view.total)}</p>
        )}
      </div>

      {actions.error !== null && <PageError message={actions.error} />}

      {!hasHabits ? (
        <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-line bg-raised/70 px-4 py-8 text-center">
          <div className="flex flex-col gap-1">
            <p className="font-medium text-ink">No habits yet</p>
            <p className="text-sm text-muted">Habits you add show here, day by day.</p>
          </div>
          <NewHabitButton size="sm" />
        </div>
      ) : view.rows.length === 0 ? (
        <p className="text-sm text-muted">No habits scheduled on this day.</p>
      ) : (
        <HabitDayList view={view} freezes={freezes} actions={actions} />
      )}
    </div>
  )
}
