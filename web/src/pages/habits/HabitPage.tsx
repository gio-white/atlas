import { Trash2 } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'

import { DayMenu } from '@/components/habits/DayMenu'
import { HistoryGrid } from '@/components/habits/HistoryGrid'
import { StatusIcon } from '@/components/habits/StatusIcon'
import { useDayActions } from '@/components/habits/useDayActions'
import { PageError, PageLoading, PageUnavailable } from '@/components/PageState'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  ApiError,
  archiveHabit,
  deleteFreeze,
  deleteHabit,
  getHabitDetail,
  type HabitDetail,
  type HabitFreeze,
  restoreHabit,
} from '@/lib/api'
import { useAsOf } from '@/lib/asOf'
import {
  dateRangeLabel,
  dayLine,
  keptFigure,
  ownDayFreeze,
  progressShare,
  rowActions,
  ruleSummary,
  shortDay,
  splitFreezes,
  streakFigure,
} from '@/lib/habits'

function message(caught: unknown, fallback: string): string {
  return caught instanceof ApiError ? caught.message : fallback
}

/**
 * One habit (habits brief §8): its rule in one line, Current streak, Best streak, Kept last 4
 * weeks, 12 weeks of history, the last 14 days (each opens the row menu), and its freezes, with
 * Archive or Restore and Delete. As of the shell's `?on=` date.
 */
export function HabitPage() {
  const { slug = '' } = useParams()
  const asOf = useAsOf()
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const [detail, setDetail] = useState<HabitDetail | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [pageError, setPageError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)

  const on = params.get('on')
  const search = on === null ? '' : new URLSearchParams({ on }).toString()

  const load = useCallback(() => getHabitDetail(slug, asOf), [slug, asOf])

  useEffect(() => {
    let cancelled = false
    load()
      .then((next) => {
        if (!cancelled) {
          setDetail(next)
          setError(null)
        }
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setError(
            caught instanceof ApiError && caught.status === 404
              ? 'There is no habit at this address.'
              : message(caught, 'Couldn’t load this habit.'),
          )
        }
      })
    return () => {
      cancelled = true
    }
  }, [load])

  const actions = useDayActions(async () => {
    setDetail(await load())
  })

  if (error !== null) return <PageUnavailable title="Habit" message={error} />
  if (detail === null) return <PageLoading />

  const { habit } = detail
  const archived = habit.archived_at !== null
  const period = detail.current_streak.period
  const freezes = splitFreezes(detail.freezes, detail.as_of)

  async function save(write: () => Promise<unknown>, fallback: string) {
    setSaving(true)
    setPageError(null)
    try {
      await write()
      setDetail(await load())
    } catch (caught: unknown) {
      setPageError(message(caught, fallback))
    } finally {
      setSaving(false)
    }
  }

  async function remove() {
    setSaving(true)
    setPageError(null)
    try {
      await deleteHabit(habit.slug)
      navigate({ pathname: '/habits/week', search })
    } catch (caught: unknown) {
      setPageError(message(caught, 'Couldn’t delete this habit.'))
      setSaving(false)
      setConfirmDelete(false)
    }
  }

  const unit = period === 'day' ? 'days' : period === 'week' ? 'weeks' : 'months'
  const kept = detail.kept_last_4_weeks

  return (
    <div className="flex flex-col gap-6">
      <nav aria-label="Breadcrumb" className="text-sm text-muted">
        <Link
          to={{ pathname: archived ? '/habits/week' : '/habits', search }}
          className="hover:text-ink"
        >
          Habits
        </Link>
      </nav>

      <header className="flex flex-wrap items-start justify-between gap-3">
        <div className="flex min-w-0 flex-col gap-1">
          <div className="flex flex-wrap items-center gap-2">
            <h1 className="text-2xl font-semibold tracking-tight text-ink">{habit.name}</h1>
            {archived && <Badge>Archived</Badge>}
          </div>
          <p className="text-sm text-muted">{ruleSummary(habit)}</p>
        </div>
        <div className="flex flex-wrap gap-2">
          {archived ? (
            <Button
              variant="secondary"
              disabled={saving}
              onClick={() => save(() => restoreHabit(habit.slug), 'Couldn’t restore this habit.')}
            >
              Restore
            </Button>
          ) : (
            <Button
              variant="secondary"
              disabled={saving}
              onClick={() => save(() => archiveHabit(habit.slug), 'Couldn’t archive this habit.')}
            >
              Archive
            </Button>
          )}
          <Button
            variant="ghost"
            className="text-bad hover:text-bad"
            disabled={saving}
            onClick={() => setConfirmDelete(true)}
          >
            Delete
          </Button>
        </div>
      </header>

      {archived && (
        <p className="-mt-3 text-sm text-muted">
          Archived habits are hidden everywhere except the Archived list on the Week tab. Restore it
          to track it again; the days it was archived are frozen.
        </p>
      )}

      {pageError !== null && <PageError message={pageError} />}
      {actions.error !== null && <PageError message={actions.error} />}

      <dl className="grid grid-cols-3 gap-3">
        <Figure label="Current streak" value={streakFigure(detail.current_streak.count, period)} />
        <Figure label="Best streak" value={streakFigure(detail.best_streak, period)} />
        <Figure
          label="Kept, last 4 weeks"
          value={keptFigure(kept)}
          note={kept.target === 0 ? undefined : `${kept.done} of ${kept.target} ${unit}`}
        />
      </dl>

      <section aria-labelledby="habit-history" className="flex flex-col gap-3">
        <h2 id="habit-history" className="text-base font-semibold text-ink">
          History
        </h2>
        <HistoryGrid history={detail.history} asOf={detail.as_of} />
      </section>

      <section aria-labelledby="habit-recent" className="flex flex-col gap-2">
        <h2 id="habit-recent" className="text-base font-semibold text-ink">
          Recent days
        </h2>
        <ul className="-mx-2 flex flex-col">
          {detail.recent.map((result) => {
            const row = { habit, result }
            const line = dayLine(row)
            const content = (
              <>
                <span className="flex size-8 shrink-0 items-center justify-center">
                  <StatusIcon status={result.status} share={progressShare(row)} />
                </span>
                <span className="w-24 shrink-0 text-sm text-ink tabular-nums">
                  {shortDay(result.day)}
                </span>
                <span className="min-w-0 truncate text-sm text-muted">{line}</span>
              </>
            )
            const menu =
              !archived && result.status !== 'not_scheduled' && result.status !== 'upcoming'
            return (
              <li key={result.day}>
                {menu ? (
                  <DayMenu
                    actions={rowActions(
                      result,
                      ownDayFreeze(detail.freezes, habit.slug, result.day) !== undefined,
                    ).filter((action) => action !== 'open')}
                    onAction={(action) =>
                      actions.act(habit.slug, result.day, action, detail.freezes)
                    }
                    disabled={actions.isBusy(habit.slug, result.day)}
                  >
                    <button
                      type="button"
                      aria-label={`${shortDay(result.day)}: ${line}`}
                      className="flex min-h-11 w-full items-center gap-3 rounded-xl px-2 text-left hover:bg-raised focus-visible:ring-2 focus-visible:ring-accent focus-visible:outline-none"
                    >
                      {content}
                    </button>
                  </DayMenu>
                ) : (
                  <div className="flex min-h-11 items-center gap-3 px-2">{content}</div>
                )}
              </li>
            )
          })}
        </ul>
      </section>

      <section aria-labelledby="habit-freezes" className="flex flex-col gap-2">
        <h2 id="habit-freezes" className="text-base font-semibold text-ink">
          Freezes
        </h2>
        {detail.freezes.length === 0 ? (
          <p className="text-sm text-muted">
            No freezes. Freeze a day from its row menu to keep the streak through it.
          </p>
        ) : (
          <>
            <FreezeList
              title="Upcoming"
              freezes={freezes.upcoming}
              disabled={saving}
              onRemove={(id) => save(() => deleteFreeze(id), 'Couldn’t remove the freeze.')}
            />
            <FreezeList
              title="Past"
              freezes={freezes.past}
              disabled={saving}
              onRemove={(id) => save(() => deleteFreeze(id), 'Couldn’t remove the freeze.')}
            />
          </>
        )}
      </section>

      <Dialog open={confirmDelete} onOpenChange={setConfirmDelete}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete {habit.name}?</DialogTitle>
            <DialogDescription>
              Its history goes with it: every day’s result, its rule changes, and its freezes. To
              keep the history, archive it instead.
            </DialogDescription>
          </DialogHeader>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" disabled={saving} onClick={() => setConfirmDelete(false)}>
              Cancel
            </Button>
            <Button variant="destructive" disabled={saving} onClick={() => void remove()}>
              <Trash2 className="size-4" aria-hidden />
              Delete
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}

