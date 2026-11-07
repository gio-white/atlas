import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { CountDonut, countSlices } from '@/components/entertainment/Charts'
import { PosterCard } from '@/components/entertainment/Posters'
import { SectionHeader } from '@/components/entertainment/SectionHeader'
import { useLibrary } from '@/components/entertainment/useLibrary'
import { Segmented } from '@/components/home/Segmented'
import { EmptyState, PageLoading, PageUnavailable } from '@/components/PageState'
import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  ApiError,
  type EntertainmentDashboard,
  getEntertainmentDashboard,
  type Period,
} from '@/lib/api'
import { useAsOf } from '@/lib/asOf'
import { shiftPeriodDate, shortDateLabel } from '@/lib/dates'
import { KIND_LABEL, STATUS_LABEL } from '@/lib/entertainment'
import { todayIso } from '@/lib/utils'

const PERIODS: { id: Period; label: string }[] = [
  { id: 'day', label: 'Day' },
  { id: 'week', label: 'Week' },
  { id: 'month', label: 'Month' },
]

function parsePeriod(raw: string | null): Period {
  if (raw === 'day' || raw === 'week' || raw === 'month') return raw
  return 'week'
}

export function EntertainmentInsightsPage() {
  const { titles, error } = useLibrary()
  if (error !== null) return <PageUnavailable title="Insights" message={error} />
  if (titles === null) return <PageLoading />
  return (
    <div className="flex flex-col gap-6">
      <SectionHeader
        icon="insights"
        title="Insights"
        description="What you finished, by kind and tag, over a day, week, or month."
      />
      <InsightsBody titleCount={titles.length} />
    </div>
  )
}

function InsightsBody({ titleCount }: { titleCount: number }) {
  const asOf = useAsOf()
  const [params, setParams] = useSearchParams()
  const period = parsePeriod(params.get('period'))
  const [dash, setDash] = useState<EntertainmentDashboard | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setError(null)
    getEntertainmentDashboard(period, asOf)
      .then((next) => {
        if (!cancelled) setDash(next)
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setError(caught instanceof ApiError ? caught.message : 'Could not load insights')
        }
      })
    return () => {
      cancelled = true
    }
  }, [asOf, period])

  function setPeriod(next: Period) {
    const copy = new URLSearchParams(params)
    if (next === 'week') copy.delete('period')
    else copy.set('period', next)
    setParams(copy, { replace: true })
  }

  function shift(delta: number) {
    const copy = new URLSearchParams(params)
    const next = shiftPeriodDate(asOf, period, delta)
    if (next === todayIso()) copy.delete('on')
    else copy.set('on', next)
    setParams(copy, { replace: true })
  }

  if (error !== null) return <p className="text-sm text-bad">{error}</p>
  if (dash === null) return <PageLoading />
  if (titleCount === 0) {
    return (
      <EmptyState
        title="Nothing in the library yet"
        hint="Add a film, series, book, podcast, or album and insights will appear here."
      />
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm text-muted">
          {shortDateLabel(dash.range_start)} – {shortDateLabel(dash.range_end)}
        </p>
        <div className="flex items-center gap-2">
          <Segmented label="Period" options={PERIODS} value={period} onChange={setPeriod} />
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => shift(-1)}
            aria-label="Previous"
          >
            <ChevronLeft className="size-4" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => shift(1)}
            aria-label="Next"
          >
            <ChevronRight className="size-4" />
          </Button>
        </div>
      </div>
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Finished" value={dash.finished_in_range} hint="in this period" />
        <StatCard label="In progress" value={dash.in_progress} hint="right now" />
        <StatCard label={STATUS_LABEL.queued} value={dash.queued} hint="waiting" />
        <StatCard label="Dropped" value={dash.dropped} hint="left unfinished" />
      </section>
      <section className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Finished by kind</CardTitle>
            <CardDescription>This period</CardDescription>
          </CardHeader>
          <CountDonut
            label="Finished by kind"
            slices={countSlices(
              dash.by_kind.map((row) => ({
                slug: row.kind,
                name: KIND_LABEL[row.kind],
                count: row.count,
              })),
            )}
          />
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Finished by tag</CardTitle>
            <CardDescription>This period</CardDescription>
          </CardHeader>
          <CountDonut
            label="Finished by tag"
            slices={countSlices(
              dash.by_topic.map((row) => ({
                slug: row.slug,
                name: row.name,
                count: row.count,
              })),
            )}
          />
        </Card>
      </section>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recently finished</CardTitle>
        </CardHeader>
        {dash.recently_finished.length === 0 ? (
          <p className="text-sm text-muted">Nothing marked done yet.</p>
        ) : (
          <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {dash.recently_finished.map((title) => (
              <li key={title.slug}>
                <PosterCard title={title} />
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  )
}

function StatCard({ label, value, hint }: { label: string; value: number; hint: string }) {
  return (
    <Card>
      <p className="text-sm text-muted">{label}</p>
      <p className="mt-1 text-3xl font-semibold tracking-tight">{value}</p>
      <p className="mt-1 text-xs text-muted">{hint}</p>
    </Card>
  )
}
