import { ArrowDown, ArrowUp, Circle, CircleCheck, CircleDot, Plus } from 'lucide-react'
import { type FormEvent, useState } from 'react'

import { Input } from '@/components/ui/input'
import {
  createQuestTask,
  type ParentKind,
  type QuestTask,
  type TaskCreate,
  updateQuestTask,
} from '@/lib/api'
import {
  estimateLabel,
  pathLabel,
  questDateLabel,
  reorder,
  shareLabel,
  TASK_STATUS_LABELS,
} from '@/lib/quests'
import { cn } from '@/lib/utils'

import { useOpenTask } from './TaskDrawer'
import { errorMessage } from './useQuestView'

export type TaskHome = { kind: ParentKind; id: number } | 'standalone'

/** Round checkbox: completing a task is always this explicit click (or the drawer). */
export function TaskCheck({
  task,
  onChanged,
  onError,
}: {
  task: QuestTask
  onChanged: () => void
  onError?: (message: string) => void
}) {
  const [busy, setBusy] = useState(false)
  const done = task.status === 'completed'
  const Icon = done ? CircleCheck : task.status === 'in_progress' ? CircleDot : Circle
  return (
    <button
      type="button"
      disabled={busy}
      aria-label={done ? `Reopen ${task.title}` : `Mark ${task.title} done`}
      className={cn(
        'inline-flex size-9 shrink-0 items-center justify-center rounded-full motion-safe:transition-colors',
        done ? 'text-good' : 'text-muted hover:text-accent',
      )}
      onClick={async () => {
        setBusy(true)
        try {
          await updateQuestTask(task.id, { status: done ? 'todo' : 'completed' })
          onChanged()
        } catch (caught) {
          onError?.(errorMessage(caught, "Couldn't update the task."))
        } finally {
          setBusy(false)
        }
      }}
    >
      <Icon className="size-5" aria-hidden />
    </button>
  )
}

export function TaskRow({
  task,
  onChanged,
  onError,
  showContext = false,
  showShare = true,
  onMove,
  canMoveUp = false,
  canMoveDown = false,
  compact = false,
}: {
  task: QuestTask
  onChanged: () => void
  onError?: (message: string) => void
  showContext?: boolean
  showShare?: boolean
  onMove?: (direction: -1 | 1) => void
  canMoveUp?: boolean
  canMoveDown?: boolean
  compact?: boolean
}) {
  const openTask = useOpenTask()
  const done = task.status === 'completed'
  const share = showShare ? shareLabel(task.weight_share) : null
  const estimate = estimateLabel(task.estimate_minutes)
  const meta: string[] = []
  if (task.status === 'in_progress') meta.push(TASK_STATUS_LABELS.in_progress)
  if (task.priority === 'high' && !done) meta.push('High priority')
  if (task.due_on !== null) meta.push(`Due ${questDateLabel(task.due_on)}`)
  if (estimate !== null) meta.push(`About ${estimate}`)
  const context = showContext && task.path.length > 0 ? pathLabel(task.path) : null

  return (
    <li
      className={cn(
        'group flex items-center gap-1 rounded-xl pr-1 hover:bg-raised/60',
        compact ? 'min-h-10' : 'min-h-12',
      )}
      data-testid="task-row"
    >
      <TaskCheck task={task} onChanged={onChanged} onError={onError} />
      <button
        type="button"
        className="min-w-0 flex-1 py-1.5 text-left"
        onClick={() => openTask(task.id)}
      >
        <span
          className={cn(
            'block text-sm break-words',
            done ? 'text-muted line-through decoration-muted/60' : 'text-ink',
          )}
        >
          {task.title}
        </span>
        {(meta.length > 0 || context !== null) && (
          <span className="block text-xs text-muted">
            {[context, ...meta].filter(Boolean).join(' · ')}
          </span>
        )}
      </button>
      {share !== null && (
        <span
          className="shrink-0 rounded-full bg-raised px-2 py-0.5 text-xs tabular-nums text-muted"
          title="How much this task counts toward its parent"
        >
          <span className="sr-only">Counts </span>
          {share}
        </span>
      )}
      {onMove !== undefined && (
        <MoveButtons
          className="hidden sm:flex"
          label={task.title}
          canUp={canMoveUp}
          canDown={canMoveDown}
          onMove={onMove}
        />
      )}
    </li>
  )
}

