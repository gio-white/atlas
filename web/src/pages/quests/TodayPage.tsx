import { CalendarPlus, CircleAlert, ListTodo, Sparkles } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { EmptyState, PageError, PageHeader, PageLoading } from '@/components/PageState'
import { SessionRow } from '@/components/quests/time/SessionRow'
import { TaskLine } from '@/components/quests/time/TaskLine'
import { type DialogTask, TimeBlockDialog } from '@/components/quests/time/TimeBlockDialog'
import { useSessionActions } from '@/components/quests/time/useSessionActions'
import { Button } from '@/components/ui/button'
import { ApiError, getTodayQuests, type QuestTask, type TodayQuests } from '@/lib/api'
import { useShell } from '@/lib/asOf'
import { shortDateLabel } from '@/lib/dates'
import { formatTime } from '@/lib/timeBlocks'
import { todayIso } from '@/lib/utils'

export function TodayPage() {
  const { asOf } = useShell()
  const [params] = useSearchParams()
  const [data, setData] = useState<TodayQuests | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [scheduling, setScheduling] = useState<{ task: DialogTask | null } | null>(null)

  const refresh = useCallback(async () => {
    try {
      setData(await getTodayQuests(asOf))
      setLoadError(null)
    } catch (err) {
      setLoadError(err instanceof ApiError ? err.message : 'Couldn’t load today.')
    }
  }, [asOf])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const { actions, status, error, dialogs } = useSessionActions(refresh)

  if (data === null && loadError !== null) {
    return (
      <div className="flex flex-col gap-5">
        <PageHeader title="Today" />
        <PageError message={loadError} />
      </div>
    )
  }
  if (data === null) return <PageLoading />

  const isToday = data.date === todayIso()
  const schedule = (task: QuestTask) => setScheduling({ task })
  const calendarLink = { pathname: '/calendar', search: params.toString() }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <PageHeader title="Today" description="Your sessions and what to do next." />
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link to={calendarLink}>Week</Link>
          </Button>
          <Button onClick={() => setScheduling({ task: null })}>
            <CalendarPlus className="size-4" aria-hidden />
            Plan a session
          </Button>
        </div>
      </div>

      <div aria-live="polite" className="empty:hidden">
        {status !== null && (
          <p className="rounded-xl border border-good/30 bg-good/10 px-4 py-2 text-sm text-good">
            {status}
          </p>
        )}
      </div>
      {error !== null && <PageError message={error} />}

      <div className="grid grid-cols-[minmax(0,1fr)] gap-6 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
        <div className="flex flex-col gap-6">
          {data.unconfirmed.length > 0 && (
            <section aria-labelledby="unconfirmed-heading" className="flex flex-col gap-3">
              <div>
                <h2
                  id="unconfirmed-heading"
                  className="flex items-center gap-2 text-base font-semibold text-ink"
                >
                  <CircleAlert className="size-4 text-warn" aria-hidden />
                  Unconfirmed
                  <span className="rounded-full bg-warn/15 px-2 py-0.5 text-xs font-semibold text-warn">
                    {data.unconfirmed.length}
                  </span>
                </h2>
                <p className="text-sm text-muted">These sessions have ended. Did they happen?</p>
              </div>
              <ol className="flex flex-col gap-3">
                {data.unconfirmed.map((item) => (
                  <SessionRow
                    key={item.block.id}
                    item={item}
                    actions={actions}
                    showDay
                    unconfirmed
                  />
                ))}
              </ol>
            </section>
          )}

          <section aria-labelledby="timeline-heading" className="flex flex-col gap-3">
            <h2 id="timeline-heading" className="text-base font-semibold text-ink">
              {isToday ? 'Today’s sessions' : `Sessions on ${shortDateLabel(data.date)}`}
            </h2>
            {data.blocks.length === 0 ? (
              <EmptyState
                title="No sessions planned"
                hint="Plan a session to set aside time for a task."
              />
            ) : (
              <ol className="flex flex-col gap-3">
                {timelineWithNow(data, isToday).map((entry) =>
                  entry === 'now' ? (
                    <NowMarker key="now" />
                  ) : (
                    <SessionRow key={entry.block.id} item={entry} actions={actions} />
                  ),
                )}
              </ol>
            )}
          </section>
        </div>

        <aside className="flex flex-col gap-6">
          <section
            aria-labelledby="due-heading"
            className="rounded-2xl border border-line bg-surface p-4 shadow-[var(--shadow-card)]"
          >
            <h2
              id="due-heading"
              className="flex items-center gap-2 text-base font-semibold text-ink"
            >
              <ListTodo className="size-4 text-primary" aria-hidden />
              Due today
            </h2>
            {data.due_today.length === 0 ? (
              <p className="mt-2 text-sm text-muted">
                Nothing is due. Tasks with a due date of today or earlier show here.
              </p>
            ) : (
              <ul className="mt-1 divide-y divide-line">
                {data.due_today.map((task) => (
                  <TaskLine
                    key={task.id}
                    task={task}
                    onSchedule={schedule}
                    meta={<DueLabel due={task.due_on} today={data.date} />}
                  />
                ))}
              </ul>
            )}
          </section>

          <section
            aria-labelledby="next-heading"
            className="rounded-2xl border border-line bg-surface p-4 shadow-[var(--shadow-card)]"
          >
            <h2
              id="next-heading"
              className="flex items-center gap-2 text-base font-semibold text-ink"
            >
              <Sparkles className="size-4 text-primary" aria-hidden />
              Up next
            </h2>
            <p className="text-xs text-muted">The next step on each of your quests.</p>
            {data.up_next.length === 0 ? (
              <p className="mt-2 text-sm text-muted">
                No next steps. Add tasks to your quests to see them here.
              </p>
            ) : (
              <ul className="mt-1 divide-y divide-line">
                {data.up_next.map((task) => (
                  <TaskLine key={task.id} task={task} onSchedule={schedule} />
                ))}
              </ul>
            )}
          </section>
        </aside>
      </div>

      {dialogs}
      <TimeBlockDialog
        open={scheduling !== null}
        onOpenChange={(open) => !open && setScheduling(null)}
        task={scheduling?.task}
        onSaved={refresh}
      />
    </div>
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
      <span className="whitespace-nowrap text-right text-xs font-semibold tabular-nums text-primary">
        Now · {formatTime(new Date().toISOString())}
      </span>
      <span className="h-0.5 rounded-full bg-primary" aria-hidden />
    </li>
  )
}

/** Today's blocks with a "now" line before the first block that hasn't started yet. */
function timelineWithNow(data: TodayQuests, isToday: boolean) {
  const entries: (TodayQuests['blocks'][number] | 'now')[] = [...data.blocks]
  if (!isToday) return entries
  const now = Date.now()
  const index = data.blocks.findIndex((item) => new Date(item.block.start_at).getTime() > now)
  entries.splice(index === -1 ? entries.length : index, 0, 'now')
  return entries
}
