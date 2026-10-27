import { ChevronLeft, ChevronRight, Plus } from 'lucide-react'
import { type ReactNode, useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { HabitCard, ProgressRing } from '@/components/habits/HabitCard'
import { HabitFormDialog } from '@/components/habits/HabitFormDialog'
import { Segmented } from '@/components/home/Segmented'
import { PageHeader, PageLoading, PageUnavailable } from '@/components/PageState'
import { Button } from '@/components/ui/button'
import { WeekGrid } from '@/components/WeekGrid'
import {
  ApiError,
  getHabitsBoard,
  getHabitsCalendar,
  type HabitsBoard,
  type HabitsCalendar,
  type Period,
} from '@/lib/api'
import { useAsOf } from '@/lib/asOf'
import { longDateLabel, shiftPeriodDate, shortDateLabel } from '@/lib/dates'
import { formatPercent } from '@/lib/format'
import { periodHabits, todayGroups, todaySummary } from '@/lib/habits'
import { flattenHabits, parseHabitPeriod } from '@/lib/habitsSummary'
import { todayIso } from '@/lib/utils'

const GRID_PERIODS: { id: Period; label: string }[] = [
  { id: 'week', label: 'Week' },
  { id: 'month', label: 'Month' },
]

export function HabitsPage() {
  const asOf = useAsOf()
  const [params, setParams] = useSearchParams()
  const search = params.toString()
  const gridPeriod = parseHabitPeriod(params.get('period')) === 'month' ? 'month' : 'week'
  const [board, setBoard] = useState<HabitsBoard | null>(null)
  const [calendar, setCalendar] = useState<HabitsCalendar | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [createOpen, setCreateOpen] = useState(false)

  const refresh = useCallback(async () => {
    const [nextBoard, nextCalendar] = await Promise.all([
      getHabitsBoard(asOf),
      getHabitsCalendar(gridPeriod, asOf),
    ])
    setBoard(nextBoard)
    setCalendar(nextCalendar)
  }, [asOf, gridPeriod])

  useEffect(() => {
    let cancelled = false
    setError(null)
    refresh().catch((caught: unknown) => {
      if (!cancelled) {
        setError(caught instanceof ApiError ? caught.message : 'Could not load habits')
      }
    })
    return () => {
      cancelled = true
    }
  }, [refresh])

  const statuses = useMemo(() => (board === null ? [] : flattenHabits(board)), [board])
  const groups = useMemo(() => todayGroups(statuses), [statuses])
  const periodic = useMemo(() => periodHabits(statuses), [statuses])
  const today = useMemo(() => todaySummary(statuses), [statuses])

  function setParam(key: string, value: string | null) {
    const copy = new URLSearchParams(params)
    if (value === null) copy.delete(key)
    else copy.set(key, value)
    setParams(copy, { replace: true })
  }

  function shiftDay(delta: number) {
    const next = shiftPeriodDate(asOf, 'day', delta)
    setParam('on', next === todayIso() ? null : next)
  }

  if (error !== null) return <PageUnavailable title="Habits" message={error} />
  if (board === null || calendar === null) return <PageLoading />

  const isToday = asOf === todayIso()
  const weekly = periodic.filter((status) => status.period === 'week')
  const monthly = periodic.filter((status) => status.period === 'month')

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageHeader
          title="Habits"
          description={isToday ? `Today · ${longDateLabel(asOf)}` : longDateLabel(asOf)}
          homeLink
        />
        <div className="flex items-center gap-1">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label="Previous day"
            onClick={() => shiftDay(-1)}
          >
            <ChevronLeft className="size-4" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            disabled={isToday}
            onClick={() => setParam('on', null)}
          >
            Today
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            aria-label="Next day"
            disabled={isToday}
            onClick={() => shiftDay(1)}
          >
            <ChevronRight className="size-4" />
          </Button>
          <Button type="button" className="ml-2" onClick={() => setCreateOpen(true)}>
            <Plus className="size-4" aria-hidden />
            New habit
          </Button>
        </div>
      </div>

      {statuses.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-line bg-raised/60 px-4 py-10 text-center">
          <p className="font-medium text-ink">No habits yet</p>
          <p className="mt-1 text-sm text-muted">
            Start with one small thing you want to do (or stop doing) every day.
          </p>
          <Button type="button" className="mt-4" onClick={() => setCreateOpen(true)}>
            <Plus className="size-4" aria-hidden />
            Create your first habit
          </Button>
        </div>
      ) : (
        <>
          <section className="grid gap-3 sm:grid-cols-3" aria-label="Summary">
            <div className="flex items-center gap-3 rounded-2xl border border-line bg-surface p-4">
              <ProgressRing
                value={today.due === 0 ? 0 : today.done / today.due}
                done={today.due > 0 && today.done === today.due}
              />
              <div>
                <p className="text-2xl font-semibold tracking-tight">
                  {today.done}/{today.due}
                </p>
                <p className="text-xs text-muted">{isToday ? 'done today' : 'done that day'}</p>
              </div>
            </div>
            <SummaryStat label="Last 7 days" value={formatPercent(board.completion_7d)} />
            <SummaryStat label="Last 30 days" value={formatPercent(board.completion_30d)} />
          </section>

          {groups.length > 0 ? (
            <section className="flex flex-col gap-5" aria-label="Today">
              {groups.map((group) => (
                <div key={group.id} className="flex flex-col gap-2">
                  <h2 className="text-xs font-semibold tracking-wide text-muted uppercase">
                    {group.label}
                  </h2>
                  <ul className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                    {group.habits.map((status) => (
                      <li key={status.slug}>
                        <HabitCard
                          status={status}
                          asOf={asOf}
                          search={search}
                          onChanged={refresh}
                        />
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </section>
          ) : null}

          {weekly.length > 0 ? (
            <PeriodSection
              title={`This week · ${shortDateLabel(weekly[0].bucket_start ?? asOf)} – ${shortDateLabel(weekly[0].bucket_end ?? asOf)}`}
            >
              {weekly.map((status) => (
                <HabitCard
                  key={status.slug}
                  status={status}
                  asOf={asOf}
                  search={search}
                  onChanged={refresh}
                  layout="row"
                />
              ))}
            </PeriodSection>
          ) : null}
          {monthly.length > 0 ? (
            <PeriodSection title="This month">
              {monthly.map((status) => (
                <HabitCard
                  key={status.slug}
                  status={status}
                  asOf={asOf}
                  search={search}
                  onChanged={refresh}
                  layout="row"
                />
              ))}
            </PeriodSection>
          ) : null}

          <section className="flex min-w-0 flex-col gap-3" aria-label="Overview">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-xs font-semibold tracking-wide text-muted uppercase">
                Overview · {shortDateLabel(calendar.range_start)} –{' '}
                {shortDateLabel(calendar.range_end)}
              </h2>
              <Segmented
                label="Overview range"
                options={GRID_PERIODS}
                value={gridPeriod}
                onChange={(next) => setParam('period', next === 'week' ? null : next)}
              />
            </div>
            <div className="min-w-0 rounded-2xl border border-line bg-surface p-3">
              <WeekGrid habits={calendar.habits} search={search} compact={gridPeriod === 'month'} />
            </div>
          </section>
        </>
      )}

      <HabitFormDialog open={createOpen} onOpenChange={setCreateOpen} onSaved={refresh} />
    </div>
  )
}

function SummaryStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex flex-col justify-center rounded-2xl border border-line bg-surface p-4">
      <p className="text-2xl font-semibold tracking-tight">{value}</p>
      <p className="text-xs text-muted">{label}</p>
    </div>
  )
}

function PeriodSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="flex flex-col gap-2" aria-label={title}>
      <h2 className="text-xs font-semibold tracking-wide text-muted uppercase">{title}</h2>
      <div className="grid gap-3 md:grid-cols-2">{children}</div>
    </section>
  )
}
