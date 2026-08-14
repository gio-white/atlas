import {
  BookOpen,
  CheckSquare,
  Flag,
  Flame,
  Monitor,
  Plus,
  Sparkles,
  TriangleAlert,
} from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { AreaChart, ProgressRing, Sparkline } from '@/components/home/Charts'
import { ProgressBar } from '@/components/PageState'
import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import {
  ApiError,
  type HabitStatus,
  type HomeWeek,
  logEntry,
  type Metric,
  type PaceStatus,
  type SlipsWeek,
  type TaskBucket,
  type TaskItem,
} from '@/lib/api'
import { formatDeltaFraction, formatMinutes } from '@/lib/format'
import { summarizeGoals } from '@/lib/goalsSummary'
import { cn } from '@/lib/utils'

export function UpdatesCard({ streakDays, onAdd }: { streakDays: number; onAdd: () => void }) {
  return (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle className="text-base">Updates</CardTitle>
        <Link to="/updates" className="text-xs font-medium text-update hover:underline">
          View all
        </Link>
      </CardHeader>
      <p className="text-sm text-muted">Daily check-in</p>
      <Button
        type="button"
        className="mt-3 min-h-11 w-full bg-update text-white hover:bg-update/90"
        onClick={onAdd}
      >
        <Plus className="size-4" aria-hidden />
        Add Update
      </Button>
      <div className="mt-auto flex items-center justify-between pt-4 text-sm">
        <span className="text-muted">Current streak</span>
        <span className="inline-flex items-center gap-1 font-semibold text-update">
          <Flame className="size-4" aria-hidden />
          {streakDays} days
        </span>
      </div>
    </Card>
  )
}

export function SlipsCard({ view }: { view: SlipsWeek | null }) {
  const thisWeek = view?.this_week ?? 0
  const delta = formatDeltaFraction(view?.delta_fraction ?? null)
  const series = view?.series ?? [0, 0, 0, 0, 0, 0, 0]
  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle className="text-base">Slips</CardTitle>
          <CardDescription>This week</CardDescription>
        </div>
        <TriangleAlert className="size-4 text-slip" aria-hidden />
      </CardHeader>
      <p className="text-4xl font-semibold tracking-tight">{thisWeek}</p>
      <p
        className={cn(
          'mt-1 text-sm',
          delta !== null && thisWeek <= (view?.last_week ?? 0) ? 'text-good' : 'text-muted',
        )}
      >
        {delta === null ? 'No slips last week to compare.' : `${delta} from last week`}
      </p>
      <div className="mt-3 text-slip">
        <Sparkline values={series} />
      </div>
    </Card>
  )
}

export function ScreenTimeCard({ minutes }: { minutes: number | null }) {
  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle className="text-base">Screen Time</CardTitle>
          <CardDescription>Today's total</CardDescription>
        </div>
        <Monitor className="size-4 text-screen" aria-hidden />
      </CardHeader>
      <p className="text-3xl font-semibold tracking-tight">
        {minutes === null ? '—' : formatMinutes(minutes)}
      </p>
      <p className="mt-1 text-sm text-muted">
        {minutes === null ? 'No sessions today.' : 'Logged today.'}
      </p>
    </Card>
  )
}

export function GoalsCard({ goals }: { goals: { pace: PaceStatus; fraction: number | null }[] }) {
  const summary = summarizeGoals(goals)
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Goals</CardTitle>
        <Link to="/goal" className="text-xs font-medium text-goal hover:underline">
          View all
        </Link>
      </CardHeader>
      {goals.length === 0 ? (
        <p className="text-sm text-muted">No active goals.</p>
      ) : (
        <div className="flex items-center gap-4">
          <ProgressRing value={summary.overall} label="Overall Progress" />
          <ul className="flex flex-col gap-2 text-sm">
            <li className="flex items-center gap-2">
              <span className="size-2 rounded-full bg-good" aria-hidden />
              {summary.onTrack} On Track
            </li>
            <li className="flex items-center gap-2">
              <span className="size-2 rounded-full bg-slip" aria-hidden />
              {summary.behind} Behind
            </li>
            <li className="flex items-center gap-2">
              <span className="size-2 rounded-full bg-screen" aria-hidden />
              {summary.ahead} Ahead
            </li>
          </ul>
        </div>
      )}
    </Card>
  )
}

