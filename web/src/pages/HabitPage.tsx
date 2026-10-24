import { Archive, ArchiveRestore, ChevronLeft, Pause, Pencil, Trash2, X } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate, useParams, useSearchParams } from 'react-router-dom'

import { BreakDialog } from '@/components/habits/BreakDialog'
import { HabitCard } from '@/components/habits/HabitCard'
import { HabitFormDialog } from '@/components/habits/HabitFormDialog'
import { PageLoading, PageUnavailable } from '@/components/PageState'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle } from '@/components/ui/card'
import { WeekGrid } from '@/components/WeekGrid'
import {
  ApiError,
  archiveHabit,
  deleteHabit,
  deleteHabitBreak,
  getHabitDetail,
  getHabitsCalendar,
  type HabitDetail,
  type HabitsCalendar,
  unarchiveHabit,
} from '@/lib/api'
import { useAsOf } from '@/lib/asOf'
import { shortDateLabel } from '@/lib/dates'
import { formatPercent } from '@/lib/format'
import {
  formatAmount,
  frequencyLabel,
  goalLabel,
  KIND_META,
  streakCount,
  streakLabel,
  TIME_OF_DAY_LABEL,
} from '@/lib/habits'

export function HabitPage() {
  const { slug = '' } = useParams()
  const asOf = useAsOf()
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const search = params.toString()
  const [detail, setDetail] = useState<HabitDetail | null>(null)
  const [calendar, setCalendar] = useState<HabitsCalendar | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [editOpen, setEditOpen] = useState(false)
  const [breakOpen, setBreakOpen] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)

  const refresh = useCallback(async () => {
    const [nextDetail, nextCalendar] = await Promise.all([
      getHabitDetail(slug, asOf),
      getHabitsCalendar('week', asOf),
    ])
    setDetail(nextDetail)
    setCalendar(nextCalendar)
  }, [slug, asOf])

  useEffect(() => {
    let cancelled = false
    setError(null)
    refresh().catch((caught: unknown) => {
      if (!cancelled) setError(caught instanceof ApiError ? caught.message : 'Could not load habit')
    })
    return () => {
      cancelled = true
    }
  }, [refresh])

  async function act(action: () => Promise<unknown>, after?: () => void) {
    setActionError(null)
    try {
      await action()
      if (after) after()
      else await refresh()
    } catch (caught) {
      setActionError(caught instanceof ApiError ? caught.message : 'Could not save')
    }
  }

  if (error !== null) return <PageUnavailable title="Habit" message={error} />
  if (detail === null) return <PageLoading />

  const { habit, status, breaks, recent } = detail
  const archived = habit.archived_at !== null
  const weekRow = calendar?.habits.find((row) => row.slug === habit.slug) ?? null
  const isQuit = habit.kind === 'quit'

  return (
    <div className="flex flex-col gap-6">
      <Link
        to={{ pathname: '/habit', search }}
        className="inline-flex w-fit items-center gap-1 text-sm text-muted hover:text-ink"
      >
        <ChevronLeft className="size-4" aria-hidden />
        Habits
      </Link>

      <div className="flex flex-wrap items-start justify-between gap-4">
        <header className="flex flex-col gap-2">
          <h1 className="text-2xl font-semibold tracking-tight text-ink">{habit.name}</h1>
          <div className="flex flex-wrap gap-1.5">
            <Badge className="normal-case">{KIND_META[habit.kind].label}</Badge>
            <Badge className="normal-case">{frequencyLabel(habit)}</Badge>
            <Badge className="normal-case">{goalLabel(status)}</Badge>
            <Badge className="normal-case">{TIME_OF_DAY_LABEL[habit.time_of_day]}</Badge>
            {archived ? <Badge tone="warn">Archived</Badge> : null}
          </div>
        </header>
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="outline" onClick={() => setEditOpen(true)}>
            <Pencil className="size-4" aria-hidden />
            Edit
          </Button>
          <Button type="button" variant="outline" onClick={() => setBreakOpen(true)}>
            <Pause className="size-4" aria-hidden />
            Skip or pause
          </Button>
          {archived ? (
            <Button
              type="button"
              variant="outline"
              onClick={() => act(() => unarchiveHabit(habit.slug))}
            >
              <ArchiveRestore className="size-4" aria-hidden />
              Restore
            </Button>
          ) : (
            <Button
              type="button"
              variant="outline"
              onClick={() => act(() => archiveHabit(habit.slug))}
            >
              <Archive className="size-4" aria-hidden />
              Archive
            </Button>
          )}
          <Button
            type="button"
            variant="destructive"
            onClick={() =>
              confirmDelete
                ? act(
                    () => deleteHabit(habit.slug),
                    () => navigate({ pathname: '/habit', search }),
                  )
                : setConfirmDelete(true)
            }
          >
            <Trash2 className="size-4" aria-hidden />
            {confirmDelete ? 'Click again to delete' : 'Delete'}
          </Button>
        </div>
      </div>
      {actionError !== null ? (
        <p className="text-sm text-bad" role="alert">
          {actionError}
        </p>
      ) : null}

      {!archived && status.scheduled ? (
        <div className="max-w-xl">
          <HabitCard
            status={status}
            asOf={asOf}
            search={search}
            onChanged={refresh}
            layout={habit.period === 'day' ? 'card' : 'row'}
          />
        </div>
      ) : null}

      <section className="grid gap-3 sm:grid-cols-3">
        <Stat
          label={isQuit ? 'Clean now' : 'Current streak'}
          value={isQuit ? streakLabel(status) : streakCount(status, status.current_streak)}
        />
        <Stat
          label={isQuit ? 'Longest clean run' : 'Longest streak'}
          value={`${streakCount(status, status.longest_streak)}${isQuit ? ' clean' : ''}`}
        />
        <Stat
          label="Adherence"
          value={formatPercent(status.adherence)}
          hint={`since ${shortDateLabel(habit.active_from)}, skipped days excluded`}
        />
      </section>

      {weekRow !== null && calendar !== null ? (
        <Card className="min-w-0">
          <CardHeader>
            <CardTitle className="text-base">
              This week · {shortDateLabel(calendar.range_start)} –{' '}
              {shortDateLabel(calendar.range_end)}
            </CardTitle>
          </CardHeader>
          <WeekGrid habits={[weekRow]} search={search} />
        </Card>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{isQuit ? 'Slips' : 'Recent check-ins'}</CardTitle>
          </CardHeader>
          {recent.length === 0 ? (
            <p className="text-sm text-muted">
              {isQuit ? 'No slips. Keep going.' : 'Nothing logged yet.'}
            </p>
          ) : (
            <ul className="flex max-h-80 flex-col divide-y divide-line overflow-y-auto pr-1 text-sm">
              {recent.map((row) => (
                <li key={row.id} className="flex items-baseline justify-between gap-3 py-2">
                  <span className="text-muted">{shortDateLabel(row.occurred_on)}</span>
                  <span className="min-w-0 flex-1 truncate text-ink">{row.note ?? ''}</span>
                  <span className="font-mono text-xs">
                    {habit.kind === 'check'
                      ? 'done'
                      : isQuit
                        ? 'slip'
                        : formatAmount(row.value, habit.kind, habit.unit)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Pauses & skips</CardTitle>
          </CardHeader>
          {breaks.length === 0 ? (
            <p className="text-sm text-muted">
              None. Skip a day or pause for a trip without losing the streak.
            </p>
          ) : (
            <ul className="flex flex-col divide-y divide-line text-sm">
              {breaks.map((row) => (
                <li key={row.id} className="flex items-center justify-between gap-3 py-2">
                  <span>
                    {row.start_on === row.end_on
                      ? shortDateLabel(row.start_on)
                      : `${shortDateLabel(row.start_on)} – ${shortDateLabel(row.end_on)}`}
                  </span>
                  <span className="min-w-0 flex-1 truncate text-muted">{row.note ?? ''}</span>
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    aria-label="Remove this pause"
                    onClick={() => act(() => deleteHabitBreak(habit.slug, row.id))}
                  >
                    <X className="size-4" aria-hidden />
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </Card>
      </div>

      <HabitFormDialog open={editOpen} onOpenChange={setEditOpen} habit={habit} onSaved={refresh} />
      <BreakDialog
        open={breakOpen}
        onOpenChange={setBreakOpen}
        slug={habit.slug}
        name={habit.name}
        defaultDay={asOf}
        onSaved={refresh}
      />
    </div>
  )
}

function Stat({ label, value, hint }: { label: string; value: string; hint?: string }) {
  return (
    <div className="rounded-2xl border border-line bg-surface p-4">
      <p className="text-xs text-muted">{label}</p>
      <p className="mt-1 text-xl font-semibold tracking-tight">{value}</p>
      {hint ? <p className="mt-1 text-xs text-muted">{hint}</p> : null}
    </div>
  )
}
