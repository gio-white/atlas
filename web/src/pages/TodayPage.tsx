import { type FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { LogForm } from '@/components/LogForm'
import { PaceBadge } from '@/components/PaceBadge'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import {
  ApiError,
  amendEntry,
  deleteEntry,
  getToday,
  type HabitStatus,
  type LoggedEntry,
  listMetrics,
  logEntry,
  type Metric,
  type TodayView,
} from '@/lib/api'
import { useAsOf } from '@/lib/asOf'
import { formatComparator, formatEntryValue, formatPercent } from '@/lib/format'
import { parseLogValue, rawFromEntry } from '@/lib/value'

export function TodayPage() {
  const asOf = useAsOf()
  const [params] = useSearchParams()
  const [view, setView] = useState<TodayView | null>(null)
  const [metrics, setMetrics] = useState<Metric[]>([])
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    const [today, metricRows] = await Promise.all([getToday(asOf), listMetrics()])
    setView(today)
    setMetrics(metricRows)
  }, [asOf])

  useEffect(() => {
    let cancelled = false
    setError(null)
    refresh().catch((caught: unknown) => {
      if (!cancelled) {
        setError(caught instanceof ApiError ? caught.message : 'Could not load today')
        setView(null)
      }
    })
    return () => {
      cancelled = true
    }
  }, [refresh])

  const metricBySlug = useMemo(
    () => Object.fromEntries(metrics.map((metric) => [metric.slug, metric])),
    [metrics],
  )

  if (error !== null) {
    return <p className="text-sm text-bad">{error}</p>
  }
  if (view === null) {
    return <p className="text-sm text-muted">Loading…</p>
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
      <div className="flex flex-col gap-6">
        <section className="flex flex-col gap-3">
          <h1 className="font-serif text-2xl tracking-tight">Today</h1>
          <p className="font-mono text-xs text-muted">{view.as_of}</p>
          {view.habits.length === 0 ? (
            <p className="text-sm text-muted">No habits scheduled.</p>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              {view.habits.map((habit) => (
                <HabitCard
                  key={habit.slug}
                  habit={habit}
                  metric={metricBySlug[habit.metric_slug]}
                  search={params.toString()}
                  asOf={asOf}
                  onLogged={refresh}
                />
              ))}
            </div>
          )}
        </section>
        <Card>
          <CardHeader>
            <div>
              <CardTitle>Log</CardTitle>
              <CardDescription className="mt-1">
                One capture path. Counts for {asOf}.
              </CardDescription>
            </div>
          </CardHeader>
          <LogForm metrics={metrics} occurredOn={asOf} onLogged={refresh} />
        </Card>
        <Card>
          <CardHeader>
            <CardTitle>Logged</CardTitle>
          </CardHeader>
          {view.entries.length === 0 ? (
            <p className="text-sm text-muted">Nothing logged yet.</p>
          ) : (
            <ul className="flex flex-col gap-3">
              {view.entries.map((entry) => (
                <EntryRow
                  key={entry.id}
                  entry={entry}
                  metric={metricBySlug[entry.metric_slug]}
                  onChanged={refresh}
                />
              ))}
            </ul>
          )}
        </Card>
      </div>
      <aside className="flex flex-col gap-3">
        <h2 className="font-serif text-lg">Goals</h2>
        {view.goals.length === 0 ? (
          <p className="text-sm text-muted">No active goals.</p>
        ) : (
          view.goals.map((goal) => (
            <Link
              key={goal.slug}
              to={{ pathname: `/goal/${goal.slug}`, search: params.toString() }}
              className="rounded-xl border border-line bg-surface p-3 hover:bg-raised"
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-medium">{goal.name}</p>
                <PaceBadge pace={goal.pace} />
              </div>
              <p className="mt-2 font-mono text-xs text-muted">{formatPercent(goal.fraction)}</p>
            </Link>
          ))
        )}
      </aside>
    </div>
  )
}

