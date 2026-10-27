import { Check, CheckSquare, ListChecks, Minus, Plus, SkipForward, X } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'

import { LogForm } from '@/components/LogForm'
import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import {
  ApiError,
  type Goal,
  type HabitsCalendar,
  type Metric,
  setHabitDay,
  type TaskBucket,
  type TaskItem,
  type WeekDayCell,
  type WeekHabit,
} from '@/lib/api'
import { shortDateLabel, weekdayLabel } from '@/lib/dates'
import { type HabitCellState, habitCellState, habitWeekSummary, visibleTasks } from '@/lib/home'
import { goalNameBySlug, resolveGoalName, TASK_BUCKET_META, TASK_BUCKETS } from '@/lib/tasks'
import { cn } from '@/lib/utils'

export function TasksCard({
  tasks,
  goals,
  asOf,
  search,
  onAdd,
  onToggle,
}: {
  tasks: TaskItem[]
  goals: Goal[]
  asOf: string
  search: string
  onAdd: (title: string, bucket: TaskBucket, goal: string | null) => Promise<void>
  onToggle: (id: number, done: boolean) => Promise<void>
}) {
  const [tab, setTab] = useState<TaskBucket>('today')
  const [draft, setDraft] = useState('')
  const [goal, setGoal] = useState('')
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const visible = visibleTasks(tasks, asOf)
  const items = visible.filter((task) => task.bucket === tab)
  const goalNames = goalNameBySlug(goals)
  const openCount = (bucket: TaskBucket) =>
    visible.filter((task) => task.bucket === bucket && task.done_at === null).length

  return (
    <Card className="flex flex-col">
      <CardHeader>
        <div>
          <CardTitle className="flex items-center gap-2 text-base">
            <CheckSquare className="size-4 text-goal" aria-hidden />
            Tasks
          </CardTitle>
          <CardDescription>{TASK_BUCKET_META[tab].kicker}</CardDescription>
        </div>
        <Link
          to={{ pathname: '/tasks', search }}
          className="text-xs font-medium text-goal hover:underline"
        >
          View all
        </Link>
      </CardHeader>
      <form
        className="mb-4 flex flex-wrap gap-2"
        onSubmit={(event) => {
          event.preventDefault()
          const title = draft.trim()
          if (title === '') return
          setPending(true)
          setError(null)
          onAdd(title, tab, goal || null)
            .then(() => setDraft(''))
            .catch((caught: unknown) => {
              setError(caught instanceof ApiError ? caught.message : 'Could not add task')
            })
            .finally(() => setPending(false))
        }}
      >
        <Input
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder={`Add a task to ${TASK_BUCKET_META[tab].label.toLowerCase()}`}
          aria-label="New task title"
          className="min-w-0 flex-1 basis-48"
        />
        {goals.length > 0 && (
          <Select
            aria-label="Link to goal"
            value={goal}
            onChange={(event) => setGoal(event.target.value)}
            className="w-auto max-w-40"
          >
            <option value="">No goal</option>
            {goals.map((item) => (
              <option key={item.slug} value={item.slug}>
                {item.name}
              </option>
            ))}
          </Select>
        )}
        <Button type="submit" disabled={pending || draft.trim() === ''}>
          <Plus className="size-4" aria-hidden />
          Add
        </Button>
      </form>
      {error !== null && (
        <p className="-mt-2 mb-3 text-xs text-bad" role="alert">
          {error}
        </p>
      )}
      <div
        className="mb-3 flex gap-1 rounded-lg bg-raised p-1"
        role="tablist"
        aria-label="Task buckets"
      >
        {TASK_BUCKETS.map((bucket) => (
          <button
            key={bucket}
            type="button"
            role="tab"
            aria-selected={tab === bucket}
            className={cn(
              'min-h-9 flex-1 rounded-md px-2 text-xs font-medium',
              tab === bucket ? 'bg-surface text-ink shadow-sm' : 'text-muted hover:text-ink',
            )}
            onClick={() => setTab(bucket)}
          >
            {TASK_BUCKET_META[bucket].label}
            <span className="ml-1.5 tabular-nums text-muted">{openCount(bucket)}</span>
          </button>
        ))}
      </div>
      {items.length === 0 ? (
        <p className="py-6 text-center text-sm text-muted">
          Nothing in {TASK_BUCKET_META[tab].label.toLowerCase()}. Add one above.
        </p>
      ) : (
        <ul className="flex flex-col divide-y divide-line">
          {items.map((task) => (
            <TaskRow
              key={task.id}
              task={task}
              goalName={resolveGoalName(task.goal, goalNames)}
              onToggle={onToggle}
            />
          ))}
        </ul>
      )}
    </Card>
  )
}

function TaskRow({
  task,
  goalName,
  onToggle,
}: {
  task: TaskItem
  goalName: string | null
  onToggle: (id: number, done: boolean) => Promise<void>
}) {
  const when = taskWhen(task)
  const done = task.done_at !== null
  return (
    <li className="flex min-h-11 items-center gap-3 text-sm">
      <input
        type="checkbox"
        className="size-4 rounded border-line"
        checked={done}
        aria-label={`Mark ${task.title} ${done ? 'not done' : 'done'}`}
        onChange={() => {
          void onToggle(task.id, !done)
        }}
      />
      <span className={cn('min-w-0 flex-1 truncate', done && 'text-muted line-through')}>
        {task.title}
      </span>
      {goalName !== null && (
        <span className="hidden max-w-40 truncate text-xs text-muted sm:inline" title={goalName}>
          {goalName}
        </span>
      )}
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
  return task.due_on === null ? null : shortDateLabel(task.due_on)
}

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
            <ListChecks className="size-4 text-update" aria-hidden />
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
          className="text-xs font-medium text-update hover:underline"
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
        <div className="overflow-x-auto">
          <table className="w-full min-w-[22rem] border-collapse text-sm">
            <thead>
              <tr>
                <th className="pb-2 pr-2 text-left text-xs font-medium text-muted">Habit</th>
                {headings.map((cell) => (
                  <th
                    key={cell.day}
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
                  <td className="py-2 pr-2">
                    <Link
                      to={{ pathname: `/habit/${habit.slug}`, search }}
                      className="block max-w-40 truncate font-medium hover:underline"
                    >
                      {habit.name}
                    </Link>
                    <span className="text-xs text-muted">{habitWeekSummary(habit, asOf)}</span>
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
        today && 'ring-2 ring-update/40',
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
