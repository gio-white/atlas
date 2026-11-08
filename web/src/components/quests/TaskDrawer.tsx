import * as DialogPrimitive from '@radix-ui/react-dialog'
import { Archive, ArchiveRestore, FolderInput, X } from 'lucide-react'
import {
  createContext,
  type FormEvent,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'
import { Link } from 'react-router-dom'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import {
  getQuestTask,
  organizeTask,
  type QuestTaskDetail,
  type TaskPriority,
  type TaskStatus,
  updateQuestTask,
} from '@/lib/api'
import {
  KIND_LABELS,
  notifyInboxChanged,
  PRIORITY_LABELS,
  pathLabel,
  shareLabel,
  TASK_STATUS_LABELS,
  taskContextHref,
} from '@/lib/quests'
import { cn } from '@/lib/utils'

import { OrganizePicker } from './OrganizePicker'
import { LevelIcon } from './QuestVisuals'
import { TaskTimeBlocks } from './time/TaskTimeBlocks'
import { errorMessage } from './useQuestView'

/**
 * Renders extra content inside the drawer for the open task. The sessions section (Q3's
 * `components/quests/time/TaskTimeBlocks.tsx`) plugs in here; see `TaskDrawerProvider`.
 */
export type TaskDrawerSection = (task: QuestTaskDetail, onChanged: () => void) => ReactNode

/**
 * The drawer's default sessions section: a task's time blocks with planned effort. The drawer
 * hides it for Inbox tasks: they are scheduled once organized, like the time-block picker.
 */
export const sessionsSection: TaskDrawerSection = (task, onChanged) => (
  <TaskTimeBlocks taskId={task.id} onChanged={onChanged} />
)

type DrawerContext = { openTask: (id: number) => void }

const TaskDrawerContext = createContext<DrawerContext>({ openTask: () => {} })

/** Open the task drawer from any task row under a `TaskDrawerProvider`. */
export function useOpenTask(): (id: number) => void {
  return useContext(TaskDrawerContext).openTask
}

/**
 * Hosts one task drawer for a screen. `onChanged` runs after every change made in the drawer
 * so the screen can reload its read model.
 */
export function TaskDrawerProvider({
  onChanged,
  extraSection,
  children,
}: {
  onChanged: () => void
  extraSection?: TaskDrawerSection
  children: ReactNode
}) {
  const [taskId, setTaskId] = useState<number | null>(null)
  const value = useMemo(() => ({ openTask: setTaskId }), [])
  return (
    <TaskDrawerContext.Provider value={value}>
      {children}
      <TaskDrawer
        taskId={taskId}
        onClose={() => setTaskId(null)}
        onChanged={onChanged}
        extraSection={extraSection ?? sessionsSection}
      />
    </TaskDrawerContext.Provider>
  )
}

const STATUSES: TaskStatus[] = ['todo', 'in_progress', 'completed']
const PRIORITIES: TaskPriority[] = ['low', 'normal', 'high']

type Draft = {
  title: string
  description: string
  priority: TaskPriority
  estimate: string
  due: string
  weight: string
}

function draftOf(task: QuestTaskDetail): Draft {
  return {
    title: task.title,
    description: task.description ?? '',
    priority: task.priority,
    estimate: task.estimate_minutes === null ? '' : String(task.estimate_minutes),
    due: task.due_on ?? '',
    weight: task.weight === null ? '' : String(task.weight),
  }
}

function positiveOrNull(value: string): number | null | 'invalid' {
  if (value.trim() === '') return null
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 'invalid'
}

export function TaskDrawer({
  taskId,
  onClose,
  onChanged,
  extraSection,
}: {
  taskId: number | null
  onClose: () => void
  onChanged: () => void
  extraSection?: TaskDrawerSection
}) {
  const [task, setTask] = useState<QuestTaskDetail | null>(null)
  const [draft, setDraft] = useState<Draft | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [moving, setMoving] = useState(false)
  const [saved, setSaved] = useState(false)

  const refresh = useCallback(async (id: number) => {
    const next = await getQuestTask(id)
    setTask(next)
    setDraft(draftOf(next))
  }, [])

  useEffect(() => {
    setTask(null)
    setDraft(null)
    setError(null)
    setSaved(false)
    if (taskId === null) return
    refresh(taskId).catch((caught: unknown) =>
      setError(errorMessage(caught, "Couldn't open this task.")),
    )
  }, [taskId, refresh])

  async function run(action: () => Promise<QuestTaskDetail>, failure: string) {
    setBusy(true)
    setError(null)
    setSaved(false)
    try {
      const next = await action()
      setTask(next)
      setDraft(draftOf(next))
      onChanged()
      notifyInboxChanged()
      return true
    } catch (caught) {
      setError(errorMessage(caught, failure))
      return false
    } finally {
      setBusy(false)
    }
  }

  async function onSave(event: FormEvent) {
    event.preventDefault()
    if (task === null || draft === null) return
    const title = draft.title.trim()
    if (title === '') {
      setError('Give the task a title.')
      return
    }
    const estimate = positiveOrNull(draft.estimate)
    const weight = positiveOrNull(draft.weight)
    if (estimate === 'invalid') {
      setError('The estimate is a number of minutes above zero.')
      return
    }
    if (weight === 'invalid') {
      setError('The weight is a number above zero, or leave it empty.')
      return
    }
    const ok = await run(
      () =>
        updateQuestTask(task.id, {
          title,
          description: draft.description.trim() === '' ? null : draft.description.trim(),
          priority: draft.priority,
          estimate_minutes: estimate === null ? null : Math.round(estimate),
          due_on: draft.due === '' ? null : draft.due,
          weight,
        }),
      "Couldn't save the task.",
    )
    if (ok) setSaved(true)
  }

  const dirty = task !== null && draft !== null && !sameDraft(draftOf(task), draft)
  const contextHref = task === null ? null : taskContextHref(task)
  const share = task === null ? null : shareLabel(task.weight_share)

  return (
    <DialogPrimitive.Root open={taskId !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogPrimitive.Portal>
        <DialogPrimitive.Overlay className="fixed inset-0 z-50 bg-black/40" />
        <DialogPrimitive.Content
          className="fixed inset-y-0 right-0 z-50 flex w-full max-w-md flex-col overflow-y-auto border-l border-line bg-surface shadow-[var(--shadow-card)] sm:rounded-l-2xl"
          aria-describedby={undefined}
        >
          <div className="flex items-start gap-3 border-b border-line px-5 py-4">
            <LevelIcon kind="task" className="mt-1" />
            <DialogPrimitive.Title className="min-w-0 flex-1 text-lg font-semibold tracking-tight text-ink">
              {task?.title ?? 'Task'}
            </DialogPrimitive.Title>
            <DialogPrimitive.Close
              className="-mt-2 -mr-2 inline-flex size-11 items-center justify-center rounded-lg text-muted hover:bg-raised hover:text-ink"
              aria-label="Close"
            >
              <X className="size-4" aria-hidden />
            </DialogPrimitive.Close>
          </div>

          {error !== null && (
            <p role="alert" className="mx-5 mt-4 rounded-lg bg-bad/10 px-3 py-2 text-sm text-bad">
              {error}
            </p>
          )}
          {task === null || draft === null ? (
            error === null && (
              <p role="status" className="px-5 py-6 text-sm text-muted">
                Loading…
              </p>
            )
          ) : (
            <div className="flex flex-col gap-6 px-5 py-5">
              <section aria-labelledby="task-status-heading" className="flex flex-col gap-2">
                <h3 id="task-status-heading" className="text-xs font-medium text-muted">
                  Status
                </h3>
                <div className="grid grid-cols-3 gap-1 rounded-xl bg-raised p-1">
                  {STATUSES.map((status) => (
                    <button
                      key={status}
                      type="button"
                      disabled={busy}
                      aria-pressed={task.status === status}
                      className={cn(
                        'min-h-10 rounded-lg px-2 text-sm font-medium',
                        task.status === status
                          ? status === 'completed'
                            ? 'bg-good text-on-primary'
                            : 'bg-surface text-ink shadow-sm'
                          : 'text-muted hover:text-ink',
                      )}
                      onClick={() => {
                        if (task.status === status) return
                        void run(
                          () => updateQuestTask(task.id, { status }),
                          "Couldn't change the status.",
                        )
                      }}
                    >
                      {TASK_STATUS_LABELS[status]}
                    </button>
                  ))}
                </div>
                <p className="text-xs text-muted">
                  {task.status === 'completed'
                    ? 'Done. Pick another status to reopen it.'
                    : 'A task is done only when you mark it Done.'}
                </p>
              </section>

              <form className="flex flex-col gap-4" onSubmit={onSave}>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="task-title">Title</Label>
                  <Input
                    id="task-title"
                    value={draft.title}
                    onChange={(event) => setDraft({ ...draft, title: event.target.value })}
                  />
                </div>
                <div className="flex flex-col gap-1.5">
                  <Label htmlFor="task-description">Description</Label>
                  <textarea
                    id="task-description"
                    rows={3}
                    className="w-full rounded-lg border border-line bg-canvas px-3 py-2 text-sm text-ink placeholder:text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                    placeholder="What does done look like?"
                    value={draft.description}
                    onChange={(event) => setDraft({ ...draft, description: event.target.value })}
                  />
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="task-priority">Priority</Label>
                    <Select
                      id="task-priority"
                      value={draft.priority}
                      onChange={(event) =>
                        setDraft({ ...draft, priority: event.target.value as TaskPriority })
                      }
                    >
                      {PRIORITIES.map((priority) => (
                        <option key={priority} value={priority}>
                          {PRIORITY_LABELS[priority]}
                        </option>
                      ))}
                    </Select>
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="task-due">Due date</Label>
                    <Input
                      id="task-due"
                      type="date"
                      value={draft.due}
                      onChange={(event) => setDraft({ ...draft, due: event.target.value })}
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="task-estimate">Estimate (minutes)</Label>
                    <Input
                      id="task-estimate"
                      type="number"
                      inputMode="numeric"
                      min={1}
                      placeholder="None"
                      value={draft.estimate}
                      onChange={(event) => setDraft({ ...draft, estimate: event.target.value })}
                    />
                  </div>
                  <div className="flex flex-col gap-1.5">
                    <Label htmlFor="task-weight">Weight</Label>
                    <Input
                      id="task-weight"
                      type="number"
                      inputMode="decimal"
                      min={0}
                      step="any"
                      placeholder="1"
                      value={draft.weight}
                      disabled={task.parent === null}
                      onChange={(event) => setDraft({ ...draft, weight: event.target.value })}
                    />
                  </div>
                </div>
                <p className="-mt-2 text-xs text-muted">
                  {task.parent === null
                    ? 'Weight matters once the task belongs somewhere.'
                    : `Counts for ${share ?? '—'} of ${task.parent.title}. Empty counts as 1.`}
                </p>
                <div className="flex items-center gap-3">
                  <Button type="submit" disabled={busy || !dirty}>
                    Save changes
                  </Button>
                  {saved && !dirty && (
                    <span role="status" className="text-sm text-muted">
                      Saved
                    </span>
                  )}
                </div>
              </form>

              <section aria-labelledby="task-parent-heading" className="flex flex-col gap-2">
                <h3 id="task-parent-heading" className="text-xs font-medium text-muted">
                  Belongs to
                </h3>
                <div className="flex items-center gap-3 rounded-xl border border-line px-3 py-2">
                  {task.parent === null ? (
                    <p className="min-w-0 flex-1 text-sm text-ink">
                      {task.inbox ? 'Inbox, not sorted yet' : 'Standalone side quest'}
                    </p>
                  ) : (
                    <div className="flex min-w-0 flex-1 items-center gap-2">
                      <LevelIcon kind={task.parent.kind} />
                      <div className="min-w-0">
                        {contextHref === null ? (
                          <p className="truncate text-sm text-ink">{task.parent.title}</p>
                        ) : (
                          <Link
                            to={contextHref}
                            className="block truncate text-sm text-ink hover:underline"
                            onClick={onClose}
                          >
                            {task.parent.title}
                          </Link>
                        )}
                        <p className="truncate text-xs text-muted">
                          {KIND_LABELS[task.parent.kind]}
                          {task.path.length > 1 && ` · ${pathLabel(task.path.slice(0, -1))}`}
                        </p>
                      </div>
                    </div>
                  )}
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={busy}
                    onClick={() => setMoving(true)}
                  >
                    <FolderInput className="size-3.5" aria-hidden />
                    Move…
                  </Button>
                </div>
                {!task.standalone && (
                  <button
                    type="button"
                    className="self-start text-xs text-muted underline-offset-2 hover:text-ink hover:underline"
                    disabled={busy}
                    onClick={() =>
                      void run(
                        () => organizeTask(task.id, { standalone: true }),
                        "Couldn't move the task.",
                      )
                    }
                  >
                    Make it a standalone side quest
                  </button>
                )}
              </section>

              {/* Sessions: `sessionsSection` by default (TaskTimeBlocks); a provider may replace it. */}
              {extraSection !== undefined && !task.inbox && (
                <section aria-label="Sessions" data-slot="task-sessions">
                  {extraSection(task, () => {
                    void refresh(task.id)
                    onChanged()
                  })}
                </section>
              )}

              <div className="border-t border-line pt-4">
                <Button
                  type="button"
                  variant="ghost"
                  disabled={busy}
                  onClick={() =>
                    void run(
                      () => updateQuestTask(task.id, { archived: task.archived_at === null }),
                      "Couldn't archive the task.",
                    )
                  }
                >
                  {task.archived_at === null ? (
                    <>
                      <Archive className="size-4" aria-hidden />
                      Archive task
                    </>
                  ) : (
                    <>
                      <ArchiveRestore className="size-4" aria-hidden />
                      Restore task
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}
          {task !== null && (
            <OrganizePicker
              open={moving}
              onOpenChange={setMoving}
              title="Move task"
              description="Pick where this task belongs. It keeps its status and history."
              current={task.parent}
              onPick={async (target) => {
                const ok = await run(
                  () => organizeTask(task.id, { parent_kind: target.kind, parent_id: target.id }),
                  "Couldn't move the task.",
                )
                if (ok) setMoving(false)
              }}
            />
          )}
        </DialogPrimitive.Content>
      </DialogPrimitive.Portal>
    </DialogPrimitive.Root>
  )
}

function sameDraft(a: Draft, b: Draft): boolean {
  return (
    a.title === b.title &&
    a.description === b.description &&
    a.priority === b.priority &&
    a.estimate === b.estimate &&
    a.due === b.due &&
    a.weight === b.weight
  )
}