export function TodaysFocusCard({
  habits,
  metrics,
  asOf,
  onLogged,
  onOpenLog,
}: {
  habits: HabitStatus[]
  metrics: Metric[]
  asOf: string
  onLogged: () => Promise<void>
  onOpenLog: () => void
}) {
  const [pending, setPending] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const done = habits.filter((habit) => habit.satisfied).length
  const metricBySlug = Object.fromEntries(metrics.map((metric) => [metric.slug, metric]))

  async function onToggle(habit: HabitStatus) {
    if (habit.satisfied) return
    const metric = metricBySlug[habit.metric_slug]
    if (metric?.value_type !== 'bool') {
      onOpenLog()
      return
    }
    setError(null)
    setPending(habit.slug)
    try {
      await logEntry({ metric: habit.metric_slug, occurred_on: asOf })
      await onLogged()
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Could not log')
    } finally {
      setPending(null)
    }
  }

  return (
    <Card className="flex flex-col">
      <CardHeader>
        <div>
          <CardTitle className="text-base">Today's Focus</CardTitle>
          <CardDescription>
            {habits.length === 0
              ? 'No habits scheduled.'
              : `${habits.length} task${habits.length === 1 ? '' : 's'} planned.`}
          </CardDescription>
        </div>
      </CardHeader>
      {habits.length === 0 ? (
        <p className="text-sm text-muted">Define a habit in Catalog, then come back.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {habits.map((habit) => (
            <li key={habit.slug}>
              <label className="flex min-h-11 cursor-pointer items-center gap-3 text-sm">
                <input
                  type="checkbox"
                  className="size-4 rounded border-line"
                  checked={habit.satisfied}
                  disabled={pending === habit.slug}
                  onChange={() => {
                    if (habit.satisfied) return
                    void onToggle(habit)
                  }}
                />
                <span className={cn(habit.satisfied && 'text-muted line-through')}>
                  {habit.name}
                </span>
              </label>
            </li>
          ))}
        </ul>
      )}
      {error !== null && (
        <p className="mt-2 text-xs text-bad" role="alert">
          {error}
        </p>
      )}
      <div className="mt-auto pt-4">
        <p className="mb-2 text-xs text-muted">
          {habits.length === 0 ? '0/0 completed' : `${done}/${habits.length} completed`}
        </p>
        <ProgressBar value={habits.length === 0 ? 0 : done / habits.length} />
        {habits.length > 0 && (
          <Button type="button" variant="ghost" size="sm" className="mt-2" onClick={onOpenLog}>
            Log a value
          </Button>
        )}
      </div>
    </Card>
  )
}

const TASK_TABS: TaskBucket[] = ['today', 'upcoming', 'someday']

export function TasksCard({
  tasks,
  onAdd,
  onToggle,
}: {
  tasks: TaskItem[]
  onAdd: (title: string, bucket: TaskBucket) => Promise<void>
  onToggle: (id: number, done: boolean) => Promise<void>
}) {
  const [tab, setTab] = useState<TaskBucket>('today')
  const [draft, setDraft] = useState('')
  const [pending, setPending] = useState(false)
  const items = tasks.filter((task) => task.bucket === tab)
  return (
    <Card className="flex flex-col">
      <CardHeader>
        <CardTitle className="text-base">Tasks</CardTitle>
      </CardHeader>
      <div
        className="mb-3 flex gap-1 rounded-lg bg-raised p-1"
        role="tablist"
        aria-label="Task buckets"
      >
        {TASK_TABS.map((item) => (
          <button
            key={item}
            type="button"
            role="tab"
            aria-selected={tab === item}
            className={cn(
              'min-h-9 flex-1 rounded-md px-2 text-xs font-medium capitalize',
              tab === item ? 'bg-surface text-ink shadow-sm' : 'text-muted hover:text-ink',
            )}
            onClick={() => setTab(item)}
          >
            {item}
          </button>
        ))}
      </div>
      {items.length === 0 ? (
        <p className="text-sm text-muted">No tasks in {tab}.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {items.map((task) => (
            <TaskRow key={task.id} task={task} onToggle={onToggle} />
          ))}
        </ul>
      )}
      <form
        className="mt-auto flex gap-2 pt-3"
        onSubmit={(event) => {
          event.preventDefault()
          const title = draft.trim()
          if (title === '') return
          setPending(true)
          void onAdd(title, tab).finally(() => {
            setDraft('')
            setPending(false)
          })
        }}
      >
        <Input
          id="home-task-title"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Add a task"
          aria-label="New task title"
        />
        <Button type="submit" size="sm" disabled={pending || draft.trim() === ''}>
          <Plus className="size-4" aria-hidden />
          Add
        </Button>
      </form>
    </Card>
  )
}

function TaskRow({
  task,
  onToggle,
}: {
  task: TaskItem
  onToggle: (id: number, done: boolean) => Promise<void>
}) {
  const when = taskWhen(task)
  return (
    <li className="flex min-h-11 items-center gap-3 text-sm">
      <input
        type="checkbox"
        className="size-4 rounded border-line"
        checked={task.done_at !== null}
        onChange={() => {
          void onToggle(task.id, task.done_at === null)
        }}
      />
      <span
        className={cn(
          'min-w-0 flex-1 truncate',
          task.done_at !== null && 'text-muted line-through',
        )}
      >
        {task.title}
      </span>
      {when !== null && <span className="text-xs text-muted">{when}</span>}
      {task.priority === 'high' && (
        <span className="rounded-full bg-bad/15 px-2 py-0.5 text-[10px] font-semibold text-bad">
          High
        </span>
      )}
    </li>
  )
}

