import { CircleCheck, RotateCcw } from 'lucide-react'
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
  completeAmbition,
  completeMilestone,
  completeQuestGoal,
  completeSideQuest,
  type ItemRef,
  type QuestStatus,
  reopenAmbition,
  reopenMilestone,
  reopenQuestGoal,
  reopenSideQuest,
} from '@/lib/api'
import { countLabel, KIND_LABELS } from '@/lib/quests'
import { cn } from '@/lib/utils'

import { LevelIcon } from './QuestVisuals'
import { errorMessage } from './useQuestView'

export type CompletableKind = 'ambition' | 'goal' | 'milestone' | 'side_quest'

export type CompletableItem = {
  id: number
  title: string
  status: QuestStatus
  eligible: boolean
  open_children: ItemRef[]
  completed_with_open_items: boolean
}

const COMPLETE: Record<CompletableKind, (id: number, override: boolean) => Promise<unknown>> = {
  ambition: completeAmbition,
  goal: completeQuestGoal,
  milestone: completeMilestone,
  side_quest: completeSideQuest,
}
const REOPEN: Record<CompletableKind, (id: number) => Promise<unknown>> = {
  ambition: reopenAmbition,
  goal: reopenQuestGoal,
  milestone: reopenMilestone,
  side_quest: reopenSideQuest,
}

/**
 * Shows whether an item can be completed (from the API's `eligible` and `open_children`) and
 * completes it only on an explicit click. Completing with open items asks first.
 */
export function CompletionControl({
  kind,
  item,
  onChanged,
  compact = false,
}: {
  kind: CompletableKind
  item: CompletableItem
  onChanged: () => void
  compact?: boolean
}) {
  const [confirming, setConfirming] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const level = KIND_LABELS[kind].toLowerCase()
  const open = item.open_children

  async function act(action: () => Promise<unknown>, failure: string) {
    setBusy(true)
    setError(null)
    try {
      await action()
      setConfirming(false)
      onChanged()
    } catch (caught) {
      setError(errorMessage(caught, failure))
    } finally {
      setBusy(false)
    }
  }

  if (item.status === 'archived') return null

  if (item.status === 'completed') {
    return (
      <div
        className={cn(
          'flex flex-wrap items-center gap-3',
          !compact && 'rounded-xl border border-good/30 bg-good/8 px-4 py-3',
        )}
      >
        <CircleCheck className="size-5 shrink-0 text-good" aria-hidden />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-ink">
            {item.completed_with_open_items ? 'Completed with open items' : 'Completed'}
          </p>
          {item.completed_with_open_items && !compact && (
            <p className="text-xs text-muted">
              You completed this {level} with {countLabel(open.length, 'open item')}. They keep
              their status.
            </p>
          )}
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={busy}
          onClick={() => void act(() => REOPEN[kind](item.id), `Couldn't reopen the ${level}.`)}
        >
          <RotateCcw className="size-3.5" aria-hidden />
          Reopen
        </Button>
        {error !== null && (
          <p role="alert" className="w-full text-sm text-bad">
            {error}
          </p>
        )}
      </div>
    )
  }

  const summary = item.eligible
    ? 'Everything here is done. Complete it when you are ready.'
    : open.length === 0
      ? 'Nothing is under this yet.'
      : `${countLabel(open.length, 'item')} still open.`

  return (
    <div
      className={cn(
        'flex flex-wrap items-center gap-3',
        !compact && 'rounded-xl border border-line bg-raised/50 px-4 py-3',
      )}
    >
      <div className="min-w-0 flex-1">
        {!compact && <p className="text-sm font-medium text-ink">Completion</p>}
        <p className="text-xs text-muted">{summary}</p>
      </div>
      {item.eligible ? (
        <Button
          type="button"
          size="sm"
          className="bg-good hover:bg-good/90"
          disabled={busy}
          onClick={() =>
            void act(() => COMPLETE[kind](item.id, false), `Couldn't complete the ${level}.`)
          }
        >
          <CircleCheck className="size-3.5" aria-hidden />
          Complete {level}
        </Button>
      ) : (
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={busy}
          onClick={() => setConfirming(true)}
        >
          Complete anyway…
        </Button>
      )}
      {error !== null && !confirming && (
        <p role="alert" className="w-full text-sm text-bad">
          {error}
        </p>
      )}
      <Dialog open={confirming} onOpenChange={setConfirming}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Complete with open items?</DialogTitle>
            <DialogDescription>
              {open.length === 0
                ? `“${item.title}” has nothing under it yet. You can still mark it complete.`
                : `“${item.title}” isn't finished yet. These stay exactly as they are:`}
            </DialogDescription>
          </DialogHeader>
          {open.length > 0 && (
            <ul className="flex max-h-60 flex-col gap-1 overflow-y-auto" aria-label="Open items">
              {open.map((child) => (
                <li
                  key={`${child.kind}-${child.id}`}
                  className="flex items-center gap-2 rounded-lg bg-raised/60 px-3 py-2 text-sm"
                >
                  <LevelIcon kind={child.kind} label />
                  <span className="min-w-0 flex-1 truncate text-ink">{child.title}</span>
                </li>
              ))}
            </ul>
          )}
          <p className="text-xs text-muted">
            The {level} will show “Completed with open items”. You can reopen it any time.
          </p>
          {error !== null && (
            <p role="alert" className="text-sm text-bad">
              {error}
            </p>
          )}
          <div className="flex flex-wrap justify-end gap-2">
            <Button type="button" variant="ghost" onClick={() => setConfirming(false)}>
              Keep working
            </Button>
            <Button
              type="button"
              disabled={busy}
              onClick={() =>
                void act(() => COMPLETE[kind](item.id, true), `Couldn't complete the ${level}.`)
              }
            >
              Complete anyway
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
