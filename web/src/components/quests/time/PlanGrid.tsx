import { Layers } from 'lucide-react'
import { type MouseEvent, useEffect, useMemo, useRef } from 'react'

import type { ScheduledBlock } from '@/lib/api'
import {
  assignLanes,
  BLOCK_STATUS_LABELS,
  dayPlacement,
  formatTimeRange,
  weekDays,
} from '@/lib/timeBlocks'
import { cn } from '@/lib/utils'

export const HOUR_PX = 48
const HOURS = Array.from({ length: 24 }, (_, hour) => hour)

function hourLabel(hour: number): string {
  return `${String(hour).padStart(2, '0')}:00`
}

function dayHeading(date: string): { weekday: string; day: string; full: string } {
  const [year, month, day] = date.split('-').map(Number)
  const value = new Date(year, month - 1, day)
  return {
    weekday: value.toLocaleDateString('en-GB', { weekday: 'short' }),
    day: String(day),
    full: value.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' }),
  }
}

/**
 * Monday–Sunday × 24 hours. Blocks are drawn where they fall in local time; overlaps come
 * from the API's `overlaps` flag (lanes only keep them readable). Empty hours are buttons that
 * plan a session there (the lower half of an hour starts at :30).
 */
export function PlanGrid({
  monday,
  blocks,
  today,
  showCancelled,
  onSlot,
  onBlock,
}: {
  monday: string
  blocks: ScheduledBlock[]
  today: string
  showCancelled: boolean
  onSlot: (date: string, time: string) => void
  onBlock: (item: ScheduledBlock) => void
}) {
  const scroller = useRef<HTMLDivElement>(null)
  const todayHeader = useRef<HTMLDivElement>(null)
  const days = weekDays(monday)
  const visible = useMemo(
    () => blocks.filter((item) => showCancelled || item.block.status !== 'cancelled'),
    [blocks, showCancelled],
  )

  // Open near the current time, and on narrow screens with today's column in view.
  useEffect(() => {
    const element = scroller.current
    if (element === null) return
    const hour = new Date().getHours()
    element.scrollTop = Math.max(0, (hour - 1) * HOUR_PX - 12)
    const header = todayHeader.current
    if (header !== null && element.scrollWidth > element.clientWidth) {
      element.scrollLeft = Math.max(0, header.offsetLeft - 56)
    }
  }, [])

  const now = new Date()
  const nowMinutes = now.getHours() * 60 + now.getMinutes()

  return (
    <div
      ref={scroller}
      className="max-h-[70svh] overflow-auto rounded-2xl border border-line bg-surface shadow-[var(--shadow-card)]"
      data-testid="plan-grid"
    >
      <div className="grid min-w-[760px] grid-cols-[3.5rem_repeat(7,minmax(0,1fr))]">
        <div className="sticky top-0 left-0 z-30 border-b border-line bg-surface" />
        {days.map((date) => {
          const heading = dayHeading(date)
          const isToday = date === today
          return (
            <div
              key={date}
              ref={isToday ? todayHeader : undefined}
              className="sticky top-0 z-20 border-b border-l border-line bg-surface px-2 py-2 text-center"
            >
              <span className="sr-only">{heading.full}</span>
              <p
                className={cn('text-xs', isToday ? 'font-semibold text-accent' : 'text-muted')}
                aria-hidden
              >
                {heading.weekday}
              </p>
              <p
                className={cn(
                  'mx-auto mt-0.5 flex size-8 items-center justify-center rounded-full text-base font-semibold tabular-nums',
                  isToday ? 'bg-accent text-surface' : 'text-ink',
                )}
                aria-hidden
              >
                {heading.day}
              </p>
            </div>
          )
        })}

        <div className="sticky left-0 z-10 bg-surface">
          {HOURS.map((hour) => (
            <div
              key={hour}
              className="relative pr-2 text-right text-[11px] tabular-nums text-muted"
              style={{ height: HOUR_PX }}
            >
              {hour > 0 && <span className="absolute -top-2 right-2">{hourLabel(hour)}</span>}
            </div>
          ))}
        </div>

        {days.map((date) => (
          <DayColumn
            key={date}
            date={date}
            blocks={visible}
            isToday={date === today}
            nowMinutes={nowMinutes}
            onSlot={onSlot}
            onBlock={onBlock}
          />
        ))}
      </div>
    </div>
  )
}

