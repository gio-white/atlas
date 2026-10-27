import { Check, Flame } from 'lucide-react'
import { type FormEvent, useCallback, useEffect, useState } from 'react'

import {
  EmptyState,
  PageError,
  PageHeader,
  PageLoading,
  PageUnavailable,
} from '@/components/PageState'
import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Label } from '@/components/ui/label'
import {
  ApiError,
  amendEntry,
  type Entry,
  getJournal,
  getUpdates,
  type JournalDay,
  listEntries,
  logJournal,
  logUpdate,
  type UpdatesStatus,
} from '@/lib/api'
import { useAsOf } from '@/lib/asOf'
import { longDateLabel } from '@/lib/dates'
import { historyRange } from '@/lib/entries'

const JOURNAL_METRIC = 'journal'
const PAST_DAYS = 90

function message(caught: unknown, fallback: string): string {
  return caught instanceof ApiError ? caught.message : fallback
}

type JournalData = { today: JournalDay; updates: UpdatesStatus; past: Entry[] }

export function JournalPage() {
  const asOf = useAsOf()
  const [data, setData] = useState<JournalData | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  const refresh = useCallback(async () => {
    // GET /journal creates the journal metric on first use, so it must land before the list.
    const [today, updates] = await Promise.all([getJournal(asOf), getUpdates(asOf)])
    const { start } = historyRange(asOf, PAST_DAYS)
    const past = await listEntries({ metric: JOURNAL_METRIC, start_on: start, end_on: asOf })
    setData({ today, updates, past: past.filter((entry) => entry.occurred_on !== asOf) })
  }, [asOf])

  useEffect(() => {
    let cancelled = false
    setError(null)
    refresh().catch((caught: unknown) => {
      if (!cancelled) {
        setError(message(caught, 'Could not load the journal'))
        setData(null)
      }
    })
    return () => {
      cancelled = true
    }
  }, [refresh])

  async function run(action: () => Promise<unknown>, fallback: string): Promise<boolean> {
    setActionError(null)
    setPending(true)
    try {
      await action()
      await refresh()
      return true
    } catch (caught) {
      setActionError(message(caught, fallback))
      return false
    } finally {
      setPending(false)
    }
  }

  if (error !== null) return <PageUnavailable title="Journal" message={error} />
  if (data === null) return <PageLoading />

  const { today, updates, past } = data

  return (
    <div className="flex flex-col gap-6">
      <PageHeader
        title="Journal"
        description="A daily check-in and a few lines about the day."
        homeLink
      />
      {actionError !== null && <PageError message={actionError} />}
      <Card>
        <CardHeader className="mb-0">
          <div>
            <CardTitle>Check-in</CardTitle>
            <CardDescription className="mt-1">
              <Flame className="mr-1 inline size-4 text-update" aria-hidden />
              {updates.current_streak} day streak · best {updates.longest_streak}
            </CardDescription>
          </div>
          {updates.checked_in ? (
            <p className="inline-flex items-center gap-1 text-sm font-medium text-good">
              <Check className="size-4" aria-hidden />
              Checked in
            </p>
          ) : (
            <Button
              type="button"
              disabled={pending}
              onClick={() => run(() => logUpdate({ occurred_on: asOf }), 'Could not check in')}
            >
              Check in
            </Button>
          )}
        </CardHeader>
      </Card>
      <Card>
        <CardHeader>
          <div>
            <CardTitle>{longDateLabel(asOf)}</CardTitle>
            <CardDescription className="mt-1">
              {today.text === null ? 'Nothing written yet.' : 'Saved. Edit it any time today.'}
            </CardDescription>
          </div>
        </CardHeader>
        <div>
          <JournalForm
            key={`${asOf}-${today.entry_id ?? 'new'}`}
            initial={today.text ?? ''}
            pending={pending}
            onSave={(text) =>
              run(
                () =>
                  today.entry_id === null
                    ? logJournal({ text, occurred_on: asOf })
                    : amendEntry(today.entry_id, { value: text }),
                'Could not save the journal',
              )
            }
          />
        </div>
      </Card>
      <section className="flex flex-col gap-3" aria-labelledby="journal-past">
        <h2 id="journal-past" className="text-lg font-semibold text-ink">
          Earlier
        </h2>
        {past.length === 0 ? (
          <EmptyState title="No earlier entries" hint={`Nothing in the last ${PAST_DAYS} days.`} />
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
      </section>
    </div>
  )
}

function JournalForm({
  initial,
  pending,
  onSave,
}: {
  initial: string
  pending: boolean
  onSave: (text: string) => Promise<boolean>
}) {
  const [text, setText] = useState(initial)
  const trimmed = text.trim()

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (trimmed !== '' && trimmed !== initial) void onSave(trimmed)
  }

  return (
    <form className="flex flex-col gap-3" onSubmit={onSubmit}>
      <Label htmlFor="journal-text" className="sr-only">
        Journal text
      </Label>
      <textarea
        id="journal-text"
        rows={6}
        value={text}
        onChange={(event) => setText(event.target.value)}
        placeholder="How did today go?"
        className="w-full rounded-lg border border-line bg-canvas px-3 py-2 text-sm text-ink placeholder:text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
      />
      <div>
        <Button type="submit" disabled={pending || trimmed === '' || trimmed === initial}>
          Save
        </Button>
      </div>
    </form>
  )
}
