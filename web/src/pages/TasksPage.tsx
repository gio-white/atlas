import { CheckSquare, Plus } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { EmptyState, PageHeader, PageLoading, PageUnavailable } from '@/components/PageState'
import { TaskCreateDialog } from '@/components/tasks/TaskCreateDialog'
import { Button } from '@/components/ui/button'
import { Select } from '@/components/ui/select'
import {
  ApiError,
  type Goal,
  listGoals,
  listTasks,
  type TaskBucket,
  type TaskItem,
  updateTask,
} from '@/lib/api'
import { weekdayLabel } from '@/lib/dates'
import {
  activeGoals,
  filterTasks,
  goalNameBySlug,
  groupTasksByBucket,
  resolveGoalName,
  TASK_BUCKET_META,
  TASK_BUCKETS,
  withGoalParam,
} from '@/lib/tasks'
import { cn } from '@/lib/utils'

export function TasksPage() {
  const [params, setParams] = useSearchParams()
  const search = params.toString()
  const goalFilter = params.get('goal')
  const [tasks, setTasks] = useState<TaskItem[] | null>(null)
  const [goals, setGoals] = useState<Goal[]>([])
  const [error, setError] = useState<string | null>(null)
  const [includeDone, setIncludeDone] = useState(false)
  const [createOpen, setCreateOpen] = useState(false)

  const refresh = useCallback(async () => {
    const [nextTasks, nextGoals] = await Promise.all([
      listTasks({ include_done: true }),
      listGoals(),
    ])
    setTasks(nextTasks)
    setGoals(nextGoals)
  }, [])

  useEffect(() => {
    let cancelled = false
    setError(null)
    refresh().catch((caught: unknown) => {
      if (!cancelled) {
        setError(caught instanceof ApiError ? caught.message : 'Could not load tasks')
        setTasks(null)
      }
    })
    return () => {
      cancelled = true
    }
  }, [refresh])

  const names = useMemo(() => goalNameBySlug(goals), [goals])
  const chips = useMemo(() => activeGoals(goals), [goals])
  const visible = useMemo(
    () => filterTasks(tasks ?? [], { goal: goalFilter, includeDone }),
    [tasks, goalFilter, includeDone],
  )
  const grouped = useMemo(() => groupTasksByBucket(visible), [visible])

  function setGoalFilter(slug: string | null) {
    const next = new URLSearchParams(withGoalParam(search, slug))
    setParams(next, { replace: true })
  }

  if (error !== null) {
    return <PageUnavailable title="Tasks" message={error} />
  }
  if (tasks === null) return <PageLoading />

  const empty = tasks.length === 0

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageHeader
          title="Tasks"
          description="Day-to-day operative work. Not habits, not metrics — check them off as you go."
          homeLink
        />
        <Button type="button" onClick={() => setCreateOpen(true)}>
          <Plus className="size-4" aria-hidden />
          New Task
        </Button>
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex flex-wrap gap-2" role="tablist" aria-label="Filter by goal">
          <FilterChip
            label="All goals"
            selected={goalFilter === null}
            onClick={() => setGoalFilter(null)}
          />
          {chips.map((goal) => (
            <FilterChip
              key={goal.slug}
              label={goal.name}
              selected={goalFilter === goal.slug}
              onClick={() => setGoalFilter(goal.slug)}
            />
          ))}
        </div>
        <button
          type="button"
          className={cn(
            'ml-auto rounded-full border px-3 py-1.5 text-sm motion-safe:transition-colors',
            includeDone
              ? 'border-goal bg-goal/15 text-ink'
              : 'border-line bg-surface text-muted hover:bg-raised',
          )}
          aria-pressed={includeDone}
          onClick={() => setIncludeDone((current) => !current)}
        >
          Show done
        </button>
      </div>
      {empty ? (
        <EmptyState
          title="No tasks yet"
          hint="Add the work you will do today. Link a goal when the task moves one."
        />
      ) : (
        <div className="flex gap-4 overflow-x-auto pb-2">
          {TASK_BUCKETS.map((bucket) => (
            <BucketColumn
              key={bucket}
              bucket={bucket}
              tasks={grouped[bucket]}
              names={names}
              search={search}
              onToggle={(task) => {
                updateTask(task.id, { done: task.done_at === null })
                  .then(refresh)
                  .catch((caught: unknown) => {
                    setError(caught instanceof ApiError ? caught.message : 'Could not update task')
                  })
              }}
              onMove={(task, next) => {
                updateTask(task.id, { bucket: next })
                  .then(refresh)
                  .catch((caught: unknown) => {
                    setError(caught instanceof ApiError ? caught.message : 'Could not update task')
                  })
              }}
            />
          ))}
        </div>
      )}
      <TaskCreateDialog
        open={createOpen}
        onOpenChange={setCreateOpen}
        goals={goals}
        defaultGoal={goalFilter}
        onCreated={refresh}
      />
    </div>
  )
}

