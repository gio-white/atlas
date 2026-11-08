import { CalendarCheck, CircleAlert, Sun } from 'lucide-react'
import { Link } from 'react-router-dom'

import { PathLine, TaskMark } from '@/components/quests/time/parts'
import { useSessionActions } from '@/components/quests/time/useSessionActions'
import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { TodayQuests } from '@/lib/api'
import { formatTimeRange } from '@/lib/timeBlocks'

const NEXT_SESSIONS = 3
const NEXT_ACTIONS = 3

/** Home's slice of `/today`: the next few sessions, how many to confirm, and next steps. */
export function TodaysQuestsCard({
  today,
  search = '',
  onChanged,
}: {
  today: TodayQuests | null
  search?: string
  onChanged: () => void | Promise<void>
}) {
  const { actions, status, error, dialogs } = useSessionActions(onChanged)
  const todayLink = { pathname: '/today', search }

  return (
    <Card className="flex flex-col">
      <CardHeader>
        <div>
          <CardTitle className="flex items-center gap-2 text-base">
            <Sun className="size-4 text-iris" aria-hidden />
            Today’s quests
          </CardTitle>
          <CardDescription>Your sessions and next steps</CardDescription>
        </div>
        <Link to={todayLink} className="text-xs font-medium text-iris hover:underline">
          View all
        </Link>
      </CardHeader>

      {today === null ? (
        <p className="text-sm text-muted">Today’s quests are unavailable right now.</p>
      ) : (
        <div className="flex flex-col gap-4">
          {today.unconfirmed.length > 0 && (
            <Link
              to={todayLink}
              className="flex items-center gap-2 rounded-xl border border-warn/30 bg-warn/10 px-3 py-2 text-sm text-ink hover:bg-warn/15"
            >
              <CircleAlert className="size-4 shrink-0 text-warn" aria-hidden />
              {today.unconfirmed.length === 1
                ? '1 past session to confirm'
                : `${today.unconfirmed.length} past sessions to confirm`}
            </Link>
          )}

          <Sessions today={today} actions={actions} />

          <div>
            <h3 className="text-xs font-medium text-muted">Next steps</h3>
            {today.up_next.length === 0 ? (
              <p className="mt-1 text-sm text-muted">
                No next steps yet. Add tasks to your quests.
              </p>
            ) : (
              <ul className="mt-1 flex flex-col gap-2">
                {today.up_next.slice(0, NEXT_ACTIONS).map((task) => (
                  <li key={task.id} className="flex items-start gap-2">
                    <TaskMark status={task.status} className="mt-0.5" />
                    <div className="min-w-0">
                      <p className="text-sm text-ink">{task.title}</p>
                      <PathLine task={task} />
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div aria-live="polite" className="empty:hidden">
            {status !== null && <p className="text-xs text-good">{status}</p>}
          </div>
          {error !== null && (
            <p className="text-xs text-bad" role="alert">
              {error}
            </p>
          )}
        </div>
      )}
      {dialogs}
    </Card>
  )
}

function Sessions({
  today,
  actions,
}: {
  today: TodayQuests
  actions: ReturnType<typeof useSessionActions>['actions']
}) {
  const open = today.blocks.filter(
    (item) => item.block.status === 'scheduled' && !item.block.unconfirmed,
  )
  const doneCount = today.blocks.filter((item) => item.block.status === 'completed').length

  if (today.blocks.length === 0) {
    return <p className="text-sm text-muted">No sessions planned for today.</p>
  }
  return (
    <div>
      <h3 className="text-xs font-medium text-muted">
        Sessions{doneCount > 0 ? ` · ${doneCount} of ${today.blocks.length} done` : ''}
      </h3>
      {open.length === 0 ? (
        <p className="mt-1 text-sm text-muted">No more sessions planned today.</p>
      ) : (
        <ul className="mt-1 flex flex-col divide-y divide-line">
          {open.slice(0, NEXT_SESSIONS).map((item) => (
            <li key={item.block.id} className="flex items-center gap-3 py-2">
              <span className="w-24 shrink-0 text-sm font-semibold tabular-nums text-ink">
                {formatTimeRange(item.block.start_at, item.block.end_at)}
              </span>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm text-ink">{item.task.title}</p>
                <PathLine task={item.task} />
              </div>
              <Button
                size="sm"
                variant="outline"
                disabled={actions.busy}
                onClick={() => actions.onSessionDone(item)}
                aria-label={`Session done: ${item.task.title}`}
              >
                <CalendarCheck className="size-4 text-iris" aria-hidden />
                <span className="sr-only sm:not-sr-only">Session done</span>
              </Button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
