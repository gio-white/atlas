import { Ban, CalendarCheck, CircleCheckBig, Pencil } from 'lucide-react'

import { Button } from '@/components/ui/button'
import type { ScheduledBlock } from '@/lib/api'
import { formatBlockDay, formatDuration, formatTime, formatTimeRange } from '@/lib/timeBlocks'
import { cn } from '@/lib/utils'

import { PathLine, TaskMark } from './parts'

export type SessionActions = {
  onSessionDone: (item: ScheduledBlock) => void
  onCancel: (item: ScheduledBlock) => void
  onOutcome: (item: ScheduledBlock) => void
  onEdit: (item: ScheduledBlock) => void
  busy: boolean
}

/**
 * One session on Today. "Session done" (records the session) and "Outcome achieved"
 * (completes the task) are two separate buttons in separate groups, so one tap never does both.
 */
export function SessionRow({
  item,
  actions,
  showDay = false,
  unconfirmed = false,
}: {
  item: ScheduledBlock
  actions: SessionActions
  showDay?: boolean
  unconfirmed?: boolean
}) {
  const { block, task } = item
  const done = block.status === 'completed'
  const scheduled = block.status === 'scheduled'
  const taskDone = task.status === 'completed'

  return (
    <li
      className={cn(
        'grid grid-cols-[minmax(0,1fr)] gap-3 sm:grid-cols-[5rem_minmax(0,1fr)]',
        done && 'opacity-80',
      )}
      data-testid={`session-${block.id}`}
    >
      <div className="hidden pt-3 text-right sm:block">
        {showDay && <p className="text-xs text-muted">{formatBlockDay(block.start_at)}</p>}
        <p className="text-base font-semibold tabular-nums text-ink">
          {formatTime(block.start_at)}
        </p>
        <p className="text-xs tabular-nums text-muted">{formatTime(block.end_at)}</p>
      </div>
      <div
        className={cn(
          'rounded-2xl border bg-surface p-3 shadow-[var(--shadow-card)]',
          unconfirmed
            ? 'border-warn/40'
            : scheduled
              ? 'border-line border-l-4 border-l-primary'
              : 'border-line',
        )}
      >
        <p className="mb-1.5 text-sm font-semibold tabular-nums text-ink sm:hidden">
          {showDay && (
            <span className="font-normal text-muted">{formatBlockDay(block.start_at)} · </span>
          )}
          {formatTimeRange(block.start_at, block.end_at)}
        </p>
        <div className="flex items-start gap-2">
          <TaskMark status={task.status} className="mt-0.5" />
          <div className="min-w-0 flex-1">
            <p className={cn('font-medium text-ink', taskDone && 'line-through decoration-muted')}>
              {task.title}
            </p>
            <PathLine task={task} />
          </div>
          <span className="shrink-0 text-xs tabular-nums text-muted">
            {formatDuration(block.minutes)}
          </span>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2">
          <div className="flex items-center gap-1 sm:gap-2">
            {scheduled ? (
              <Button
                size="sm"
                variant="outline"
                disabled={actions.busy}
                onClick={() => actions.onSessionDone(item)}
                aria-label={`Session done: ${task.title}`}
              >
                <CalendarCheck className="size-4 text-primary" aria-hidden />
                Session done
              </Button>
            ) : (
              <span className="inline-flex items-center gap-1.5 text-xs font-medium text-good">
                <CalendarCheck className="size-4" aria-hidden />
                Session done
              </span>
            )}
            {scheduled && (
              <Button
                size="sm"
                variant="ghost"
                disabled={actions.busy}
                onClick={() => actions.onCancel(item)}
                aria-label={`${unconfirmed ? 'Didn’t happen' : 'Cancel session'}: ${task.title}`}
              >
                <Ban className="size-4" aria-hidden />
                {unconfirmed ? 'Didn’t happen' : 'Cancel'}
              </Button>
            )}
            <Button
              size="sm"
              variant="ghost"
              disabled={actions.busy}
              onClick={() => actions.onEdit(item)}
              aria-label={`Edit session: ${task.title}`}
            >
              <Pencil className="size-4" aria-hidden />
              <span className="sr-only sm:not-sr-only">Edit</span>
            </Button>
          </div>
          {!unconfirmed && (
            <div className="w-full border-t border-line pt-2 sm:ml-auto sm:w-auto sm:border-t-0 sm:border-l sm:pt-0 sm:pl-4">
              {taskDone ? (
                <span className="inline-flex items-center gap-1.5 text-xs font-medium text-good">
                  <CircleCheckBig className="size-4" aria-hidden />
                  Outcome achieved
                </span>
              ) : (
                <Button
                  size="sm"
                  variant="secondary"
                  disabled={actions.busy}
                  onClick={() => actions.onOutcome(item)}
                  aria-label={`Outcome achieved: ${task.title}`}
                  title="Completes the task"
                >
                  <CircleCheckBig className="size-4 text-good" aria-hidden />
                  Outcome achieved
                </Button>
              )}
            </div>
          )}
        </div>
      </div>
    </li>
  )
}