function Figure({ label, value, note }: { label: string; value: string; note?: string }) {
  return (
    <div className="flex flex-col gap-0.5 rounded-2xl border border-line bg-surface px-3 py-3">
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="text-lg font-semibold text-ink tabular-nums">{value}</dd>
      {note !== undefined && <dd className="text-xs text-muted tabular-nums">{note}</dd>}
    </div>
  )
}

function FreezeList({
  title,
  freezes,
  disabled,
  onRemove,
}: {
  title: string
  freezes: HabitFreeze[]
  disabled: boolean
  onRemove: (id: number) => void
}) {
  if (freezes.length === 0) return null
  return (
    <div className="flex flex-col gap-1">
      <h3 className="text-xs font-semibold tracking-wide text-muted uppercase">{title}</h3>
      <ul className="flex flex-col">
        {freezes.map((freeze) => {
          const range = dateRangeLabel(freeze.start_on, freeze.end_on)
          return (
            <li key={freeze.id} className="flex min-h-11 items-center justify-between gap-3">
              <span className="flex min-w-0 flex-col">
                <span className="text-sm text-ink">
                  {range}
                  {freeze.reason !== null && freeze.reason !== '' && (
                    <span className="text-muted"> · {freeze.reason}</span>
                  )}
                </span>
                {freeze.habit === null && <span className="text-xs text-muted">All habits</span>}
              </span>
              <Button
                variant="ghost"
                size="icon"
                className="size-11"
                aria-label={`Remove the freeze ${range}`}
                disabled={disabled}
                onClick={() => onRemove(freeze.id)}
              >
                <Trash2 className="size-4" aria-hidden />
              </Button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
