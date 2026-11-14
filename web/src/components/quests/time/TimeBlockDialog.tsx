import { Ban, CalendarCheck, Search, Trash2 } from 'lucide-react'
import { type FormEvent, useEffect, useId, useMemo, useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  ApiError,
  cancelTimeBlock,
  completeTimeBlock,
  createTimeBlock,
  deleteTimeBlock,
  listQuestTasks,
  missTimeBlock,
  type QuestTask,
  type TimeBlock,
  updateTimeBlock,
} from '@/lib/api'
import {
  addMinutesToTime,
  BLOCK_STATUS_LABELS,
  formatDuration,
  hasStarted,
  inputMinutes,
  localToUtc,
  nextHalfHour,
  pathLabel,
  utcToLocal,
  windowError,
} from '@/lib/timeBlocks'
import { cn } from '@/lib/utils'

import { PathLine, TaskMark } from './parts'

export type DialogTask = Pick<
  QuestTask,
  'id' | 'title' | 'path' | 'status' | 'standalone' | 'inbox' | 'archived_at'
>

export type TimeBlockDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Edit this block; omit to plan a new one. */
  block?: TimeBlock | null
  /** The task the session is for. Omit to let the person pick one. */
  task?: DialogTask | null
  /** Where a new session starts (local date and time), e.g. the clicked slot on Plan. */
  initial?: { date: string; start: string; end?: string } | null
  /** Called after any change is saved (create, edit, done, cancel, delete). */
  onSaved: () => void | Promise<void>
}

const DEFAULT_MINUTES = 60

function initialWindow(
  block: TimeBlock | null | undefined,
  initial: TimeBlockDialogProps['initial'],
) {
  if (block) {
    const start = utcToLocal(block.start_at)
    const end = utcToLocal(block.end_at)
    return { date: start.date, start: start.time, end: end.time }
  }
  const from =
    initial ??
    (() => {
      const next = nextHalfHour()
      return { date: next.date, start: next.time }
    })()
  return {
    date: from.date,
    start: from.start,
    end: initial?.end ?? addMinutesToTime(from.start, DEFAULT_MINUTES),
  }
}

/** Plan or edit one session. Shared by Home, Plan, and a task's sessions list. */
export function TimeBlockDialog(props: TimeBlockDialogProps) {
  return (
    <Dialog open={props.open} onOpenChange={props.onOpenChange}>
      <DialogContent className="max-h-[calc(100svh-2rem)] overflow-y-auto">
        {props.open && <TimeBlockForm {...props} />}
      </DialogContent>
    </Dialog>
  )
}

function TimeBlockForm({ onOpenChange, block, task, initial, onSaved }: TimeBlockDialogProps) {
  const editing = block !== null && block !== undefined
  const start0 = useMemo(() => initialWindow(block, initial), [block, initial])
  const [date, setDate] = useState(start0.date)
  const [start, setStart] = useState(start0.start)
  const [end, setEnd] = useState(start0.end)
  const [picked, setPicked] = useState<DialogTask | null>(task ?? null)
  const [touched, setTouched] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const ids = useId()

  const minutes = inputMinutes(date, start, end)
  const invalid = windowError(date, start, end)
  const showInvalid = touched && invalid !== null

  async function run(action: () => Promise<unknown>, fallback: string) {
    setSaving(true)
    setError(null)
    try {
      await action()
      await onSaved()
      onOpenChange(false)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : fallback)
    } finally {
      setSaving(false)
    }
  }

  function submit(event: FormEvent) {
    event.preventDefault()
    setTouched(true)
    if (invalid !== null) return
    if (!editing && picked === null) {
      setError('Choose a task for this session.')
      return
    }
    const window = { start_at: localToUtc(date, start), end_at: localToUtc(date, end) }
    if (editing) {
      void run(() => updateTimeBlock(block.id, window), 'Couldn’t save the session.')
    } else if (picked !== null) {
      void run(
        () => createTimeBlock({ task_id: picked.id, ...window }),
        'Couldn’t plan the session.',
      )
    }
  }

  return (
    <form className="flex flex-col gap-4" onSubmit={submit} noValidate>
      <DialogHeader>
        <DialogTitle>{editing ? 'Edit session' : 'Plan a session'}</DialogTitle>
        <DialogDescription>
          {editing
            ? `${BLOCK_STATUS_LABELS[block.status]}. Change the time, or record how it went.`
            : 'Set aside time to work on a task. Finishing a session never completes the task.'}
        </DialogDescription>
      </DialogHeader>

      {task || editing ? (
        picked !== null && <ChosenTask task={picked} />
      ) : (
        <TaskPicker picked={picked} onPick={setPicked} />
      )}

      <fieldset className="grid grid-cols-2 gap-2 sm:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)_minmax(0,1fr)]">
        <legend className="sr-only">When</legend>
        <div className="col-span-2 flex flex-col gap-1 sm:col-span-1">
          <Label htmlFor={`${ids}-date`}>Date</Label>
          <Input
            id={`${ids}-date`}
            type="date"
            value={date}
            onChange={(event) => setDate(event.target.value)}
            required
          />
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor={`${ids}-start`}>From</Label>
          <Input
            id={`${ids}-start`}
            type="time"
            value={start}
            onChange={(event) => setStart(event.target.value)}
            required
          />
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor={`${ids}-end`}>To</Label>
          <Input
            id={`${ids}-end`}
            type="time"
            value={end}
            onChange={(event) => {
              setEnd(event.target.value)
              setTouched(true)
            }}
            aria-invalid={showInvalid}
            aria-describedby={`${ids}-window`}
            required
          />
        </div>
      </fieldset>
      <p
        id={`${ids}-window`}
        className={cn('-mt-2 text-sm', showInvalid ? 'text-bad' : 'text-muted')}
        role={showInvalid ? 'alert' : undefined}
      >
        {showInvalid
          ? invalid
          : minutes !== null && minutes > 0
            ? `Duration: ${formatDuration(minutes)}`
            : ' '}
      </p>

      {error !== null && (
        <p className="rounded-lg bg-bad/10 px-3 py-2 text-sm text-bad" role="alert">
          {error}
        </p>
      )}

      <div className="flex flex-wrap items-center justify-between gap-2">
        {editing ? (
          <div className="flex flex-wrap gap-2">
            {block.status === 'scheduled' && (
              <>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  disabled={saving}
                  onClick={() =>
                    run(() => completeTimeBlock(block.id), 'Couldn’t mark the session done.')
                  }
                >
                  <CalendarCheck className="size-4" aria-hidden />
                  Session done
                </Button>
                {hasStarted(block) ? (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    disabled={saving}
                    onClick={() => run(() => missTimeBlock(block.id), 'Couldn’t mark the session.')}
                  >
                    <Ban className="size-4" aria-hidden />
                    Didn’t happen
                  </Button>
                ) : (
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    disabled={saving}
                    onClick={() =>
                      run(() => cancelTimeBlock(block.id), 'Couldn’t cancel the session.')
                    }
                  >
                    <Ban className="size-4" aria-hidden />
                    Cancel session
                  </Button>
                )}
              </>
            )}
            {confirmDelete ? (
              <Button
                type="button"
                variant="destructive"
                size="sm"
                disabled={saving}
                onClick={() => run(() => deleteTimeBlock(block.id), 'Couldn’t delete the session.')}
              >
                <Trash2 className="size-4" aria-hidden />
                Delete for good
              </Button>
            ) : (
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="text-bad hover:text-bad"
                disabled={saving}
                onClick={() => setConfirmDelete(true)}
                title="Only for a mistaken entry. To keep a record, cancel the session."
              >
                <Trash2 className="size-4" aria-hidden />
                Delete
              </Button>
            )}
          </div>
        ) : (
          <span />
        )}
        <div className="ml-auto flex gap-2">
          <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          <Button type="submit" disabled={saving}>
            {editing ? 'Save time' : 'Plan session'}
          </Button>
        </div>
      </div>
    </form>
  )
}

