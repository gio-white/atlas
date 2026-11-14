import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { EmptyState, PageHeader, PageLoading, PageUnavailable } from '@/components/PageState'
import { ApiError, type Entry, getJournal, listEntries } from '@/lib/api'
import { useAsOf } from '@/lib/asOf'
import { longDateLabel } from '@/lib/dates'
import { historyRange } from '@/lib/entries'

const JOURNAL_METRIC = 'journal'
const PAST_DAYS = 90

/**
 * Earlier notes: the notes written before today, newest first. Today's note is written on Home,
 * which links here; this page has no entry on the rail.
 */
export function JournalPage() {
  const asOf = useAsOf()
  const [params] = useSearchParams()
  const on = params.get('on')
  const search = on === null ? '' : new URLSearchParams({ on }).toString()
  const [past, setPast] = useState<Entry[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setError(null)
    async function load() {
      // GET /journal creates the journal metric on first use, so it must land before the list.
      await getJournal(asOf)
      const { start } = historyRange(asOf, PAST_DAYS)
      const rows = await listEntries({ metric: JOURNAL_METRIC, start_on: start, end_on: asOf })
      return rows.filter((entry) => entry.occurred_on !== asOf)
    }
    load()
      .then((rows) => {
        if (!cancelled) setPast(rows)
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setError(
            caught instanceof ApiError && caught.status === 0
              ? caught.message
              : 'Couldn’t load your notes.',
          )
        }
      })
    return () => {
      cancelled = true
    }
  }, [asOf])

  if (error !== null) return <PageUnavailable title="Earlier notes" message={error} />
  if (past === null) return <PageLoading />

  return (
    <div className="flex max-w-3xl flex-col gap-5">
      <div className="flex flex-col gap-1">
        <Link to={{ pathname: '/', search }} className="w-fit text-sm text-muted hover:text-ink">
          Home
        </Link>
        <PageHeader
          title="Earlier notes"
          description={`Your notes from the last ${PAST_DAYS} days. Write today’s on Home.`}
        />
      </div>
      {past.length === 0 ? (
        <EmptyState
          title="No earlier notes"
          hint="Notes you write on Home show up here from the next day."
        />
      ) : (
        <ul className="flex flex-col gap-3">
          {past.map((entry) => (
            <li key={entry.id} className="rounded-2xl border border-line bg-surface px-4 py-3">
              <p className="text-xs font-medium text-muted">{longDateLabel(entry.occurred_on)}</p>
              <p className="mt-1 whitespace-pre-wrap text-sm text-ink">{entry.value_text}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