function taskWhen(task: TaskItem): string | null {
  if (task.due_at !== null) {
    return new Date(task.due_at).toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
  }
  return task.due_on
}

function weekStatTone(delta: number | null, invert: boolean): string {
  if (delta === null) return 'text-muted'
  const good = invert ? delta <= 0 : delta >= 0
  return good ? 'text-good' : 'text-bad'
}

const WEEK_DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

export function WeeklyOverviewCard({ view }: { view: HomeWeek | null }) {
  const updates = view?.updates ?? 0
  const slips = view?.slips ?? 0
  const focus = view?.focus_minutes ?? 0
  const tasks = view?.tasks_done ?? 0
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Weekly Overview</CardTitle>
      </CardHeader>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <WeekStat label="Updates" value={String(updates)} delta={view?.updates_delta ?? null} />
        <WeekStat label="Slips" value={String(slips)} delta={view?.slips_delta ?? null} invert />
        <WeekStat
          label="Focus Time"
          value={formatMinutes(focus)}
          delta={view?.focus_delta ?? null}
        />
        <WeekStat label="Tasks Done" value={String(tasks)} delta={view?.tasks_delta ?? null} />
      </div>
      <div className="mt-4">
        <AreaChart
          seriesA={view?.series_updates ?? [0, 0, 0, 0, 0, 0, 0]}
          seriesB={view?.series_slips ?? [0, 0, 0, 0, 0, 0, 0]}
          labels={WEEK_DAYS}
        />
      </div>
    </Card>
  )
}

function WeekStat({
  label,
  value,
  delta,
  invert = false,
}: {
  label: string
  value: string
  delta: number | null
  invert?: boolean
}) {
  const formatted = formatDeltaFraction(delta)
  return (
    <div>
      <p className="text-xs text-muted">{label}</p>
      <p className="text-xl font-semibold">{value}</p>
      <p className={cn('text-xs', weekStatTone(delta, invert))}>
        {formatted === null ? 'No last week to compare.' : `${formatted} from last week`}
      </p>
    </div>
  )
}

const QUOTE = {
  text: 'Discipline is the bridge between goals and accomplishment.',
  attribution: 'Jim Rohn',
}

export function QuoteCard() {
  return (
    <Card className="flex items-start gap-4">
      <Sparkles className="mt-1 size-8 shrink-0 text-update" aria-hidden />
      <blockquote>
        <p className="text-lg font-medium tracking-tight">“{QUOTE.text}”</p>
        <footer className="mt-2 text-sm text-muted">— {QUOTE.attribution}</footer>
      </blockquote>
    </Card>
  )
}

export type QuickKind = 'update' | 'slip' | 'screen' | 'task' | 'goal' | 'journal'

const QUICK: { kind: QuickKind; label: string; className: string; icon: typeof Sparkles }[] = [
  {
    kind: 'update',
    label: 'Update',
    className: 'bg-update/15 text-update hover:bg-update/25',
    icon: Sparkles,
  },
  {
    kind: 'slip',
    label: 'Slip',
    className: 'bg-slip/15 text-slip hover:bg-slip/25',
    icon: TriangleAlert,
  },
  {
    kind: 'screen',
    label: 'Screen Time',
    className: 'bg-screen/15 text-screen hover:bg-screen/25',
    icon: Monitor,
  },
  {
    kind: 'task',
    label: 'Task',
    className: 'bg-goal/15 text-goal hover:bg-goal/25',
    icon: CheckSquare,
  },
  {
    kind: 'goal',
    label: 'Goal',
    className: 'bg-quick/15 text-quick hover:bg-quick/25',
    icon: Flag,
  },
  {
    kind: 'journal',
    label: 'Journal',
    className: 'bg-update/15 text-update hover:bg-update/25',
    icon: BookOpen,
  },
]

export function QuickAddCard({ onPick }: { onPick: (kind: QuickKind) => void }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Quick Add</CardTitle>
      </CardHeader>
      <div className="flex flex-wrap gap-2">
        {QUICK.map((item) => (
          <Button
            key={item.kind}
            type="button"
            variant="ghost"
            className={cn('min-h-11 rounded-full px-4', item.className)}
            onClick={() => onPick(item.kind)}
          >
            <item.icon className="size-4" aria-hidden />
            {item.label}
          </Button>
        ))}
      </div>
    </Card>
  )
}