function ChosenTask({ task }: { task: DialogTask }) {
  return (
    <div className="flex items-start gap-2 rounded-xl border border-line bg-raised/60 px-3 py-2">
      <TaskMark status={task.status} className="mt-0.5" />
      <div className="min-w-0">
        <p className="text-sm font-medium text-ink">{task.title}</p>
        <PathLine task={task} />
      </div>
    </div>
  )
}

/** Search over organized tasks that are still open. */
function TaskPicker({
  picked,
  onPick,
}: {
  picked: DialogTask | null
  onPick: (task: DialogTask | null) => void
}) {
  const [tasks, setTasks] = useState<QuestTask[] | null>(null)
  const [failed, setFailed] = useState(false)
  const [query, setQuery] = useState('')
  const searchId = useId()

  useEffect(() => {
    let cancelled = false
    listQuestTasks()
      .then((rows) => {
        if (!cancelled) setTasks(rows)
      })
      .catch(() => {
        if (!cancelled) setFailed(true)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const matches = useMemo(() => {
    const open = (tasks ?? []).filter(
      (task) => !task.inbox && task.status !== 'completed' && task.archived_at === null,
    )
    const needle = query.trim().toLowerCase()
    if (!needle) return open
    return open.filter((task) =>
      `${task.title} ${pathLabel(task.path)}`.toLowerCase().includes(needle),
    )
  }, [tasks, query])

  if (picked !== null) {
    return (
      <div className="flex flex-col gap-1">
        <span className="text-xs font-medium text-muted">Task</span>
        <div className="flex items-start gap-2">
          <div className="min-w-0 flex-1">
            <ChosenTask task={picked} />
          </div>
          <Button type="button" variant="ghost" size="sm" onClick={() => onPick(null)}>
            Change
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-1">
      <Label htmlFor={searchId}>Task</Label>
      <div className="relative">
        <Search
          className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted"
          aria-hidden
        />
        <Input
          id={searchId}
          className="pl-9"
          placeholder="Search your tasks"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          autoComplete="off"
        />
      </div>
      <div
        className="mt-1 max-h-56 overflow-y-auto rounded-xl border border-line"
        role="listbox"
        aria-label="Tasks"
      >
        {failed ? (
          <p className="px-3 py-3 text-sm text-bad">Couldn’t load your tasks.</p>
        ) : tasks === null ? (
          <p className="px-3 py-3 text-sm text-muted">Loading tasks…</p>
        ) : matches.length === 0 ? (
          <p className="px-3 py-3 text-sm text-muted">
            {query ? 'No open task matches.' : 'No open tasks yet. Add one on a quest first.'}
          </p>
        ) : (
          matches.slice(0, 30).map((task) => (
            <button
              key={task.id}
              type="button"
              role="option"
              aria-selected={false}
              className="flex w-full items-start gap-2 border-b border-line px-3 py-2 text-left last:border-b-0 hover:bg-raised focus-visible:bg-raised"
              onClick={() => onPick(task)}
            >
              <TaskMark status={task.status} className="mt-0.5" />
              <span className="min-w-0">
                <span className="block text-sm text-ink">{task.title}</span>
                <PathLine task={task} />
              </span>
            </button>
          ))
        )}
      </div>
    </div>
  )
}
