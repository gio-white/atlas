import { Archive, FolderInput, Pencil, Sparkles, SquareArrowOutUpRight } from 'lucide-react'
import { type FormEvent, useState } from 'react'

import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  organizeTask,
  type PromoteResult,
  type QuestTask,
  type TaskOrganize,
  updateQuestTask,
} from '@/lib/api'
import { notifyInboxChanged, questDateLabel } from '@/lib/quests'

import { OrganizePicker } from './OrganizePicker'
import { PromoteDialog } from './PromoteDialog'
import { useOpenTask } from './TaskDrawer'
import { errorMessage } from './useQuestView'

export type InboxOutcome =
  | { kind: 'organized'; where: string }
  | { kind: 'standalone' }
  | { kind: 'promoted'; result: PromoteResult }
  | { kind: 'archived' }
  | { kind: 'edited' }

/** One Inbox task with every way to sort it. The task keeps its id when organized. */
export function InboxItem({
  task,
  onDone,
}: {
  task: QuestTask
  onDone: (outcome: InboxOutcome) => void
}) {
  const openTask = useOpenTask()
  const [editing, setEditing] = useState(false)
  const [title, setTitle] = useState(task.title)
  const [description, setDescription] = useState(task.description ?? '')
  const [organizing, setOrganizing] = useState(false)
  const [promoting, setPromoting] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function act(action: () => Promise<unknown>, outcome: InboxOutcome, failure: string) {
    setBusy(true)
    setError(null)
    try {
      await action()
      notifyInboxChanged()
      onDone(outcome)
      return true
    } catch (caught) {
      setError(errorMessage(caught, failure))
      return false
    } finally {
      setBusy(false)
    }
  }

  async function save(event: FormEvent) {
    event.preventDefault()
    const trimmed = title.trim()
    if (trimmed === '') {
      setError('Give the task a title.')
      return
    }
    const ok = await act(
      () =>
        updateQuestTask(task.id, {
          title: trimmed,
          description: description.trim() === '' ? null : description.trim(),
        }),
      { kind: 'edited' },
      "Couldn't save the task.",
    )
    if (ok) setEditing(false)
  }

  function organize(body: TaskOrganize, outcome: InboxOutcome) {
    return act(() => organizeTask(task.id, body), outcome, "Couldn't organize the task.")
  }

  return (
    <li
      className="flex flex-col gap-2 rounded-2xl border border-line bg-surface px-4 py-3 shadow-[var(--shadow-card)]"
      aria-label={task.title}
    >
      {editing ? (
        <form className="flex flex-col gap-2" onSubmit={save}>
          <Input
            autoFocus
            aria-label="Title"
            value={title}
            onChange={(event) => setTitle(event.target.value)}
          />
          <textarea
            aria-label="Description"
            rows={2}
            placeholder="Add a note (optional)"
            className="w-full rounded-lg border border-line bg-canvas px-3 py-2 text-sm text-ink placeholder:text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
          <div className="flex gap-2">
            <Button type="submit" size="sm" disabled={busy}>
              Save
            </Button>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={() => {
                setEditing(false)
                setTitle(task.title)
                setDescription(task.description ?? '')
              }}
            >
              Cancel
            </Button>
          </div>
        </form>
      ) : (
        <div className="flex items-start gap-2">
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-ink">{task.title}</p>
            {task.description !== null && (
              <p className="mt-0.5 text-sm text-muted">{task.description}</p>
            )}
            <p className="mt-0.5 text-xs text-muted">Added {questDateLabel(task.created_at)}</p>
          </div>
          <button
            type="button"
            aria-label={`Edit ${task.title}`}
            className="inline-flex size-9 shrink-0 items-center justify-center rounded-lg text-muted hover:bg-raised hover:text-ink"
            onClick={() => setEditing(true)}
          >
            <Pencil className="size-3.5" aria-hidden />
          </button>
          <button
            type="button"
            aria-label={`Open details for ${task.title}`}
            className="inline-flex size-9 shrink-0 items-center justify-center rounded-lg text-muted hover:bg-raised hover:text-ink"
            onClick={() => openTask(task.id)}
          >
            <SquareArrowOutUpRight className="size-3.5" aria-hidden />
          </button>
        </div>
      )}
      {!editing && (
        <div className="flex flex-wrap gap-1.5">
          <Button
            type="button"
            size="sm"
            className="bg-accent hover:bg-accent/90"
            disabled={busy}
            onClick={() => setOrganizing(true)}
          >
            <FolderInput className="size-3.5" aria-hidden />
            Organize…
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={busy}
            onClick={() => void organize({ standalone: true }, { kind: 'standalone' })}
          >
            Make standalone
          </Button>
          <Button
            type="button"
            variant="outline"
            size="sm"
            disabled={busy}
            onClick={() => setPromoting(true)}
          >
            <Sparkles className="size-3.5" aria-hidden />
            Turn into…
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            disabled={busy}
            onClick={() =>
              void act(
                () => updateQuestTask(task.id, { archived: true }),
                { kind: 'archived' },
                "Couldn't archive the task.",
              )
            }
          >
            <Archive className="size-3.5" aria-hidden />
            Archive
          </Button>
        </div>
      )}
      {error !== null && (
        <p role="alert" className="text-sm text-bad">
          {error}
        </p>
      )}
      <OrganizePicker
        open={organizing}
        onOpenChange={setOrganizing}
        title="Organize task"
        description="Pick where it belongs. It's the same task, just sorted."
        onPick={async (target) => {
          const ok = await organize(
            { parent_kind: target.kind, parent_id: target.id },
            { kind: 'organized', where: target.title },
          )
          if (ok) setOrganizing(false)
        }}
      />
      <PromoteDialog
        task={task}
        open={promoting}
        onOpenChange={setPromoting}
        onPromoted={(result) => {
          notifyInboxChanged()
          onDone({ kind: 'promoted', result })
        }}
      />
    </li>
  )
}
