import { Moon } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Hypnogram, NightsChart, StageLegend, StageSplit } from '@/components/sleep/SleepCharts'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import type { SleepNight, SleepView } from '@/lib/api'
import { formatMinutes } from '@/lib/format'
import { formatClock } from '@/lib/sleep'

export const SLEEP_EMPTY = 'No sleep data yet. It will appear here once a data source is connected.'

export function SleepCard({ view, search = '' }: { view: SleepView | null; search?: string }) {
  const empty = view !== null && view.nights_logged === 0 && view.last_recorded_at === null
  return (
    <Card className="flex flex-col">
      <CardHeader>
        <div>
          <CardTitle className="flex items-center gap-2 text-base">
            <Moon className="size-4 text-sleep" aria-hidden />
            Sleep
          </CardTitle>
          <CardDescription>Last night and the past 7 nights</CardDescription>
        </div>
        <Link
          to={{ pathname: '/stats/sleep', search }}
          className="text-xs font-medium text-sleep hover:underline"
        >
          View all
        </Link>
      </CardHeader>
      {view === null ? (
        <p className="text-sm text-muted">Sleep data is unavailable right now.</p>
      ) : empty ? (
        <p className="text-sm text-muted">{SLEEP_EMPTY}</p>
      ) : (
        <div className="grid gap-6 md:grid-cols-[minmax(0,1fr)_minmax(0,1.15fr)]">
          <LastNight night={view.night} />
          <WeekNights view={view} />
        </div>
      )}
    </Card>
  )
}

function LastNight({ night }: { night: SleepNight | null }) {
  if (night === null) {
    return (
      <section aria-label="Last night">
        <p className="text-xs font-medium uppercase tracking-wide text-muted">Last night</p>
        <p className="mt-2 text-sm text-muted">No data for last night.</p>
      </section>
    )
  }
  return (
    <section aria-label="Last night" className="flex flex-col gap-3">
      <div>
        <p className="text-xs font-medium uppercase tracking-wide text-muted">Last night</p>
        <p className="text-3xl font-semibold tracking-tight">
          {formatMinutes(night.asleep_minutes)}
        </p>
        <p className="text-sm text-muted">
          {formatClock(night.bed_offset)} → {formatClock(night.wake_offset)} · in bed{' '}
          {formatMinutes(night.in_bed_minutes)}
        </p>
      </div>
      {night.segments.length === 0 ? (
        <p className="text-xs text-muted">No sleep stages recorded for this night.</p>
      ) : (
        <>
          <Hypnogram night={night} />
          <StageSplit stages={night.stages} />
        </>
      )}
    </section>
  )
}

function WeekNights({ view }: { view: SleepView }) {
  return (
    <section aria-label="Past 7 nights" className="flex flex-col gap-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="text-xs font-medium uppercase tracking-wide text-muted">Past 7 nights</p>
        <p className="text-xs text-muted">
          {view.nights_logged} of {view.days.length} nights recorded
        </p>
      </div>
      <dl className="grid grid-cols-3 gap-2 text-xs">
        <WeekStat label="Avg sleep" value={formatMinutes(view.average_asleep)} />
        <WeekStat label="Avg bedtime" value={formatClock(view.average_bed_offset)} />
        <WeekStat label="Avg wake" value={formatClock(view.average_wake_offset)} />
      </dl>
      <NightsChart view={view} />
      <StageLegend withGap={view.nights_logged < view.days.length} />
    </section>
  )
}

function WeekStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg bg-raised px-2 py-1.5">
      <dt className="text-muted">{label}</dt>
      <dd className="text-sm font-semibold tabular-nums text-ink">{value}</dd>
    </div>
  )
}