export function MoveButtons({
  label,
  canUp,
  canDown,
  onMove,
  className,
}: {
  label: string
  canUp: boolean
  canDown: boolean
  onMove: (direction: -1 | 1) => void
  className?: string
}) {
  return (
    <span className={cn('flex shrink-0 items-center', className)}>
      <button
        type="button"
        aria-label={`Move ${label} up`}
        disabled={!canUp}
        className="inline-flex size-9 items-center justify-center rounded-lg text-muted hover:bg-raised hover:text-ink disabled:opacity-30"
        onClick={() => onMove(-1)}
      >
        <ArrowUp className="size-3.5" aria-hidden />
      </button>
      <button
        type="button"
        aria-label={`Move ${label} down`}
        disabled={!canDown}
        className="inline-flex size-9 items-center justify-center rounded-lg text-muted hover:bg-raised hover:text-ink disabled:opacity-30"
        onClick={() => onMove(1)}
      >
        <ArrowDown className="size-3.5" aria-hidden />
      </button>
    </span>
  )
}

/** Send the position updates for one up/down move, then reload. */
export async function moveSibling(
  items: { id: number; position: number }[],
  index: number,
  direction: -1 | 1,
  save: (id: number, position: number) => Promise<unknown>,
) {
  for (const update of reorder(items, index, direction)) {
    await save(update.id, update.position)
  }
}

export function TaskList({
  tasks,
  home,
  onChanged,
  reorderable = true,
  showContext = false,
  showShare = true,
  addLabel = 'Add a task',
  emptyHint,
  compact = false,
}: {
  tasks: QuestTask[]
  /** Where new tasks go; omit to hide the add control. */
  home?: TaskHome
  onChanged: () => void
  reorderable?: boolean
  showContext?: boolean
  showShare?: boolean
  addLabel?: string
  emptyHint?: string
  compact?: boolean
}) {
  const [error, setError] = useState<string | null>(null)

  async function move(index: number, direction: -1 | 1) {
    setError(null)
    try {
      await moveSibling(tasks, index, direction, (id, position) =>
        updateQuestTask(id, { position }),
      )
    } catch (caught) {
      setError(errorMessage(caught, "Couldn't reorder the tasks."))
    } finally {
      onChanged()
    }
  }

  return (
    <div className="flex flex-col gap-1">
      {tasks.length === 0 && emptyHint !== undefined && (
        <p className="px-2 py-1 text-sm text-muted">{emptyHint}</p>
      )}
      {tasks.length > 0 && (
        <ul className="flex flex-col">
          {tasks.map((task, index) => (
            <TaskRow
              key={task.id}
              task={task}
              onChanged={onChanged}
              onError={setError}
              showContext={showContext}
              showShare={showShare}
              compact={compact}
              onMove={reorderable && tasks.length > 1 ? (dir) => void move(index, dir) : undefined}
              canMoveUp={index > 0}
              canMoveDown={index < tasks.length - 1}
            />
          ))}
        </ul>
      )}
      {error !== null && (
        <p role="alert" className="px-2 text-sm text-bad">
          {error}
        </p>
      )}
      {home !== undefined && <AddTask home={home} label={addLabel} onAdded={onChanged} />}
    </div>
  )
}

function AddTask({ home, label, onAdded }: { home: TaskHome; label: string; onAdded: () => void }) {
  const [open, setOpen] = useState(false)
  const [title, setTitle] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    const trimmed = title.trim()
    if (trimmed === '') return
    setBusy(true)
    setError(null)
    const body: TaskCreate =
      home === 'standalone'
        ? { title: trimmed, standalone: true }
        : { title: trimmed, parent_kind: home.kind, parent_id: home.id }
    try {
      await createQuestTask(body)
      setTitle('')
      onAdded()
    } catch (caught) {
      setError(errorMessage(caught, "Couldn't add the task."))
    } finally {
      setBusy(false)
    }
  }

  if (!open) {
    return (
      <button
        type="button"
        className="inline-flex min-h-10 items-center gap-2 self-start rounded-lg px-2 text-sm text-muted hover:bg-raised hover:text-ink"
        onClick={() => setOpen(true)}
      >
        <Plus className="size-4" aria-hidden />
        {label}
      </button>
    )
  }
  return (
    <form className="flex flex-col gap-1 px-1" onSubmit={onSubmit}>
      <div className="flex items-center gap-2">
        <Circle className="ml-2 size-5 shrink-0 text-muted/60" aria-hidden />
        <Input
          autoFocus
          aria-label="New task title"
          placeholder="What needs doing? Press Enter to add"
          value={title}
          readOnly={busy}
          onChange={(event) => setTitle(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Escape') {
              setOpen(false)
              setTitle('')
            }
          }}
          onBlur={() => {
            if (title.trim() === '') setOpen(false)
          }}
        />
      </div>
      {error !== null && (
        <p role="alert" className="px-2 text-sm text-bad">
          {error}
        </p>
      )}
    </form>
  )
}
