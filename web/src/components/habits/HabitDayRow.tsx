import { Flame, MoreHorizontal } from 'lucide-react'
import { useState } from 'react'

import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import type { HabitDayRow as Row } from '@/lib/api'
import {
  DAY_STATUS_LABEL,
  progressLabel,
  progressShare,
  ROW_ACTION_LABEL,
  type RowAction,
  reasonLine,
  rowActions,
  streakLabel,
} from '@/lib/habits'
import { cn } from '@/lib/utils'

import { StatusIcon } from './StatusIcon'

/**
 * One habit on the Day tab (habits brief §7): its status icon, name, reason line, and on the
 * right the period's progress and the streak. The icon ticks a habit you tick (and unticks it);
 * on a data habit, or a frozen day, it opens the row menu, as the row itself does.
 */
export function HabitDayRow({
  row,
  canUnfreeze,
  busy,
  onAction,
  onToggle,
}: {
  row: Row
  canUnfreeze: boolean
  busy: boolean
  onAction: (action: RowAction) => void
  onToggle: () => void
}) {
  const [menuOpen, setMenuOpen] = useState(false)
  const { habit, result, streak, progress } = row
  const ticks = habit.rule.check === 'manual' && result.status !== 'frozen'
  const reason = reasonLine(row)
  const streakText = streakLabel(streak)
  const progressText = progressLabel(progress)
  const actions = rowActions(result, canUnfreeze)
  const status = DAY_STATUS_LABEL[result.status]

  return (
    <li className={cn('flex items-center gap-1 pl-1', busy && 'opacity-60')}>
      <button
        type="button"
        disabled={busy}
        className="flex size-11 shrink-0 items-center justify-center rounded-full focus-visible:ring-2 focus-visible:ring-accent focus-visible:outline-none"
        {...(ticks
          ? { 'aria-pressed': result.status === 'done', 'aria-label': `Done: ${habit.name}` }
          : { 'aria-haspopup': 'menu' as const, 'aria-label': `${status}: ${habit.name}` })}
        onClick={() => (ticks ? onToggle() : setMenuOpen(true))}
      >
        <StatusIcon status={result.status} share={progressShare(row)} />
      </button>
      <DropdownMenu open={menuOpen} onOpenChange={setMenuOpen}>
        <DropdownMenuTrigger asChild disabled={busy}>
          <button
            type="button"
            aria-label={`${habit.name}, ${status}${reason === null ? '' : `, ${reason}`}`}
            className="flex min-h-14 min-w-0 flex-1 items-center gap-3 rounded-xl py-2 pr-2 text-left focus-visible:ring-2 focus-visible:ring-accent focus-visible:outline-none"
          >
            <span className="flex min-w-0 flex-1 flex-col">
              <span className="truncate font-medium text-ink">{habit.name}</span>
              {reason !== null && <span className="truncate text-xs text-muted">{reason}</span>}
            </span>
            {(progressText !== null || streakText !== null) && (
              <span className="flex shrink-0 items-center gap-1.5 text-xs text-muted tabular-nums">
                {progressText !== null && <span>{progressText}</span>}
                {progressText !== null && streakText !== null && <span aria-hidden>·</span>}
                {streakText !== null && (
                  <span className="inline-flex items-center gap-1">
                    <Flame className="size-3.5 text-accent" aria-hidden />
                    {streakText}
                  </span>
                )}
              </span>
            )}
            <MoreHorizontal className="size-4 shrink-0 text-muted" aria-hidden />
          </button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="end">
          {actions.map((action) => (
            <DropdownMenuItem key={action} onSelect={() => onAction(action)}>
              {ROW_ACTION_LABEL[action]}
            </DropdownMenuItem>
          ))}
        </DropdownMenuContent>
      </DropdownMenu>
    </li>
  )
}