function DayColumn({
  date,
  blocks,
  isToday,
  nowMinutes,
  onSlot,
  onBlock,
}: {
  date: string
  blocks: ScheduledBlock[]
  isToday: boolean
  nowMinutes: number
  onSlot: (date: string, time: string) => void
  onBlock: (item: ScheduledBlock) => void
}) {
  const placed = blocks
    .map((item) => ({ item, at: dayPlacement(item.block.start_at, item.block.end_at, date) }))
    .filter(
      (entry): entry is { item: ScheduledBlock; at: { top: number; height: number } } =>
        entry.at !== null,
    )
  const lanes = assignLanes(placed.map(({ item, at }) => ({ id: item.block.id, ...at })))
  const heading = dayHeading(date).full

  function clickSlot(event: MouseEvent<HTMLButtonElement>, hour: number) {
    const rect = event.currentTarget.getBoundingClientRect()
    const lower = rect.height > 0 && event.clientY - rect.top > rect.height / 2
    onSlot(date, `${String(hour).padStart(2, '0')}:${lower ? '30' : '00'}`)
  }

  return (
    <div
      className={cn('relative border-l border-line', isToday && 'bg-accent/[0.04]')}
      style={{ height: HOUR_PX * 24 }}
      data-day={date}
      data-testid={`day-${date}`}
    >
      {HOURS.map((hour) => (
        <button
          key={hour}
          type="button"
          className="block w-full border-t border-line/70 hover:bg-raised focus-visible:bg-raised focus-visible:outline-offset-[-2px]"
          style={{ height: HOUR_PX }}
          aria-label={`Plan a session on ${heading} at ${hourLabel(hour)}`}
          onClick={(event) => clickSlot(event, hour)}
        />
      ))}

      {isToday && (
        <div
          className="pointer-events-none absolute inset-x-0 z-10 h-0.5 bg-accent"
          style={{ top: (nowMinutes / 60) * HOUR_PX }}
          aria-hidden
        >
          <span className="absolute -top-1 -left-1 size-2.5 rounded-full bg-accent" />
        </div>
      )}

      {placed.map(({ item, at }) => {
        const { block, task } = item
        const lane = lanes.get(block.id) ?? { lane: 0, lanes: 1 }
        const width = 100 / lane.lanes
        const height = Math.max((at.height / 60) * HOUR_PX, 22)
        const short = height < 40
        const state = block.unconfirmed ? 'Unconfirmed' : BLOCK_STATUS_LABELS[block.status]
        return (
          <button
            key={block.id}
            type="button"
            data-testid={`cal-block-${block.id}`}
            data-status={block.status}
            onClick={() => onBlock(item)}
            className={cn(
              'absolute z-20 overflow-hidden rounded-lg border px-1.5 py-1 text-left text-xs shadow-sm motion-safe:transition-colors',
              block.status === 'scheduled' &&
                !block.unconfirmed &&
                'border-accent/40 border-l-4 border-l-accent bg-surface text-ink hover:bg-raised',
              block.unconfirmed && 'border-warn/50 border-l-4 border-l-warn bg-warn/10 text-ink',
              block.status === 'completed' && 'border-line bg-raised text-muted hover:text-ink',
              block.status === 'cancelled' &&
                'border-dashed border-line bg-transparent text-muted line-through',
              block.status === 'missed' && 'border-dashed border-warn/50 bg-transparent text-muted',
              block.overlaps && 'ring-2 ring-warn/60',
            )}
            style={{
              top: (at.top / 60) * HOUR_PX,
              height,
              left: `calc(${lane.lane * width}% + 2px)`,
              width: `calc(${width}% - 4px)`,
            }}
            aria-label={`${task.title}, ${formatTimeRange(block.start_at, block.end_at)}, ${state}${block.overlaps ? ', overlaps another session' : ''}`}
          >
            <span className={cn('flex items-center gap-1', short && 'truncate')}>
              {block.overlaps && <Layers className="size-3 shrink-0 text-warn" aria-hidden />}
              <span className="truncate font-medium">{task.title}</span>
            </span>
            {!short && (
              <span className="block truncate tabular-nums text-muted">
                {formatTimeRange(block.start_at, block.end_at)}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}
