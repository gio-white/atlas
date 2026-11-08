import { type ReactNode, useState } from 'react'

import { ApiError, cancelTimeBlock, completeTimeBlock, type ScheduledBlock } from '@/lib/api'

import type { SessionActions } from './SessionRow'
import { TimeBlockDialog } from './TimeBlockDialog'
import { useOutcomeAchieved } from './useOutcome'

/**
 * The session controls Today and Home share. "Session done" calls only the block-complete
 * endpoint; "Outcome achieved" calls only the task update. A status line confirms each.
 */
export function useSessionActions(refresh: () => void | Promise<void>): {
  actions: SessionActions
  status: string | null
  error: string | null
  dialogs: ReactNode
} {
  const [busy, setBusy] = useState(false)
  const [status, setStatus] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState<ScheduledBlock | null>(null)
  const outcome = useOutcomeAchieved(async () => {
    setStatus('Task completed.')
    await refresh()
  })

  async function run(action: () => Promise<unknown>, done: string, failed: string) {
    setBusy(true)
    setError(null)
    setStatus(null)
    try {
      await action()
      setStatus(done)
      await refresh()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : failed)
    } finally {
      setBusy(false)
    }
  }

  const actions: SessionActions = {
    busy: busy || outcome.pendingId !== null,
    onSessionDone: ({ block, task }) =>
      void run(
        () => completeTimeBlock(block.id),
        `Session done. “${task.title}” stays open until you mark the outcome.`,
        'Couldn’t mark the session done.',
      ),
    onCancel: ({ block }) =>
      void run(
        () => cancelTimeBlock(block.id),
        'Session cancelled.',
        'Couldn’t cancel the session.',
      ),
    onOutcome: ({ task }) => {
      setStatus(null)
      outcome.request(task)
    },
    onEdit: (item) => setEditing(item),
  }

  const dialogs = (
    <>
      {outcome.dialog}
      <TimeBlockDialog
        open={editing !== null}
        onOpenChange={(open) => !open && setEditing(null)}
        block={editing?.block}
        task={editing?.task}
        onSaved={async () => {
          setStatus('Session updated.')
          await refresh()
        }}
      />
    </>
  )

  return { actions, status, error: error ?? outcome.error, dialogs }
}
