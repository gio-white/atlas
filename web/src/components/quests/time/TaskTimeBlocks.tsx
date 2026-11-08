import { Ban, CalendarCheck, CalendarPlus, Pencil } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  ApiError,
  cancelTimeBlock,
  completeTimeBlock,
  getQuestTask,
  type QuestTaskDetail,
  type TimeBlock,
} from '@/lib/api'
import { formatMinutes } from '@/lib/format'
import { BLOCK_STATUS_LABELS, formatBlockDay, formatTimeRange } from '@/lib/timeBlocks'
import { cn } from '@/lib/utils'

import { TimeBlockDialog } from './TimeBlockDialog'

/**
 * A task's sessions: planned time beside the estimate, and add / done / cancel / edit /
 * delete. Built for the task drawer's `extraSection` slot:
 * `extraSection={(task) => <TaskTimeBlocks taskId={task.id} onChanged={reload} />}`.
 */
export function TaskTimeBlocks({ taskId, onChanged }: { taskId: number; onChanged?: () => void }) {
  const [task, setTask] = useState<QuestTaskDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [dialog, setDialog] = useState<{ block: TimeBlock | null } | null>(null)

  const load = useCallback(async () => {
    try {
      setTask(await getQuestTask(taskId))
      setError(null)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Couldn’t load the sessions.')
    }
  }, [taskId])

  useEffect(() => {
    void load()
  }, [load])

  async function changed() {
    await load()
    onChanged?.()
  }

  async function run(action: () => Promise<unknown>, failed: string) {
    setBusy(true)
    setError(null)
    try {
      await action()
      await changed()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : failed)
    } finally {
      setBusy(false)
    }
  }

  if (task === null) {
    return (
      <section aria-label="Sessions" className="flex flex-col gap-2">
        <h3 className="text-sm font-semibold text-ink">Sessions</h3>
        {error !== null ? (
          <p className="text-sm text-bad">{error}</p>
        ) : (
          <p className="text-sm text-muted">Loading sessions…</p>
        )}
      </section>
    )
  }

  const closed = task.status === 'completed' || task.archived_at !== null

  return (
    <section aria-labelledby={`task-${taskId}-sessions`} className="flex flex-col gap-3">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 id={`task-${taskId}-sessions`} className="text-sm font-semibold text-ink">
            Sessions
          </h3>
          <p className="text-xs text-muted" data-testid="planned-effort">
            {formatMinutes(task.planned_minutes)} planned
            {task.estimate_minutes !== null &&
              ` · estimate ${formatMinutes(task.estimate_minutes)}`}
          </p>
        </div>
        <Button
          size="sm"
          variant="outline"
          disabled={closed}
          title={closed ? 'Reopen the task to plan more sessions.' : undefined}
          onClick={() => setDialog({ block: null })}
        >
          <CalendarPlus className="size-4 text-primary" aria-hidden />
          Schedule
        </Button>
      </div>
      {closed && task.status === 'completed' && (
        <p className="text-xs text-muted">Reopen the task to plan more sessions.</p>
      )}
      {error !== null && (
        <p className="text-sm text-bad" role="alert">
          {error}
        </p>
      )}

      {task.blocks.length === 0 ? (
        <p className="rounded-xl border border-dashed border-line px-3 py-3 text-sm text-muted">
          No sessions yet. Schedule one to set aside time for this task.
        </p>
      ) : (
        <ul className="flex flex-col divide-y divide-line rounded-xl border border-line">
          {task.blocks.map((block) => (
            <li
              key={block.id}
              className={cn(
                'flex flex-wrap items-center gap-x-3 gap-y-1 px-3 py-2',
                block.status === 'cancelled' && 'text-muted',
              )}
            >
              <div className="min-w-0 flex-1">
                <p
                  className={cn(
                    'text-sm tabular-nums text-ink',
                    block.status === 'cancelled' && 'text-muted line-through',
                  )}
                >
                  {formatBlockDay(block.start_at)} · {formatTimeRange(block.start_at, block.end_at)}
                </p>
                <p className="text-xs text-muted">
                  {block.unconfirmed ? (
                    <span className="font-medium text-warn">Unconfirmed</span>
                  ) : (
                    BLOCK_STATUS_LABELS[block.status]
                  )}{' '}
                  · {formatMinutes(block.minutes)}
                </p>
              </div>
              <div className="flex gap-1">
                {block.status === 'scheduled' && (
                  <>
                    <Button
                      size="sm"
                      variant="ghost"
                      disabled={busy}
                      onClick={() =>
                        run(() => completeTimeBlock(block.id), 'Couldn’t mark the session done.')
                      }
                      aria-label={`Session done: ${formatBlockDay(block.start_at)}`}
                    >
                      <CalendarCheck className="size-4" aria-hidden />
                      Done
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      disabled={busy}
                      onClick={() =>
                        run(() => cancelTimeBlock(block.id), 'Couldn’t cancel the session.')
                      }
                      aria-label={`Cancel session: ${formatBlockDay(block.start_at)}`}
                    >
                      <Ban className="size-4" aria-hidden />
                    </Button>
                  </>
                )}
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={busy}
                  onClick={() => setDialog({ block })}
                  aria-label={`Edit session: ${formatBlockDay(block.start_at)}`}
                >
                  <Pencil className="size-4" aria-hidden />
                </Button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <TimeBlockDialog
        open={dialog !== null}
        onOpenChange={(open) => !open && setDialog(null)}
        block={dialog?.block}
        task={task}
        onSaved={changed}
      />
    </section>
  )
}
