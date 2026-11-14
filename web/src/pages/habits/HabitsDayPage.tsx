import { useCallback, useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'

import { HabitDayRow } from '@/components/habits/HabitDayRow'
import { WeekStrip } from '@/components/habits/WeekStrip'
import { PageError, PageLoading } from '@/components/PageState'
import {
  ApiError,
  clearHabitDay,
  createFreeze,
  deleteFreeze,
  getHabitsDay,
  type HabitFreeze,
  type HabitsDay,
  listFreezes,
  listHabits,
  type HabitDayRow as Row,
  setHabitDay,
} from '@/lib/api'
import { useAsOf } from '@/lib/asOf'
import {
  dayCountLabel,
  dayGroups,
  dayHeading,
  ownDayFreeze,
  type RowAction,
  stripSteps,
} from '@/lib/habits'
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
  const navigate = useNavigate()
  const [loaded, setLoaded] = useState<Loaded | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [busy, setBusy] = useState<string | null>(null)

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

  async function act(row: Row, run: () => Promise<unknown>) {
    setBusy(row.habit.slug)
    setActionError(null)
    try {
      await run()
      setLoaded(await load(view.day))
    } catch (caught: unknown) {
      setActionError(message(caught, 'Couldn’t save that. Try again.'))
    } finally {
      setBusy(null)
    }
  }

  function toggle(row: Row) {
    const { slug } = row.habit
    void act(row, () =>
      row.result.status === 'done'
        ? clearHabitDay(slug, view.day)
        : setHabitDay(slug, view.day, 'done'),
    )
  }

  function runAction(row: Row, action: RowAction) {
    const { slug } = row.habit
    const day = view.day
    switch (action) {
      case 'mark_done':
        return void act(row, () => setHabitDay(slug, day, 'done'))
      case 'mark_not_done':
        return void act(row, () => setHabitDay(slug, day, 'not_done'))
      case 'use_data':
        return void act(row, () => clearHabitDay(slug, day))
      case 'freeze':
        return void act(row, () => createFreeze({ habit: slug, start_on: day, end_on: day }))
      case 'unfreeze': {
        const freeze = ownDayFreeze(freezes, slug, day)
        if (freeze !== undefined) void act(row, () => deleteFreeze(freeze.id))
        return
      }
      case 'open':
        return navigate({ pathname: `/habit/${slug}`, search: params.toString() })
    }
  }

  const groups = dayGroups(view.rows)

  return (
    <div className="flex flex-col gap-5">
      <h1 className="text-2xl font-semibold tracking-tight text-ink">Habits</h1>

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

      {actionError !== null && <PageError message={actionError} />}

      {!hasHabits ? (
        <div className="rounded-2xl border border-dashed border-line bg-raised/70 px-4 py-8 text-center">
          <p className="font-medium text-ink">No habits yet</p>
        </div>
      ) : groups.length === 0 ? (
        <p className="text-sm text-muted">No habits scheduled on this day.</p>
      ) : (
        groups.map((group) => (
          <section
            key={group.id}
            aria-label={group.label ?? 'Habits'}
            className="flex flex-col gap-1"
          >
            {group.label !== null && (
              <h3 className="px-1 text-xs font-semibold tracking-wide text-muted uppercase">
                {group.label}
              </h3>
            )}
            <ul className="-mx-2 flex flex-col md:mx-0">
              {group.rows.map((row) => (
                <HabitDayRow
                  key={row.habit.slug}
                  row={row}
                  busy={busy === row.habit.slug}
                  canUnfreeze={ownDayFreeze(freezes, row.habit.slug, view.day) !== undefined}
                  onToggle={() => toggle(row)}
                  onAction={(action) => runAction(row, action)}
                />
              ))}
            </ul>
          </section>
        ))
      )}
    </div>
  )
}
