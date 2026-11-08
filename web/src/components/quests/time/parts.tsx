// Small shared pieces for the execution screens (Today, Calendar, Home, the task's sessions).
// The quest accent is the theme's `primary` (amber in light, gold in dark), kept to borders,
// icons, and the now line so the screens stay mostly neutral.

import { Circle, CircleCheckBig, CircleDashed, Compass, Flag, Scroll } from 'lucide-react'

import type { ItemRef, QuestTask, TaskStatus } from '@/lib/api'
import { pathLabel, TASK_STATUS_LABELS } from '@/lib/timeBlocks'
import { cn } from '@/lib/utils'

/** Task = round checkbox (empty, dashed while in progress, checked when done). */
export function TaskMark({ status, className }: { status: TaskStatus; className?: string }) {
  const Icon =
    status === 'completed' ? CircleCheckBig : status === 'in_progress' ? CircleDashed : Circle
  return (
    <Icon
      className={cn(
        'size-4 shrink-0',
        status === 'completed'
          ? 'text-good'
          : status === 'in_progress'
            ? 'text-primary'
            : 'text-muted',
        className,
      )}
      aria-label={TASK_STATUS_LABELS[status]}
      role="img"
    />
  )
}

const ROOT_ICONS = { ambition: Compass, goal: Flag, side_quest: Scroll } as const

/** The task's parents, with the icon of the outermost quest. Empty for an Inbox task. */
export function PathLine({
  task,
  className,
}: {
  task: Pick<QuestTask, 'path' | 'standalone'>
  className?: string
}) {
  const path: ItemRef[] = task.path
  const label = path.length > 0 ? pathLabel(path) : task.standalone ? 'Side quest' : 'Inbox'
  const root = path[0]?.kind
  const Icon =
    root !== undefined && root in ROOT_ICONS
      ? ROOT_ICONS[root as keyof typeof ROOT_ICONS]
      : task.standalone
        ? Scroll
        : null
  return (
    <p className={cn('flex min-w-0 items-start gap-1.5 text-xs text-muted', className)}>
      {Icon !== null && <Icon className="mt-px size-3.5 shrink-0" aria-hidden />}
      <span className="line-clamp-2" title={label}>
        {label}
      </span>
    </p>
  )
}
