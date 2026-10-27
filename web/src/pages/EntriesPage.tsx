import { Pencil, Trash2 } from 'lucide-react'
import { type FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import {
  EmptyState,
  PageError,
  PageHeader,
  PageLoading,
  PageUnavailable,
} from '@/components/PageState'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import {
  ApiError,
  amendEntry,
  deleteEntry,
  type Entry,
  listEntries,
  listMetrics,
  type Metric,
} from '@/lib/api'
import { useAsOf } from '@/lib/asOf'
import { longDateLabel } from '@/lib/dates'
import {
  amendBodyFromDraft,
  draftFromEntry,
  type EntryDraft,
  entryValueLabel,
  groupEntriesByDay,
  historyRange,
} from '@/lib/entries'

function message(caught: unknown, fallback: string): string {
  return caught instanceof ApiError || caught instanceof Error ? caught.message : fallback
}

export function EntriesPage() {
  const asOf = useAsOf()
  const [params, setParams] = useSearchParams()
  const defaults = useMemo(() => historyRange(asOf), [asOf])
  const metricFilter = params.get('metric') ?? ''
  const start = params.get('from') ?? defaults.start
  const end = params.get('to') ?? defaults.end
  const [entries, setEntries] = useState<Entry[] | null>(null)
  const [metrics, setMetrics] = useState<Metric[]>([])
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    const [nextEntries, nextMetrics] = await Promise.all([
      listEntries({
        metric: metricFilter || undefined,
        start_on: start,
        end_on: end,
        limit: 500,
      }),
      listMetrics(undefined, true),
    ])
    setEntries(nextEntries)
    setMetrics(nextMetrics)
  }, [metricFilter, start, end])

  useEffect(() => {
    let cancelled = false
    setError(null)
    refresh().catch((caught: unknown) => {
      if (!cancelled) {
        setError(message(caught, 'Could not load entries'))
        setEntries(null)
      }
    })
    return () => {
      cancelled = true
    }
  }, [refresh])

  const bySlug = useMemo(() => new Map(metrics.map((metric) => [metric.slug, metric])), [metrics])
  const days = useMemo(() => groupEntriesByDay(entries ?? []), [entries])

  function setFilter(key: 'metric' | 'from' | 'to', value: string) {
    const next = new URLSearchParams(params)
    if (value === '') next.delete(key)
    else next.set(key, value)
    setParams(next, { replace: true })
  }

  async function run(action: () => Promise<unknown>, fallback: string): Promise<boolean> {
    setActionError(null)
    try {
      await action()
      await refresh()
      return true
    } catch (caught) {
      setActionError(message(caught, fallback))
      return false
    }
  }

  if (error !== null) return <PageUnavailable title="History" message={error} />
  if (entries === null) return <PageLoading />

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="History"
        description="Everything you have logged. Fix a value, move it to another day, or delete it — streaks and goals recompute on their own."
        homeLink
      />
      <div className="grid gap-3 sm:grid-cols-3">
        <div className="flex flex-col gap-1">
          <Label htmlFor="history-metric">Metric</Label>
          <Select
            id="history-metric"
            value={metricFilter}
            onChange={(event) => setFilter('metric', event.target.value)}
          >
            <option value="">All metrics</option>
            {metrics.map((metric) => (
              <option key={metric.slug} value={metric.slug}>
                {metric.name}
                {metric.archived_at !== null ? ' (archived)' : ''}
              </option>
            ))}
          </Select>
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="history-from">From</Label>
          <Input
            id="history-from"
            type="date"
            value={start}
            max={end}
            onChange={(event) => setFilter('from', event.target.value)}
          />
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="history-to">To</Label>
          <Input
            id="history-to"
            type="date"
            value={end}
            min={start}
            onChange={(event) => setFilter('to', event.target.value)}
          />
        </div>
      </div>
      {actionError !== null && <PageError message={actionError} />}
      {days.length === 0 ? (
        <EmptyState
          title="Nothing logged in this range"
          hint="Widen the dates or pick another metric."
        />
      ) : (
        <div className="flex flex-col gap-5">
          {days.map((day) => (
            <section key={day.day} className="flex flex-col gap-2" aria-label={day.day}>
              <h2 className="text-sm font-medium text-muted">{longDateLabel(day.day)}</h2>
              <ul className="flex flex-col divide-y divide-line rounded-2xl border border-line bg-surface">
                {day.entries.map((entry) => (
                  <EntryRow
                    key={entry.id}
                    entry={entry}
                    metric={bySlug.get(entry.metric)}
                    onSave={(body) => run(() => amendEntry(entry.id, body), 'Could not save entry')}
                    onDelete={() => run(() => deleteEntry(entry.id), 'Could not delete entry')}
                  />
                ))}
              </ul>
            </section>
          ))}
          {entries.length >= 500 && (
            <p className="text-sm text-muted">Showing the latest 500 entries. Narrow the dates.</p>
          )}
        </div>
      )}
    </div>
  )
}

