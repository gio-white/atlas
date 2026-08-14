import { ArrowRight, Calendar, CheckCircle2, Flag, Plus, Rocket } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { GoalCreateDialog } from '@/components/goals/GoalCreateDialog'
import { PaceBadge } from '@/components/PaceBadge'
import { PageHeader, PageLoading, PageUnavailable, ProgressBar } from '@/components/PageState'
import { Button } from '@/components/ui/button'
import {
  ApiError,
  type Area,
  type Goal,
  type GoalBoardColumn,
  type GoalHorizon,
  type GoalProgress,
  type GoalsBoard,
  getGoalsBoard,
  listAreas,
  listGoals,
  listMetrics,
  type Metric,
  type TaskItem,
  updateTask,
} from '@/lib/api'
import { useAsOf } from '@/lib/asOf'
import { parseIsoDate, weekdayLabel } from '@/lib/dates'
import { formatPercent } from '@/lib/format'
import { HORIZON_META, HORIZONS } from '@/lib/horizons'
import { cn } from '@/lib/utils'

const FILTERS: { id: 'all' | GoalHorizon; label: string }[] = [
  { id: 'all', label: 'All Goals' },
  { id: 'long', label: 'Long Term (1+ year)' },
  { id: 'medium', label: 'Medium Term (months)' },
  { id: 'short', label: 'Short Term (week)' },
]

const COLUMN_ICON = {
  long: Rocket,
  medium: Calendar,
  short: Flag,
} as const

export function GoalsPage() {
  const asOf = useAsOf()
  const [params] = useSearchParams()
  const [board, setBoard] = useState<GoalsBoard | null>(null)
  const [areas, setAreas] = useState<Area[]>([])
  const [metrics, setMetrics] = useState<Metric[]>([])
  const [goals, setGoals] = useState<Goal[]>([])
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<'all' | GoalHorizon>('all')
  const [createHorizon, setCreateHorizon] = useState<GoalHorizon | null>(null)

  const refresh = useCallback(async () => {
    const [nextBoard, nextAreas, nextMetrics, nextGoals] = await Promise.all([
      getGoalsBoard(asOf),
      listAreas(),
      listMetrics(),
      listGoals(),
    ])
    setBoard(nextBoard)
    setAreas(nextAreas)
    setMetrics(nextMetrics)
    setGoals(nextGoals)
  }, [asOf])

  useEffect(() => {
    let cancelled = false
    setError(null)
    refresh().catch((caught: unknown) => {
      if (!cancelled) {
        setError(caught instanceof ApiError ? caught.message : 'Could not load goals')
        setBoard(null)
      }
    })
    return () => {
      cancelled = true
    }
  }, [refresh])

  if (error !== null) {
    return <PageUnavailable title="Goals" message={error} />
  }
  if (board === null) return <PageLoading />

  const columns = HORIZONS.filter((horizon) => filter === 'all' || filter === horizon).map(
    (horizon) => board[horizon],
  )
  const empty =
    board.long.total + board.medium.total + board.short.total === 0 && board.week.total === 0

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageHeader
          title="Goals"
          description="Big picture to daily actions. Stay aligned, every step of the way."
          homeLink
        />
        <Button type="button" onClick={() => setCreateHorizon('long')}>
          <Plus className="size-4" aria-hidden />
          New Goal
        </Button>
      </div>
      <div className="flex flex-wrap gap-2" role="tablist" aria-label="Goal horizon">
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
      {empty ? (
        <div className="rounded-2xl border border-dashed border-line bg-raised/70 px-4 py-8 text-center">
          <p className="font-medium text-ink">No goals yet</p>
          <p className="mt-1 text-sm text-muted">
            Start with a long-term north star, then nest the work underneath.
          </p>
          <Button type="button" size="sm" className="mt-3" onClick={() => setCreateHorizon('long')}>
            Add a long-term goal
          </Button>
        </div>
      ) : (
        <div className="flex gap-4 overflow-x-auto pb-2">
          {columns.map((column, index) => (
            <div key={column.horizon} className="flex min-w-72 flex-1 items-stretch gap-4">
              {index > 0 && (
                <div className="hidden items-center text-muted lg:flex" aria-hidden>
                  <ArrowRight className="size-5" />
                </div>
              )}
              <HorizonColumn
                column={column}
                search={params.toString()}
                onAdd={() => setCreateHorizon(column.horizon)}
              />
            </div>
          ))}
          {(filter === 'all' || filter === 'short') && (
            <div className="flex min-w-72 flex-1 items-stretch gap-4">
              <div className="hidden items-center text-muted lg:flex" aria-hidden>
                <ArrowRight className="size-5" />
              </div>
              <WeekColumn
                week={board.week}
                search={params.toString()}
                onToggle={(task) => {
                  updateTask(task.id, { done: task.done_at === null })
                    .then(refresh)
                    .catch((caught: unknown) => {
                      setError(
                        caught instanceof ApiError ? caught.message : 'Could not update task',
                      )
                    })
                }}
              />
            </div>
          )}
        </div>
      )}
      <div className="grid gap-4 lg:grid-cols-2">
        <aside className="rounded-2xl border border-line bg-surface p-4 shadow-[var(--shadow-card)]">
          <h2 className="font-medium">Everything is connected</h2>
          <p className="mt-2 text-sm text-muted">
            Long-term goals are the north star. Medium-term goals are the next stretch. Short-term
            goals are this week&apos;s focus. Tasks are how the week actually moves.
          </p>
        </aside>
        <blockquote className="rounded-2xl border border-line bg-surface p-4 shadow-[var(--shadow-card)]">
          <p className="text-lg font-medium tracking-tight">
            The best way to predict the future is to create it.
          </p>
          <footer className="mt-2 text-sm text-muted">— Peter Drucker</footer>
        </blockquote>
      </div>
      {createHorizon !== null && (
        <GoalCreateDialog
          open
          onOpenChange={(open) => {
            if (!open) setCreateHorizon(null)
          }}
          horizon={createHorizon}
          areas={areas}
          metrics={metrics}
          goals={goals}
          onCreated={refresh}
        />
      )}
    </div>
  )
}

