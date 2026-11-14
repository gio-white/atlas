import { CalendarPlus } from 'lucide-react'
import type { SessionActions } from '@/components/quests/time/SessionRow'
import { SessionRow } from '@/components/quests/time/SessionRow'
import { TaskLine } from '@/components/quests/time/TaskLine'
import { Button } from '@/components/ui/button'
import type { QuestTask, TodayQuests } from '@/lib/api'
import { shortDateLabel } from '@/lib/dates'
import { formatTime } from '@/lib/timeBlocks'
import { todayIso } from '@/lib/utils'

import { BlockEmpty, HomeBlock } from './HomeBlock'

type QuestBlockProps = {
  today: TodayQuests | null
  search: string
  className?: string
}

/** Sessions whose time has passed without an answer. Shown only when there are some. */
export function ToConfirmBlock({
  today,
  search,
  actions,
  className,
}: QuestBlockProps & { actions: SessionActions }) {
  if (today === null || today.unconfirmed.length === 0) return null
  const count = today.unconfirmed.length
  return (
    <HomeBlock
      id="to-confirm"
      title="To confirm"
      search={search}
      className={`border-warn/40 ${className ?? ''}`}
    >
      <p className="text-sm text-muted">
        {count === 1 ? '1 session to confirm' : `${count} sessions to confirm`}
      </p>
      <ol className="flex flex-col gap-3">
        {today.unconfirmed.map((item) => (
          <SessionRow key={item.block.id} item={item} actions={actions} showDay unconfirmed />
        ))}
      </ol>
    </HomeBlock>
  )
}

/** Today's sessions as a timeline, with a "Now" line on the current day. */
export function TodayBlock({
  today,
  search,
  actions,
  onPlan,
  className,
}: QuestBlockProps & { actions: SessionActions; onPlan: () => void }) {
  const isToday = today !== null && today.date === todayIso()
  const title = today === null || isToday ? 'Today' : shortDateLabel(today.date)
  return (
    <HomeBlock
      id="today"
      title={title}
      search={search}
      unavailable={today === null}
      className={className}
    >
      {today !== null && (
        <>
          {today.blocks.length === 0 ? (
            <BlockEmpty>No sessions today.</BlockEmpty>
          ) : (
            <ol className="flex flex-col gap-3">
              {timelineWithNow(today, isToday).map((entry) =>
                entry === 'now' ? (
                  <NowMarker key="now" />
                ) : (
                  <SessionRow key={entry.block.id} item={entry} actions={actions} />
                ),
              )}
            </ol>
          )}
          <div>
            <Button type="button" size="sm" variant="outline" onClick={onPlan}>
              <CalendarPlus className="size-4 text-accent" aria-hidden />
              Plan a session
            </Button>
          </div>
        </>
      )}
    </HomeBlock>
  )
}

export function DueTodayBlock({
  today,
  search,
  onSchedule,
  className,
}: QuestBlockProps & { onSchedule: (task: QuestTask) => void }) {
  return (
    <HomeBlock
      id="due-today"
      title="Due today"
      search={search}
      unavailable={today === null}
      className={className}
    >
      {today !== null &&
        (today.due_today.length === 0 ? (
          <BlockEmpty>Nothing due today.</BlockEmpty>
        ) : (
          <ul className="divide-y divide-line">
            {today.due_today.map((task) => (
              <TaskLine
                key={task.id}
                task={task}
                onSchedule={onSchedule}
                meta={<DueLabel due={task.due_on} today={today.date} />}
              />
            ))}
          </ul>
        ))}
    </HomeBlock>
  )
}

export function UpNextBlock({
  today,
  search,
  onSchedule,
  className,
}: QuestBlockProps & { onSchedule: (task: QuestTask) => void }) {
  return (
    <HomeBlock
      id="up-next"
      title="Up next"
      search={search}
      unavailable={today === null}
      className={className}
    >
      {today !== null &&
        (today.up_next.length === 0 ? (
          <BlockEmpty>No next steps yet. Add tasks to your quests.</BlockEmpty>
        ) : (
          <ul className="divide-y divide-line">
            {today.up_next.map((task) => (
              <TaskLine key={task.id} task={task} onSchedule={onSchedule} />
            ))}
          </ul>
        ))}
    </HomeBlock>
  )
}

function DueLabel({ due, today }: { due: string | null; today: string }) {
  if (due === null) return null
  if (due < today)
    return <span className="font-medium text-bad">Overdue · {shortDateLabel(due)}</span>
  return <span className="font-medium text-warn">Due today</span>
}

function NowMarker() {
  return (
    <li className="grid grid-cols-[auto_minmax(0,1fr)] items-center gap-3 sm:grid-cols-[5rem_minmax(0,1fr)]">
      <span className="whitespace-nowrap text-right text-xs font-semibold tabular-nums text-accent">
        Now · {formatTime(new Date().toISOString())}
      </span>
      <span className="h-0.5 rounded-full bg-accent" aria-hidden />
    </li>
  )
}

/** Today's sessions with a "Now" line before the first one that hasn't started yet. */
export function timelineWithNow(data: TodayQuests, isToday: boolean, now: number = Date.now()) {
  const entries: (TodayQuests['blocks'][number] | 'now')[] = [...data.blocks]
  if (!isToday) return entries
  const index = data.blocks.findIndex((item) => new Date(item.block.start_at).getTime() > now)
  entries.splice(index === -1 ? entries.length : index, 0, 'now')
  return entries
}
