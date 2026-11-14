import { CalendarPlus, ChevronLeft, ChevronRight, Layers } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { PageError, PageHeader } from '@/components/PageState'
import { PlanGrid } from '@/components/quests/time/PlanGrid'
import { TaskLine } from '@/components/quests/time/TaskLine'
import { TimeBlockDialog } from '@/components/quests/time/TimeBlockDialog'
import { Button } from '@/components/ui/button'
import { ApiError, getPlan, type QuestTask, type ScheduledBlock } from '@/lib/api'
import { useShell } from '@/lib/asOf'
import { addDays, weekLabel, weekRangeUtc, weekStart } from '@/lib/timeBlocks'
import { todayIso } from '@/lib/utils'

type DialogState =
  | { kind: 'new'; date: string; start: string }
  | { kind: 'new-any' }
  | { kind: 'edit'; item: ScheduledBlock }
  | { kind: 'task'; task: QuestTask }

/** Week view of sessions. The week follows the shell's `?on=` date, so it lives in the URL. */
export function PlanPage() {
  const { asOf } = useShell()
  const [params, setParams] = useSearchParams()
  const monday = weekStart(asOf)
  const today = todayIso()
  const thisWeek = monday === weekStart(today)
  const [blocks, setBlocks] = useState<ScheduledBlock[] | null>(null)
  const [notScheduled, setNotScheduled] = useState<QuestTask[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showCancelled, setShowCancelled] = useState(false)
  const [dialog, setDialog] = useState<DialogState | null>(null)

  const load = useCallback(async () => {
    const range = weekRangeUtc(monday)
    try {
      const view = await getPlan(range.start, range.end)
      setBlocks(view.blocks)
      setNotScheduled(view.not_scheduled)
      setError(null)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Couldn’t load your plan.')
    }
  }, [monday])

  useEffect(() => {
    void load()
  }, [load])

  function goTo(date: string | null) {
    const next = new URLSearchParams(params)
    if (date === null || weekStart(date) === weekStart(today)) next.delete('on')
    else next.set('on', date)
    setParams(next)
  }

  const cancelledCount = (blocks ?? []).filter((item) => item.block.status === 'cancelled').length

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <PageHeader
          tab
          title="Plan"
          kicker={weekLabel(monday)}
          description="When you plan to work on your tasks. Click an empty time to plan a session."
        />
        <Button onClick={() => setDialog({ kind: 'new-any' })}>
          <CalendarPlus className="size-4" aria-hidden />
          Plan a session
        </Button>
      </div>

      <div className="flex flex-wrap items-center justify-between gap-3">
        <nav aria-label="Week" className="flex items-center gap-1">
          <Button
            variant="outline"
            size="icon"
            aria-label="Previous week"
            onClick={() => goTo(addDays(monday, -7))}
          >
            <ChevronLeft className="size-4" aria-hidden />
          </Button>
          <Button variant="outline" disabled={thisWeek} onClick={() => goTo(null)}>
            This week
          </Button>
          <Button
            variant="outline"
            size="icon"
            aria-label="Next week"
            onClick={() => goTo(addDays(monday, 7))}
          >
            <ChevronRight className="size-4" aria-hidden />
          </Button>
        </nav>
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-muted">
          <Legend swatch="border-l-4 border-l-accent border-accent/40 bg-surface" label="Planned" />
          <Legend swatch="border-l-4 border-l-warn border-warn/50 bg-warn/10" label="Unconfirmed" />
          <Legend swatch="border-line bg-raised" label="Done" />
          <Legend swatch="border-dashed border-warn/50" label="Didn’t happen" />
          <span className="inline-flex items-center gap-1.5">
            <Layers className="size-3.5 text-warn" aria-hidden />
            Overlaps
          </span>
          <label className="inline-flex items-center gap-2 text-ink">
            <input
              type="checkbox"
              className="size-4 accent-accent"
              checked={showCancelled}
              onChange={(event) => setShowCancelled(event.target.checked)}
            />
            Show cancelled{cancelledCount > 0 ? ` (${cancelledCount})` : ''}
          </label>
        </div>
      </div>

      {error !== null && <PageError message={error} />}
      <div className="flex flex-col gap-5 xl:flex-row xl:items-start">
        <div className="min-w-0 flex-1">
          {blocks === null && error === null ? (
            <div className="h-[60svh] animate-pulse rounded-2xl bg-raised" role="status">
              <span className="sr-only">Loading</span>
            </div>
          ) : (
            <PlanGrid
              key={monday}
              monday={monday}
              blocks={blocks ?? []}
              today={today}
              showCancelled={showCancelled}
              onSlot={(date, start) => setDialog({ kind: 'new', date, start })}
              onBlock={(item) => setDialog({ kind: 'edit', item })}
            />
          )}
        </div>
        {notScheduled !== null && (
          <NotScheduled
            tasks={notScheduled}
            onSchedule={(task) => setDialog({ kind: 'task', task })}
          />
        )}
      </div>

      <TimeBlockDialog
        open={dialog !== null}
        onOpenChange={(open) => !open && setDialog(null)}
        block={dialog?.kind === 'edit' ? dialog.item.block : null}
        task={
          dialog?.kind === 'edit' ? dialog.item.task : dialog?.kind === 'task' ? dialog.task : null
        }
        initial={dialog?.kind === 'new' ? { date: dialog.date, start: dialog.start } : null}
        onSaved={load}
      />
    </div>
  )
}

/**
 * Each active goal's and side quest's next action that has no upcoming session, whatever week is
 * shown. Choosing one plans a session for it.
 */
function NotScheduled({
  tasks,
  onSchedule,
}: {
  tasks: QuestTask[]
  onSchedule: (task: QuestTask) => void
}) {
  return (
    <section
      aria-labelledby="not-scheduled-title"
      className="flex flex-col gap-1 rounded-2xl border border-line bg-surface p-4 xl:w-80 xl:shrink-0"
    >
      <h3 id="not-scheduled-title" className="text-sm font-semibold text-ink">
        Not scheduled yet
      </h3>
      {tasks.length === 0 ? (
        <p className="py-2 text-sm text-muted">Everything next has a session.</p>
      ) : (
        <ul className="flex flex-col divide-y divide-line">
          {tasks.map((task) => (
            <TaskLine key={task.id} task={task} onSchedule={onSchedule} compact />
          ))}
        </ul>
      )}
    </section>
  )
}

function Legend({ swatch, label }: { swatch: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`inline-block h-3 w-4 rounded border ${swatch}`} aria-hidden />
      {label}
    </span>
  )
}