function EntryRow({
  entry,
  metric,
  onSave,
  onDelete,
}: {
  entry: Entry
  metric: Metric | undefined
  onSave: (body: ReturnType<typeof amendBodyFromDraft>) => Promise<boolean>
  onDelete: () => Promise<boolean>
}) {
  const [draft, setDraft] = useState<EntryDraft | null>(null)
  const [confirming, setConfirming] = useState(false)
  const [pending, setPending] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const name = metric?.name ?? entry.metric

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (draft === null) return
    setFormError(null)
    let body: ReturnType<typeof amendBodyFromDraft>
    try {
      body = amendBodyFromDraft(entry, metric, draft)
    } catch (caught) {
      setFormError(message(caught, 'Invalid value'))
      return
    }
    if (Object.keys(body).length === 0) {
      setDraft(null)
      return
    }
    setPending(true)
    if (await onSave(body)) setDraft(null)
    setPending(false)
  }

  if (draft !== null) {
    const id = `entry-${entry.id}`
    return (
      <li className="px-4 py-3">
        <form className="flex flex-col gap-3" onSubmit={onSubmit} aria-label={`Edit ${name}`}>
          <p className="text-sm font-medium text-ink">{name}</p>
          <div className="grid gap-3 sm:grid-cols-3">
            {metric === undefined ? null : metric.value_type === 'bool' ? (
              <div className="flex flex-col gap-1">
                <Label htmlFor={`${id}-bool`}>Value</Label>
                <Select
                  id={`${id}-bool`}
                  value={draft.boolValue ? 'true' : 'false'}
                  onChange={(event) =>
                    setDraft({ ...draft, boolValue: event.target.value === 'true' })
                  }
                >
                  <option value="true">yes</option>
                  <option value="false">no</option>
                </Select>
              </div>
            ) : (
              <div className="flex flex-col gap-1">
                <Label htmlFor={`${id}-value`}>
                  Value{metric.unit !== null ? ` (${metric.unit})` : ''}
                </Label>
                <Input
                  id={`${id}-value`}
                  inputMode={metric.value_type === 'text' ? 'text' : 'decimal'}
                  value={draft.raw}
                  onChange={(event) => setDraft({ ...draft, raw: event.target.value })}
                />
              </div>
            )}
            <div className="flex flex-col gap-1">
              <Label htmlFor={`${id}-date`}>Day</Label>
              <Input
                id={`${id}-date`}
                type="date"
                required
                value={draft.occurredOn}
                onChange={(event) => setDraft({ ...draft, occurredOn: event.target.value })}
              />
            </div>
            <div className="flex flex-col gap-1">
              <Label htmlFor={`${id}-note`}>Note</Label>
              <Input
                id={`${id}-note`}
                value={draft.note}
                onChange={(event) => setDraft({ ...draft, note: event.target.value })}
              />
            </div>
          </div>
          {formError !== null && (
            <p className="text-sm text-bad" role="alert">
              {formError}
            </p>
          )}
          <div className="flex gap-2">
            <Button type="submit" size="sm" disabled={pending}>
              Save
            </Button>
            <Button type="button" size="sm" variant="ghost" onClick={() => setDraft(null)}>
              Cancel
            </Button>
          </div>
        </form>
      </li>
    )
  }

  return (
    <li className="flex flex-wrap items-center gap-x-4 gap-y-1 px-4 py-3">
      <div className="min-w-0 flex-1">
        <p className="text-sm text-ink">
          <span className="font-medium">{name}</span>{' '}
          <span className="font-mono text-muted">{entryValueLabel(entry, metric)}</span>
        </p>
        {entry.note !== null && <p className="text-sm text-muted">{entry.note}</p>}
      </div>
      {confirming ? (
        <div className="flex items-center gap-2">
          <span className="text-sm text-muted">Delete this entry?</span>
          <Button
            type="button"
            size="sm"
            variant="destructive"
            disabled={pending}
            onClick={async () => {
              setPending(true)
              if (!(await onDelete())) {
                setPending(false)
                setConfirming(false)
              }
            }}
          >
            Delete
          </Button>
          <Button type="button" size="sm" variant="ghost" onClick={() => setConfirming(false)}>
            Keep
          </Button>
        </div>
      ) : (
        <div className="flex items-center gap-1">
          <Button
            type="button"
            size="icon"
            variant="ghost"
            aria-label={`Edit ${name} entry`}
            onClick={() => setDraft(draftFromEntry(entry))}
          >
            <Pencil className="size-4" aria-hidden />
          </Button>
          <Button
            type="button"
            size="icon"
            variant="ghost"
            aria-label={`Delete ${name} entry`}
            onClick={() => setConfirming(true)}
          >
            <Trash2 className="size-4" aria-hidden />
          </Button>
        </div>
      )}
    </li>
  )
}
