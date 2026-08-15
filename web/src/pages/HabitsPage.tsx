import { Flame, Plus } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { HabitCreateDialog } from '@/components/habits/HabitCreateDialog'
import { EmptyState, PageHeader, PageLoading, PageUnavailable } from '@/components/PageState'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  ApiError,
  getHabitsBoard,
  type HabitStatus,
  type HabitsBoard,
  listMetrics,
  logEntry,
  type Metric,
  type Period,
} from '@/lib/api'
import { useAsOf, useShell } from '@/lib/asOf'
import { formatComparator, formatPercent } from '@/lib/format'
import { HABIT_PERIOD_META, HABIT_PERIODS } from '@/lib/habitsSummary'
import { cn } from '@/lib/utils'

const FILTERS: { id: 'all' | Period; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'day', label: 'Daily' },
  { id: 'week', label: 'Weekly' },
  { id: 'month', label: 'Monthly' },
]

export function HabitsPage() {
  const asOf = useAsOf()
  const { openLog } = useShell()
  const [params] = useSearchParams()
  const search = params.toString()
  const [board, setBoard] = useState<HabitsBoard | null>(null)
  const [metrics, setMetrics] = useState<Metric[]>([])
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<'all' | Period>('all')
  const [createOpen, setCreateOpen] = useState(false)
  const [createPeriod, setCreatePeriod] = useState<Period>('day')
  const [pending, setPending] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    const [nextBoard, nextMetrics] = await Promise.all([getHabitsBoard(asOf), listMetrics()])
    setBoard(nextBoard)
    setMetrics(nextMetrics)
  }, [asOf])

  useEffect(() => {
    let cancelled = false
    setError(null)
    refresh().catch((caught: unknown) => {
      if (!cancelled) {
        setError(caught instanceof ApiError ? caught.message : 'Could not load habits')
        setBoard(null)
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
  if (board === null) return <PageLoading />

  const columns = HABIT_PERIODS.filter((period) => filter === 'all' || filter === period)
  const empty = board.day.length + board.week.length + board.month.length === 0

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageHeader
          title="Habits"
          description="Recurring commitments over a metric. Not one-off tasks — streaks come from what you logged."
          homeLink
        />
        <div className="flex flex-wrap gap-2">
          <Button asChild variant="outline">
            <Link to={{ pathname: '/week', search }}>Week grid</Link>
          </Button>
          <Button
            type="button"
            onClick={() => {
              setCreatePeriod(filter === 'all' ? 'day' : filter)
              setCreateOpen(true)
            }}
          >
            <Plus className="size-4" aria-hidden />
            New Habit
          </Button>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex flex-wrap gap-2" role="tablist" aria-label="Habit period">
          {FILTERS.map((item) => (
            <button
              key={item.id}
              type="button"
              role="tab"
              aria-selected={filter === item.id}
              className={cn(
                'rounded-full border px-3 py-1.5 text-sm motion-safe:transition-colors',
                filter === item.id
                  ? 'border-goal bg-goal/15 text-ink'
                  : 'border-line bg-surface text-muted hover:bg-raised',
              )}
              onClick={() => setFilter(item.id)}
            >
              {item.label}
            </button>
          ))}
        </div>
        <p className="ml-auto font-mono text-xs text-muted">
          {board.satisfied}/{board.scheduled} scheduled done
          {board.fraction !== null ? ` · ${formatPercent(board.fraction)}` : ''}
        </p>
      </div>
      {empty ? (
        <EmptyState
          title="No habits yet"
          hint="Define a recurring commitment over a metric. Completing a task will not move a streak."
        />
      ) : (
        <div className="flex gap-4 overflow-x-auto pb-2">
          {columns.map((period) => (
            <PeriodColumn
              key={period}
              period={period}
              habits={board[period]}
              search={search}
              pending={pending}
              onLog={onLog}
              onAdd={() => {
                setCreatePeriod(period)
                setCreateOpen(true)
              }}
            />
          ))}
        </div>
      )}
      <HabitCreateDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        metrics={metrics}
        defaultPeriod={createPeriod}
        onCreated={refresh}
      />
    </div>
  )
}

function PeriodColumn({
  period,
  habits,
  search,
  pending,
  onLog,
  onAdd,
}: {
  period: Period
  habits: HabitStatus[]
  search: string
  pending: string | null
  onLog: (habit: HabitStatus) => void
  onAdd: () => void
}) {
  const meta = HABIT_PERIOD_META[period]
  return (
    <section className="flex min-w-72 flex-1 flex-col gap-3 rounded-2xl border border-line bg-raised/40 p-3">
      <header className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <Flame className="size-4 text-goal" aria-hidden />
          <h2 className="font-medium">{meta.label}</h2>
          <span className="font-mono text-xs text-muted">{habits.length}</span>
        </div>
        <p className="text-xs text-muted">{meta.kicker}</p>
      </header>
      {habits.length === 0 ? (
        <p className="text-sm text-muted">No {meta.label.toLowerCase()} habits.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {habits.map((habit) => (
            <li key={habit.slug}>
              <HabitCard
                habit={habit}
                search={search}
                pending={pending === habit.slug}
                onLog={() => onLog(habit)}
              />
            </li>
          ))}
        </ul>
      )}
      <Button type="button" variant="ghost" size="sm" className="mt-auto" onClick={onAdd}>
        <Plus className="size-4" aria-hidden />
        Add {meta.label} habit
      </Button>
    </section>
  )
}

function HabitCard({
  habit,
  search,
  pending,
  onLog,
}: {
  habit: HabitStatus
  search: string
  pending: boolean
  onLog: () => void
}) {
  return (
    <div className="flex flex-col gap-2 rounded-2xl border border-line bg-surface p-3 shadow-[var(--shadow-card)]">
      <div className="flex items-start justify-between gap-2">
        <Link
          to={{ pathname: `/habit/${habit.slug}`, search }}
          className="min-w-0 font-medium hover:underline"
        >
          {habit.name}
        </Link>
        <Badge tone={habit.satisfied ? 'good' : habit.scheduled ? 'warn' : 'default'}>
          {habit.satisfied ? 'done' : habit.scheduled ? 'open' : 'off'}
        </Badge>
      </div>
      <p className="font-mono text-xs text-muted">
        {formatComparator(habit.comparator)} {habit.target_value} / {habit.period}
        {habit.current_value !== null ? ` · now ${habit.current_value}` : ''}
      </p>
      <p className="font-mono text-xs text-muted">
        streak {habit.current_streak} · best {habit.longest_streak} ·{' '}
        {formatPercent(habit.adherence)}
      </p>
      {habit.scheduled && !habit.satisfied && (
        <Button type="button" size="sm" variant="secondary" disabled={pending} onClick={onLog}>
          Log
        </Button>
      )}
    </div>
  )
}
