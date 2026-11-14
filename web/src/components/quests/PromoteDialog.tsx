import { useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  ApiError,
  type PromoteKind,
  type PromoteResult,
  promoteTask,
  type QuestTask,
} from '@/lib/api'
import { KIND_LABELS, PROMOTE_KINDS, PROMOTE_PARENTS, type QuestTarget } from '@/lib/quests'
import { cn } from '@/lib/utils'

import { OrganizePicker } from './OrganizePicker'
import { LevelIcon } from './QuestVisuals'
import { errorMessage } from './useQuestView'

const HINTS: Record<PromoteKind, string> = {
  ambition: 'A broad direction you want to grow in',
  goal: 'A concrete outcome, on its own or under an ambition',
  side_quest: 'Independent work with its own chapters and tasks',
  milestone: 'An important result inside a goal',
  chapter: 'A batch of tasks inside a milestone or side quest',
}

export const HAS_SESSIONS_MESSAGE =
  "This task already has sessions planned, so it can't become something else. Organize it instead: it keeps its sessions."

function parentPrompt(kind: PromoteKind): string {
  if (kind === 'goal') return 'Under an ambition (optional)'
  if (kind === 'milestone') return 'Choose a goal'
  return 'Choose a milestone or side quest'
}

/**
 * Turn an Inbox task into an ambition, goal, side quest, milestone, or chapter. The task is
 * replaced by the new item, so a task with sessions is refused (plan D6).
 */
export function PromoteDialog({
  task,
  open,
  onOpenChange,
  onPromoted,
}: {
  task: QuestTask
  open: boolean
  onOpenChange: (open: boolean) => void
  onPromoted: (result: PromoteResult) => void
}) {
  const [kind, setKind] = useState<PromoteKind>('goal')
  const [parent, setParent] = useState<QuestTarget | null>(null)
  const [picking, setPicking] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const hasSessions = task.block_count > 0
  const rule = PROMOTE_PARENTS[kind]
  const missingParent = rule.required && parent === null

  async function submit() {
    setBusy(true)
    setError(null)
    try {
      const result = await promoteTask(task.id, {
        kind,
        parent_kind: parent?.kind ?? null,
        parent_id: parent?.id ?? null,
      })
      onPromoted(result)
      onOpenChange(false)
    } catch (caught) {
      // The API refuses a task with time blocks (400); say so in plain words.
      setError(
        caught instanceof ApiError && caught.status === 400 && /time block/i.test(caught.message)
          ? HAS_SESSIONS_MESSAGE
          : errorMessage(caught, `Couldn't turn it into a ${KIND_LABELS[kind].toLowerCase()}.`),
      )
    } finally {
      setBusy(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Turn into…</DialogTitle>
          <DialogDescription>
            “{task.title}” becomes the new item, with its title and description. It leaves your
            Inbox.
          </DialogDescription>
        </DialogHeader>
        {hasSessions ? (
          <p role="alert" className="rounded-lg bg-warn/12 px-3 py-2 text-sm text-ink">
            {HAS_SESSIONS_MESSAGE}
          </p>
        ) : (
          <>
            <fieldset className="flex flex-col gap-1.5">
              <legend className="mb-1 text-xs font-medium text-muted">Turn it into</legend>
              {PROMOTE_KINDS.map((option) => (
                <label
                  key={option}
                  className={cn(
                    'flex min-h-12 cursor-pointer items-center gap-3 rounded-xl border px-3 py-2',
                    kind === option ? 'border-accent bg-accent/8' : 'border-line hover:bg-raised',
                  )}
                >
                  <input
                    type="radio"
                    name="promote-kind"
                    value={option}
                    checked={kind === option}
                    className="sr-only"
                    onChange={() => {
                      setKind(option)
                      setParent(null)
                    }}
                  />
                  <LevelIcon kind={option} />
                  <span className="min-w-0 flex-1">
                    <span className="block text-sm font-medium text-ink">
                      {KIND_LABELS[option]}
                    </span>
                    <span className="block text-xs text-muted">{HINTS[option]}</span>
                  </span>
                </label>
              ))}
            </fieldset>
            {rule.kinds.length > 0 && (
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-medium text-muted">{parentPrompt(kind)}</span>
                {parent !== null && (
                  <span className="inline-flex items-center gap-1.5 text-sm text-ink">
                    <LevelIcon kind={parent.kind} />
                    {parent.title}
                  </span>
                )}
                <Button type="button" variant="outline" size="sm" onClick={() => setPicking(true)}>
                  {parent === null ? 'Choose…' : 'Change…'}
                </Button>
                {parent !== null && !rule.required && (
                  <Button type="button" variant="ghost" size="sm" onClick={() => setParent(null)}>
                    Clear
                  </Button>
                )}
              </div>
            )}
          </>
        )}
        {error !== null && (
          <p role="alert" className="text-sm text-bad">
            {error}
          </p>
        )}
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            type="button"
            disabled={busy || hasSessions || missingParent}
            onClick={() => void submit()}
          >
            Turn into {KIND_LABELS[kind].toLowerCase()}
          </Button>
        </div>
        <OrganizePicker
          open={picking}
          onOpenChange={setPicking}
          title={parentPrompt(kind).replace(' (optional)', '')}
          kinds={rule.kinds}
          onPick={(target) => {
            setParent(target)
            setPicking(false)
          }}
        />
      </DialogContent>
    </Dialog>
  )
}
