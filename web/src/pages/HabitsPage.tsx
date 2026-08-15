import { ChevronLeft, ChevronRight, Plus } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { HabitCreateDialog } from '@/components/habits/HabitCreateDialog'
import {
  EmptyState,
  PageHeader,
  PageLoading,
  PageUnavailable,
  ProgressBar,
} from '@/components/PageState'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { WeekGrid } from '@/components/WeekGrid'
import {
  ApiError,
  getHabitsBoard,
  getHabitsCalendar,
  type HabitStatus,
  type HabitsBoard,
  type HabitsCalendar,
  listMetrics,
  logEntry,
  type Metric,
  type Period,
} from '@/lib/api'
import { useAsOf, useShell } from '@/lib/asOf'
import { shiftPeriodDate, shortDateLabel } from '@/lib/dates'
import { formatComparator, formatPercent } from '@/lib/format'
import {
  bucketProgress,
  flattenHabits,
  HABIT_PERIOD_META,
  parseHabitPeriod,
} from '@/lib/habitsSummary'
import { cn, todayIso } from '@/lib/utils'

const VIEW_PERIODS: { id: Period; label: string }[] = [
  { id: 'day', label: 'Day' },
  { id: 'week', label: 'Week' },
  { id: 'month', label: 'Month' },
]

export function HabitsPage() {
  const asOf = useAsOf()
  const { openLog } = useShell()
  const [params, setParams] = useSearchParams()
  const search = params.toString()
  const period = parseHabitPeriod(params.get('period'))
  const [board, setBoard] = useState<HabitsBoard | null>(null)
  const [calendar, setCalendar] = useState<HabitsCalendar | null>(null)
  const [metrics, setMetrics] = useState<Metric[]>([])
  const [error, setError] = useState<string | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [pending, setPending] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    const [nextBoard, nextCalendar, nextMetrics] = await Promise.all([
      getHabitsBoard(asOf),
      getHabitsCalendar(period, asOf),
      listMetrics(),
    ])
    setBoard(nextBoard)
    setCalendar(nextCalendar)
    setMetrics(nextMetrics)
  }, [asOf, period])

  useEffect(() => {
    let cancelled = false
    setError(null)
    refresh().catch((caught: unknown) => {
      if (!cancelled) {
        setError(caught instanceof ApiError ? caught.message : 'Could not load habits')
        setBoard(null)
        setCalendar(null)
      }
    })
    return () => {
      cancelled = true
    }
  }, [refresh])

  const metricBySlug = useMemo(
    () => Object.fromEntries(metrics.map((metric) => [metric.slug, metric])),
    [metrics],
  )
  const habits = useMemo(() => (board === null ? [] : flattenHabits(board)), [board])

  function setPeriod(next: Period) {
    const copy = new URLSearchParams(params)
    if (next === 'week') copy.delete('period')
    else copy.set('period', next)
    setParams(copy, { replace: true })
  }

  function shift(delta: number) {
    const copy = new URLSearchParams(params)
    const next = shiftPeriodDate(asOf, period, delta)
    if (next === todayIso()) copy.delete('on')
    else copy.set('on', next)
    setParams(copy, { replace: true })
  }

  async function onLog(habit: HabitStatus) {
    if (habit.satisfied) return
    const metric = metricBySlug[habit.metric_slug]
    if (metric?.value_type !== 'bool') {
      openLog()
      return
    }
    setPending(habit.slug)
    try {
      await logEntry({ metric: habit.metric_slug, occurred_on: asOf })
      await refresh()
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Could not log')
    } finally {
      setPending(null)
    }
  }

  if (error !== null) {
    return <PageUnavailable title="Habits" message={error} />
  }
  if (board === null || calendar === null) return <PageLoading />

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageHeader
          title="Habits"
          description={`${shortDateLabel(calendar.range_start)} – ${shortDateLabel(calendar.range_end)}. Recurring commitments, not one-off tasks.`}
          homeLink
        />
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex rounded-full border border-line bg-surface p-1" role="tablist">
            {VIEW_PERIODS.map((item) => (
              <button
                key={item.id}
                type="button"
                role="tab"
                aria-selected={period === item.id}
                className={cn(
                  'rounded-full px-3 py-1 text-sm motion-safe:transition-colors',
                  period === item.id ? 'bg-goal/20 text-ink' : 'text-muted hover:text-ink',
                )}
                onClick={() => setPeriod(item.id)}
              >
                {item.label}
              </button>
            ))}
          </div>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => shift(-1)}
            aria-label="Previous"
          >
            <ChevronLeft className="size-4" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => shift(1)}
            aria-label="Next"
          >
            <ChevronRight className="size-4" />
          </Button>
          <Button type="button" onClick={() => setCreateOpen(true)}>
            <Plus className="size-4" aria-hidden />
            New Habit
          </Button>
        </div>
      </div>
      <p className="font-mono text-xs text-muted">
        {board.satisfied}/{board.scheduled} scheduled done
        {board.fraction !== null ? ` · ${formatPercent(board.fraction)}` : ''}
      </p>
      {habits.length === 0 ? (
        <EmptyState
          title="No habits yet"
          hint="Define a recurring commitment over a metric. Completing a task will not move a streak."
        />
      ) : (
        <>
          <section className="rounded-2xl border border-line bg-raised/40 p-3">
            <WeekGrid habits={calendar.habits} search={search} compact={period === 'month'} />
          </section>
          <ul className="grid gap-3 lg:grid-cols-2">
            {habits.map((habit) => (
              <li key={habit.slug}>
                <HabitCard
                  habit={habit}
                  search={search}
                  isBool={metricBySlug[habit.metric_slug]?.value_type === 'bool'}
                  pending={pending === habit.slug}
                  onLog={() => onLog(habit)}
                />
              </li>
            ))}
          </ul>
        </>
      )}
      <HabitCreateDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        metrics={metrics}
        onCreated={refresh}
      />
    </div>
  )
}

