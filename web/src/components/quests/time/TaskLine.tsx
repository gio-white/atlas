import { CalendarPlus } from 'lucide-react'
import type { ReactNode } from 'react'

import { Button } from '@/components/ui/button'
import type { QuestTask } from '@/lib/api'
import { formatMinutes } from '@/lib/format'
import { cn } from '@/lib/utils'

import { PathLine, TaskMark } from './parts'

/** A task in a short list (Due today, Up next) with an optional quick Schedule action. */
export function TaskLine({
  task,
  meta,
  onSchedule,
  compact = false,
}: {
  task: QuestTask
  meta?: ReactNode
  onSchedule?: (task: QuestTask) => void
  compact?: boolean
}) {
  return (
    <li className={cn('flex items-start gap-2.5', compact ? 'py-1.5' : 'py-2.5')}>
      <TaskMark status={task.status} className="mt-0.5" />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-medium text-ink">{task.title}</p>
        <PathLine task={task} />
        {(meta !== undefined || task.estimate_minutes !== null) && !compact && (
          <p className="mt-0.5 flex flex-wrap gap-x-2 text-xs text-muted">
            {meta}
            {task.estimate_minutes !== null && (
              <span>
                {formatMinutes(task.planned_minutes)} planned of{' '}
                {formatMinutes(task.estimate_minutes)}
              </span>
            )}
          </p>
        )}
      </div>
      {onSchedule !== undefined && (
        <Button
          size="sm"
          variant="ghost"
          onClick={() => onSchedule(task)}
          aria-label={`Schedule: ${task.title}`}
        >
          <CalendarPlus className="size-4" aria-hidden />
          <span className="sr-only sm:not-sr-only">Schedule</span>
        </Button>
      )}
    </li>
  )
}