function FilterChip({
  label,
  selected,
  onClick,
}: {
  label: string
  selected: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      role="tab"
      aria-selected={selected}
      className={cn(
        'rounded-full border px-3 py-1.5 text-sm motion-safe:transition-colors',
        selected
          ? 'border-goal bg-goal/15 text-ink'
          : 'border-line bg-surface text-muted hover:bg-raised',
      )}
      onClick={onClick}
    >
      {label}
    </button>
  )
}

function BucketColumn({
  bucket,
  tasks,
  names,
  search,
  onToggle,
  onMove,
}: {
  bucket: TaskBucket
  tasks: TaskItem[]
  names: Map<string, string>
  search: string
  onToggle: (task: TaskItem) => void
  onMove: (task: TaskItem, bucket: TaskBucket) => void
}) {
  const meta = TASK_BUCKET_META[bucket]
  return (
    <section className="flex min-w-72 flex-1 flex-col gap-3 rounded-2xl border border-line bg-raised/40 p-3">
      <header className="flex flex-col gap-1">
        <div className="flex items-center gap-2">
          <CheckSquare className="size-4 text-goal" aria-hidden />
          <h2 className="font-medium">{meta.label}</h2>
          <span className="font-mono text-xs text-muted">{tasks.length}</span>
        </div>
        <p className="text-xs text-muted">{meta.kicker}</p>
      </header>
      {tasks.length === 0 ? (
        <p className="text-sm text-muted">No tasks in {meta.label.toLowerCase()}.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {tasks.map((task) => (
            <TaskBoardRow
              key={task.id}
              task={task}
              goalName={resolveGoalName(task.goal, names)}
              search={search}
              onToggle={() => onToggle(task)}
              onMove={(next) => onMove(task, next)}
            />
          ))}
        </ul>
      )}
    </section>
  )
}

function TaskBoardRow({
  task,
  goalName,
  search,
  onToggle,
  onMove,
}: {
  task: TaskItem
  goalName: string | null
  search: string
  onToggle: () => void
  onMove: (bucket: TaskBucket) => void
}) {
  const when = taskWhen(task)
  const done = task.done_at !== null
  return (
    <li
      className={cn(
        'flex flex-col gap-2 rounded-2xl border border-line bg-surface p-3 text-sm',
        done && 'text-muted',
      )}
    >
      <div className="flex items-start gap-3">
        <input
          type="checkbox"
          className="mt-0.5 size-4 accent-accent"
          checked={done}
          aria-label={`Mark ${task.title} ${done ? 'open' : 'done'}`}
          onChange={onToggle}
        />
        <div className="min-w-0 flex-1">
          <p className={cn('font-medium', done && 'line-through')}>{task.title}</p>
          {(when !== null || goalName !== null) && (
            <p className="mt-1 font-mono text-xs text-muted">
              {when}
              {when !== null && goalName !== null ? ' · ' : null}
              {task.goal !== null && goalName !== null ? (
                <Link
                  to={{ pathname: `/goal/${task.goal}`, search }}
                  className="underline hover:text-ink"
                >
                  {goalName}
                </Link>
              ) : null}
            </p>
          )}
        </div>
        {task.priority === 'high' && (
          <span className="rounded-full bg-bad/15 px-2 py-0.5 text-[10px] font-semibold text-bad">
            High
          </span>
        )}
      </div>
      <Select
        aria-label={`Move ${task.title}`}
        value={task.bucket}
        onChange={(event) => onMove(event.target.value as TaskBucket)}
      >
        {TASK_BUCKETS.map((item) => (
          <option key={item} value={item}>
            {TASK_BUCKET_META[item].label}
          </option>
        ))}
      </Select>
    </li>
  )
}

function taskWhen(task: TaskItem): string | null {
  if (task.due_at !== null) {
    return new Date(task.due_at).toLocaleTimeString('en-GB', {
      hour: 'numeric',
      minute: '2-digit',
    })
  }
  if (task.due_on !== null) return weekdayLabel(task.due_on)
  return null
}
