import { CircleCheckBig } from 'lucide-react'
import { type ReactNode, useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { ApiError, type QuestTask, updateQuestTask } from '@/lib/api'
import { markOutcomeLearned, outcomeLearned } from '@/lib/timeBlocks'

type OutcomeTask = Pick<QuestTask, 'id' | 'title'>

/**
 * "Outcome achieved" completes the task (never the session). The first time, a short
 * confirmation explains the difference from "Session done"; after that it acts at once.
 */
export function useOutcomeAchieved(onDone: () => void | Promise<void>): {
  request: (task: OutcomeTask) => void
  pendingId: number | null
  error: string | null
  dialog: ReactNode
} {
  const [asking, setAsking] = useState<OutcomeTask | null>(null)
  const [pendingId, setPendingId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function complete(task: OutcomeTask) {
    setPendingId(task.id)
    setError(null)
    try {
      await updateQuestTask(task.id, { status: 'completed' })
      await onDone()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Couldn’t complete the task.')
    } finally {
      setPendingId(null)
    }
  }

  function request(task: OutcomeTask) {
    if (outcomeLearned()) void complete(task)
    else setAsking(task)
  }

  const dialog = (
    <Dialog open={asking !== null} onOpenChange={(open) => !open && setAsking(null)}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <CircleCheckBig className="size-5 text-good" aria-hidden />
            Complete the task?
          </DialogTitle>
          <DialogDescription>
            <strong className="font-medium text-ink">Outcome achieved</strong> marks “
            {asking?.title}” as done. If you only finished a work session, use{' '}
            <strong className="font-medium text-ink">Session done</strong> instead: the task stays
            open.
          </DialogDescription>
        </DialogHeader>
        <div className="flex flex-wrap justify-end gap-2">
          <Button variant="ghost" onClick={() => setAsking(null)}>
            Not yet
          </Button>
          <Button
            onClick={() => {
              const task = asking
              setAsking(null)
              if (task === null) return
              markOutcomeLearned()
              void complete(task)
            }}
          >
            Complete task
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )

  return { request, pendingId, error, dialog }
}