function HabitCard({
  habit,
  metric,
  search,
  asOf,
  onLogged,
}: {
  habit: HabitStatus
  metric: Metric | undefined
  search: string
  asOf: string
  onLogged: () => Promise<void>
}) {
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const canQuickLog = metric?.value_type === 'bool'

  async function quickLog() {
    setError(null)
    setPending(true)
    try {
      await logEntry({ metric: habit.metric_slug, occurred_on: asOf })
      await onLogged()
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Could not log')
    } finally {
      setPending(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <div>
          <Link
            to={{ pathname: `/habit/${habit.slug}`, search }}
            className="font-serif text-lg hover:text-accent"
          >
            {habit.name}
          </Link>
          <p className="mt-1 font-mono text-xs text-muted">
            {formatComparator(habit.comparator)} {habit.target_value} · {habit.period}
          </p>
        </div>
        <Badge tone={habit.satisfied ? 'good' : 'warn'}>{habit.satisfied ? 'done' : 'open'}</Badge>
      </CardHeader>
      <div className="flex items-end justify-between gap-3">
        <div>
          <p className="font-mono text-2xl leading-none">{habit.current_streak}</p>
          <p className="mt-1 text-xs text-muted">
            streak · best {habit.longest_streak}
            {habit.current_value !== null ? ` · now ${habit.current_value}` : ''}
          </p>
        </div>
        {canQuickLog && (
          <Button type="button" size="sm" variant="secondary" disabled={pending} onClick={quickLog}>
            {pending ? '…' : 'Log'}
          </Button>
        )}
      </div>
      {error !== null && <p className="mt-2 text-xs text-bad">{error}</p>}
    </Card>
  )
}

function EntryRow({
  entry,
  metric,
  onChanged,
}: {
  entry: LoggedEntry
  metric: Metric | undefined
  onChanged: () => Promise<void>
}) {
  const [editing, setEditing] = useState(false)
  const [raw, setRaw] = useState(rawFromEntry(entry.value_num, entry.value_bool, entry.value_text))
  const [note, setNote] = useState(entry.note ?? '')
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  async function onSave(event: FormEvent) {
    event.preventDefault()
    if (metric === undefined) return
    setError(null)
    setPending(true)
    try {
      const boolValue = raw === 'true' || raw === 'yes'
      await amendEntry(entry.id, {
        value: parseLogValue(metric.value_type, raw, boolValue),
        note: note.trim() === '' ? null : note.trim(),
      })
      setEditing(false)
      await onChanged()
    } catch (caught) {
      setError(
        caught instanceof ApiError || caught instanceof Error ? caught.message : 'Could not save',
      )
    } finally {
      setPending(false)
    }
  }

  async function onDelete() {
    setError(null)
    setPending(true)
    try {
      await deleteEntry(entry.id)
      await onChanged()
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Could not delete')
      setPending(false)
    }
  }

  if (editing) {
    return (
      <li className="rounded-lg border border-line p-3">
        <form className="flex flex-col gap-2" onSubmit={onSave}>
          <Input value={raw} onChange={(event) => setRaw(event.target.value)} aria-label="Value" />
          <Input value={note} onChange={(event) => setNote(event.target.value)} aria-label="Note" />
          {error !== null && <p className="text-xs text-bad">{error}</p>}
          <div className="flex gap-2">
            <Button type="submit" size="sm" disabled={pending}>
              Save
            </Button>
            <Button type="button" size="sm" variant="ghost" onClick={() => setEditing(false)}>
              Cancel
            </Button>
          </div>
        </form>
      </li>
    )
  }

  return (
    <li className="flex items-center justify-between gap-3">
      <div>
        <p className="text-sm">
          <span className="font-medium">{entry.metric_slug}</span>{' '}
          <span className="font-mono text-muted">
            {formatEntryValue(entry.value_num, entry.value_bool, entry.value_text)}
          </span>
        </p>
        {entry.note !== null && <p className="text-xs text-muted">{entry.note}</p>}
        {error !== null && <p className="text-xs text-bad">{error}</p>}
      </div>
      <div className="flex gap-1">
        <Button type="button" size="sm" variant="ghost" onClick={() => setEditing(true)}>
          Amend
        </Button>
        <Button type="button" size="sm" variant="ghost" disabled={pending} onClick={onDelete}>
          Delete
        </Button>
      </div>
    </li>
  )
}
