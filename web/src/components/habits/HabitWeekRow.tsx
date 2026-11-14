import { Link } from 'react-router-dom'

import type { HabitDayResult, HabitFreeze, HabitsWeek } from '@/lib/api'
import {
  cellAction,
  DAY_STATUS_LABEL,
  ownDayFreeze,
  progressShare,
  type RowAction,
  reasonLine,
  rowActions,
  shortDay,
  streakLabel,
} from '@/lib/habits'
import { cn } from '@/lib/utils'

import { DayMenu } from './DayMenu'
import { StatusIcon } from './StatusIcon'
import { Streak } from './Streak'

type Row = HabitsWeek['rows'][number]

/** The seven day cells take the same width in the header and in every row. */
export const WEEK_CELLS = 'grid w-full grid-cols-7 md:w-[19.25rem]'

/**
 * One habit on the Week tab (habits brief §8): its name (a link to its page), Monday to Sunday,
 * then the period's progress and the streak. On a narrow screen the name sits above the days.
 * A habit you tick toggles from a cell up to today; any other judged cell opens its row menu.
 */
export function HabitWeekRow({
  row,
  freezes,
  search,
  isBusy,
  onToggle,
  onAction,
}: {
  row: Row
  freezes: HabitFreeze[]
  search: string
  isBusy: (day: string) => boolean
  onToggle: (result: HabitDayResult) => void
  onAction: (day: string, action: RowAction) => void
}) {
  const { habit, days, streak, progress } = row
  const streakText = streakLabel(streak)
  const progressText =
    progress === null || progress.period === 'day' ? null : `${progress.done} of ${progress.target}`

  return (
    <li className="flex flex-col gap-1 py-2 md:flex-row md:items-center md:gap-3 md:py-1">
      <div className="flex min-w-0 items-center justify-between gap-3 px-1 md:flex-1">
        <Link
          to={{ pathname: `/habit/${habit.slug}`, search }}
          className="truncate font-medium text-ink hover:text-accent focus-visible:text-accent focus-visible:outline-none"
        >
          {habit.name}
        </Link>
        <Meta progress={progressText} streak={streakText} className="md:hidden" />
      </div>
      <div className={WEEK_CELLS}>
        {days.map((result) => (
          <Cell
            key={result.day}
            name={habit.name}
            result={result}
            share={progressShare({ habit, result })}
            reason={reasonLine({ habit, result })}
            kind={cellAction(result, habit.rule.check)}
            actions={rowActions(
              result,
              ownDayFreeze(freezes, habit.slug, result.day) !== undefined,
            )}
            busy={isBusy(result.day)}
            onToggle={() => onToggle(result)}
            onAction={(action) => onAction(result.day, action)}
          />
        ))}
      </div>
      <Meta
        progress={progressText}
        streak={streakText}
        className="hidden w-40 justify-end md:flex"
      />
    </li>
  )
}

function Meta({
  progress,
  streak,
  className,
}: {
  progress: string | null
  streak: string | null
  className?: string
}) {
  if (progress === null && streak === null) return <span className={className} />
  return (
    <span
      className={cn(
        'flex shrink-0 items-center gap-1.5 text-xs whitespace-nowrap text-muted tabular-nums',
        className,
      )}
    >
      {progress !== null && <span>{progress}</span>}
      {progress !== null && streak !== null && <span aria-hidden>·</span>}
      {streak !== null && <Streak label={streak} />}
    </span>
  )
}

function Cell({
  name,
  result,
  share,
  reason,
  kind,
  actions,
  busy,
  onToggle,
  onAction,
}: {
  name: string
  result: HabitDayResult
  share: number
  reason: string | null
  kind: 'toggle' | 'menu' | 'none'
  actions: RowAction[]
  busy: boolean
  onToggle: () => void
  onAction: (action: RowAction) => void
}) {
  const label = `${name}, ${shortDay(result.day)}: ${DAY_STATUS_LABEL[result.status]}${
    reason === null ? '' : `, ${reason}`
  }`
  const icon = <StatusIcon status={result.status} share={share} small />
  const box = cn(
    'flex h-11 items-center justify-center rounded-lg',
    busy && 'opacity-50',
    kind !== 'none' &&
      'hover:bg-raised focus-visible:ring-2 focus-visible:ring-accent focus-visible:outline-none',
  )
  if (kind === 'none') {
    return (
      <span className={box} title={label}>
        <span className="sr-only">{label}</span>
        {icon}
      </span>
    )
  }
  if (kind === 'toggle') {
    return (
      <button
        type="button"
        className={box}
        title={label}
        aria-label={label}
        aria-pressed={result.status === 'done'}
        disabled={busy}
        onClick={onToggle}
      >
        {icon}
      </button>
    )
  }
  return (
    <DayMenu actions={actions} onAction={onAction} disabled={busy}>
      <button type="button" className={box} title={label} aria-label={label}>
        {icon}
      </button>
    </DayMenu>
  )
}