function HorizonColumn({
  column,
  search,
  onAdd,
}: {
  column: GoalBoardColumn
  search: string
  onAdd: () => void
}) {
  const meta = HORIZON_META[column.horizon]
  const Icon = COLUMN_ICON[column.horizon]
  return (
    <section className="flex min-w-72 flex-1 flex-col gap-3 rounded-2xl border border-line bg-raised/40 p-3">
      <header className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <Icon className="size-4 text-goal" aria-hidden />
          <h2 className="font-medium">{meta.label}</h2>
          <span className="font-mono text-xs text-muted">{meta.window}</span>
        </div>
        <p className="text-xs text-muted">{meta.kicker}</p>
        <p className="font-mono text-xs text-muted">
          {column.on_track} / {column.total} goals on track
          {column.fraction !== null ? ` · ${formatPercent(column.fraction)}` : ''}
        </p>
        <ProgressBar value={column.fraction} />
      </header>
      <ul className="flex flex-col gap-2">
        {column.goals.map((goal) => (
          <li key={goal.slug}>
            <GoalCard goal={goal} search={search} />
          </li>
        ))}
      </ul>
      <Button type="button" variant="ghost" size="sm" className="mt-auto" onClick={onAdd}>
        <Plus className="size-4" aria-hidden />
        Add {meta.label} Goal
      </Button>
    </section>
  )
}

function GoalCard({ goal, search }: { goal: GoalProgress; search: string }) {
  const dateLabel = goal.horizon === 'long' ? 'Target' : 'Due'
  return (
    <Link
      to={{ pathname: `/goal/${goal.slug}`, search }}
      className="flex flex-col gap-2 rounded-2xl border border-line bg-surface p-3 shadow-[var(--shadow-card)] motion-safe:transition-colors hover:bg-raised"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="font-medium">{goal.name}</p>
          {goal.description !== null && goal.description !== '' && (
            <p className="mt-0.5 line-clamp-2 text-xs text-muted">{goal.description}</p>
          )}
        </div>
        <PaceBadge pace={goal.pace} />
      </div>
      <p className="font-mono text-xs text-muted">
        {dateLabel}: {formatHorizonDate(goal.due_on, goal.horizon)}
      </p>
      <ProgressBar value={goal.fraction} />
    </Link>
  )
}

function WeekColumn({
  week,
  search,
  onToggle,
}: {
  week: GoalsBoard['week']
  search: string
  onToggle: (task: TaskItem) => void
}) {
  return (
    <section className="flex min-w-72 flex-1 flex-col gap-3 rounded-2xl border border-line bg-raised/40 p-3">
      <header className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="size-4 text-goal" aria-hidden />
          <h2 className="font-medium">Weekly Action Plan</h2>
          <span className="font-mono text-xs text-muted">This Week</span>
        </div>
        <p className="text-xs text-muted">Concrete tasks to achieve your short-term goals.</p>
        <p className="font-mono text-xs text-muted">
          {week.total} Tasks · {week.done} Done
          {week.fraction !== null ? ` · ${formatPercent(week.fraction)}` : ''}
        </p>
        <ProgressBar value={week.fraction} />
      </header>
      <ul className="flex flex-col gap-2">
        {week.tasks.map((task) => (
          <li key={task.id}>
            <label
              className={cn(
                'flex min-h-11 cursor-pointer items-start gap-3 rounded-2xl border border-line bg-surface p-3 text-sm',
                task.done_at !== null && 'text-muted',
              )}
            >
              <input
                type="checkbox"
                className="mt-0.5 size-4 accent-accent"
                checked={task.done_at !== null}
                onChange={() => onToggle(task)}
              />
              <span className="min-w-0 flex-1">
                <span className={cn('block', task.done_at !== null && 'line-through')}>
                  {task.title}
                </span>
                <span className="mt-1 block font-mono text-xs text-muted">
                  {taskWhen(task)}
                  {task.goal !== null ? ` · ${task.goal}` : ''}
                </span>
              </span>
            </label>
          </li>
        ))}
      </ul>
      <Button asChild variant="ghost" size="sm" className="mt-auto">
        <Link to={{ pathname: '/', search }}>View all tasks</Link>
      </Button>
    </section>
  )
}

function formatHorizonDate(iso: string, horizon: GoalHorizon): string {
  const date = parseIsoDate(iso)
  if (horizon === 'long') {
    return date.toLocaleDateString('en-GB', { month: 'short', year: 'numeric' })
  }
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' })
}

function taskWhen(task: TaskItem): string {
  if (task.due_at !== null) {
    return new Date(task.due_at).toLocaleTimeString('en-GB', {
      hour: 'numeric',
      minute: '2-digit',
    })
  }
  if (task.due_on !== null) return weekdayLabel(task.due_on)
  return task.bucket
}