function HabitCard({
  habit,
  search,
  isBool,
  pending,
  onLog,
}: {
  habit: HabitStatus
  search: string
  isBool: boolean
  pending: boolean
  onLog: () => void
}) {
  const progress = bucketProgress(habit.current_value, habit.target_value)
  const logLabel = habit.satisfied ? 'Done' : isBool ? 'Mark done' : 'Log value'
  return (
    <article className="flex flex-col gap-4 rounded-2xl border border-line bg-surface p-4 shadow-[var(--shadow-card)]">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <Link
            to={{ pathname: `/habit/${habit.slug}`, search }}
            className="text-lg font-semibold tracking-tight hover:underline"
          >
            {habit.name}
          </Link>
          <p className="mt-1 font-mono text-xs text-muted">
            {formatComparator(habit.comparator)} {habit.target_value} · {habit.metric_slug}
          </p>
        </div>
        <div className="flex flex-wrap justify-end gap-1">
          <Badge>{HABIT_PERIOD_META[habit.period].label}</Badge>
          <Badge tone={habit.satisfied ? 'good' : habit.scheduled ? 'warn' : 'default'}>
            {habit.satisfied ? 'done' : habit.scheduled ? 'open' : 'off'}
          </Badge>
        </div>
      </div>
      <dl className="grid grid-cols-2 gap-4 sm:grid-cols-3">
        <Stat label="Current streak" value={String(habit.current_streak)} />
        <Stat label="Longest" value={String(habit.longest_streak)} />
        <div className="col-span-2 sm:col-span-1">
          <dt className="text-xs text-muted">Adherence</dt>
          <dd className="mt-1 font-mono text-xl">{formatPercent(habit.adherence)}</dd>
          <div className="mt-2">
            <ProgressBar value={habit.adherence} />
          </div>
        </div>
      </dl>
      <div>
        <p className="text-xs text-muted">This bucket</p>
        <p className="mt-1 font-mono text-xl">
          {habit.current_value === null ? '—' : habit.current_value}
          <span className="text-sm text-muted">
            {' '}
            / {habit.target_value} {formatComparator(habit.comparator)}
          </span>
        </p>
        <div className="mt-2">
          <ProgressBar value={progress} />
        </div>
      </div>
      {habit.scheduled && (
        <Button type="button" disabled={pending || habit.satisfied} onClick={onLog}>
          {logLabel}
        </Button>
      )}
    </article>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="mt-1 font-mono text-xl">{value}</dd>
    </div>
  )
}
