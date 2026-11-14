import { MoreHorizontal } from 'lucide-react'
import { useState } from 'react'

import type { HabitDayRow as Row } from '@/lib/api'
import {
  DAY_STATUS_LABEL,
  progressLabel,
  progressShare,
  type RowAction,
  reasonLine,
  rowActions,
  streakLabel,
} from '@/lib/habits'
import { cn } from '@/lib/utils'

import { DayMenu } from './DayMenu'
import { StatusIcon } from './StatusIcon'
import { Streak } from './Streak'

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
      <DayMenu
        actions={actions}
        onAction={onAction}
        open={menuOpen}
        onOpenChange={setMenuOpen}
        disabled={busy}
      >
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
              {streakText !== null && <Streak label={streakText} />}
            </span>
          )}
          <MoreHorizontal className="size-4 shrink-0 text-muted" aria-hidden />
        </button>
      </DayMenu>
    </li>
  )
}
