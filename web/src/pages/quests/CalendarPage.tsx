import { CalendarPlus, ChevronLeft, ChevronRight, Layers } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { PageError, PageHeader } from '@/components/PageState'
import { TimeBlockDialog } from '@/components/quests/time/TimeBlockDialog'
import { WeekCalendar } from '@/components/quests/time/WeekCalendar'
import { Button } from '@/components/ui/button'
import { ApiError, getQuestCalendar, type ScheduledBlock } from '@/lib/api'
import { useShell } from '@/lib/asOf'
import { addDays, weekLabel, weekRangeUtc, weekStart } from '@/lib/timeBlocks'
import { todayIso } from '@/lib/utils'

type DialogState =
  | { kind: 'new'; date: string; start: string }
  | { kind: 'new-any' }
  | { kind: 'edit'; item: ScheduledBlock }

/** Week view of sessions. The week follows the shell's `?on=` date, so it lives in the URL. */
export function CalendarPage() {
  const { asOf } = useShell()
  const [params, setParams] = useSearchParams()
  const monday = weekStart(asOf)
  const today = todayIso()
  const thisWeek = monday === weekStart(today)
  const [blocks, setBlocks] = useState<ScheduledBlock[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showCancelled, setShowCancelled] = useState(false)
  const [dialog, setDialog] = useState<DialogState | null>(null)

  const load = useCallback(async () => {
    const range = weekRangeUtc(monday)
    try {
      const view = await getQuestCalendar(range.start, range.end)
      setBlocks(view.blocks)
      setError(null)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Couldn’t load the calendar.')
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
          <Legend swatch="border-l-4 border-l-iris border-iris/40 bg-surface" label="Planned" />
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
              className="size-4 accent-[var(--iris)]"
              checked={showCancelled}
              onChange={(event) => setShowCancelled(event.target.checked)}
            />
            Show cancelled{cancelledCount > 0 ? ` (${cancelledCount})` : ''}
          </label>
        </div>
      </div>

      {error !== null && <PageError message={error} />}
      {blocks === null && error === null ? (
        <div className="h-[60svh] animate-pulse rounded-2xl bg-raised" role="status">
          <span className="sr-only">Loading</span>
        </div>
      ) : (
        <WeekCalendar
          key={monday}
          monday={monday}
          blocks={blocks ?? []}
          today={today}
          showCancelled={showCancelled}
          onSlot={(date, start) => setDialog({ kind: 'new', date, start })}
          onBlock={(item) => setDialog({ kind: 'edit', item })}
        />
      )}

      <TimeBlockDialog
        open={dialog !== null}
        onOpenChange={(open) => !open && setDialog(null)}
        block={dialog?.kind === 'edit' ? dialog.item.block : null}
        task={dialog?.kind === 'edit' ? dialog.item.task : null}
        initial={dialog?.kind === 'new' ? { date: dialog.date, start: dialog.start } : null}
        onSaved={load}
      />
    </div>
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
