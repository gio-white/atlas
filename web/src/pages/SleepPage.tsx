import { Trash2 } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'

import { SleepCard } from '@/components/home/SleepCard'
import {
  EmptyState,
  PageError,
  PageHeader,
  PageLoading,
  PageUnavailable,
} from '@/components/PageState'
import { Button } from '@/components/ui/button'
import {
  ApiError,
  deleteSleepSession,
  getSleepView,
  listSleepSessions,
  type SleepSessionRecord,
  type SleepView,
} from '@/lib/api'
import { useAsOf } from '@/lib/asOf'
import { longDateLabel, toLocalInput } from '@/lib/dates'
import { formatMinutes } from '@/lib/format'
import { newestNightsFirst } from '@/lib/sleep'

const HISTORY_LIMIT = 60

function message(caught: unknown, fallback: string): string {
  return caught instanceof ApiError ? caught.message : fallback
}

function clock(iso: string): string {
  return toLocalInput(iso).slice(11)
}

function inBedMinutes(row: SleepSessionRecord): number {
  return (Date.parse(row.ended_at) - Date.parse(row.started_at)) / 60000
}

export function SleepPage() {
  const asOf = useAsOf()
  const [view, setView] = useState<SleepView | null>(null)
  const [sessions, setSessions] = useState<SleepSessionRecord[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    const [nextView, nextSessions] = await Promise.all([getSleepView(asOf), listSleepSessions()])
    setView(nextView)
    setSessions(nextSessions)
  }, [asOf])

  useEffect(() => {
    let cancelled = false
    setError(null)
    refresh().catch((caught: unknown) => {
      if (!cancelled) {
        setError(message(caught, 'Could not load sleep'))
        setSessions(null)
      }
    })
    return () => {
      cancelled = true
    }
  }, [refresh])

  const nights = useMemo(
    () =>
      newestNightsFirst((sessions ?? []).filter((row) => row.occurred_on <= asOf)).slice(
        0,
        HISTORY_LIMIT,
      ),
    [sessions, asOf],
  )

  if (error !== null) return <PageUnavailable title="Sleep" message={error} />
  if (sessions === null) return <PageLoading />

  return (
    <div className="flex flex-col gap-6">
      <PageHeader title="Sleep" description="Rest and recovery." homeLink />
      <SleepCard view={view} asOf={asOf} onLogged={refresh} />
      <section className="flex flex-col gap-3" aria-labelledby="sleep-history">
        <h2 id="sleep-history" className="text-lg font-semibold text-ink">
          Nights
        </h2>
        {actionError !== null && <PageError message={actionError} />}
        {nights.length === 0 ? (
          <EmptyState title="No nights logged" hint="Log last night from the card above." />
        ) : (
          <ul className="flex flex-col divide-y divide-line rounded-2xl border border-line bg-surface">
            {nights.map((row) => (
              <NightRow
                key={row.id}
                row={row}
                onDelete={async () => {
                  setActionError(null)
                  try {
                    await deleteSleepSession(row.id)
                    await refresh()
                  } catch (caught) {
                    setActionError(message(caught, 'Could not delete the night'))
                  }
                }}
              />
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}

function NightRow({ row, onDelete }: { row: SleepSessionRecord; onDelete: () => Promise<void> }) {
  const [confirming, setConfirming] = useState(false)
  return (
    <li className="flex flex-wrap items-center gap-x-4 gap-y-1 px-4 py-3 text-sm">
      <div className="min-w-0 flex-1">
        <p className="font-medium text-ink">{longDateLabel(row.occurred_on)}</p>
        <p className="text-muted">
          {clock(row.started_at)} → {clock(row.ended_at)} · in bed{' '}
          {formatMinutes(inBedMinutes(row))}
          {row.stages.length > 0
            ? ` · ${row.stages.length} ${row.stages.length === 1 ? 'stage' : 'stages'}`
            : ''}
          {row.note !== null ? ` · ${row.note}` : ''}
        </p>
      </div>
      {confirming ? (
        <div className="flex items-center gap-2">
          <span className="text-muted">Delete this night?</span>
          <Button type="button" size="sm" variant="destructive" onClick={() => void onDelete()}>
            Delete
          </Button>
          <Button type="button" size="sm" variant="ghost" onClick={() => setConfirming(false)}>
            Keep
          </Button>
        </div>
      ) : (
        <Button
          type="button"
          size="icon"
          variant="ghost"
          aria-label={`Delete night of ${row.occurred_on}`}
          onClick={() => setConfirming(true)}
        >
          <Trash2 className="size-4" aria-hidden />
        </Button>
      )}
    </li>
  )
}
