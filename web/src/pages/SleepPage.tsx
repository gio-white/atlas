import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { Segmented } from '@/components/home/Segmented'
import { EmptyState, PageHeader, PageLoading, PageUnavailable } from '@/components/PageState'
import {
  AsleepTrend,
  GapLegend,
  NightsChart,
  StageLegend,
  StageSplit,
} from '@/components/sleep/SleepCharts'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ApiError, getSleepView, type SleepNight, type SleepView } from '@/lib/api'
import { useAsOf } from '@/lib/asOf'
import { longDateLabel } from '@/lib/dates'
import { formatMinutes } from '@/lib/format'
import { lastUpdatedLabel } from '@/lib/freshness'
import {
  consistencyLabel,
  daysNewestFirst,
  formatClock,
  formatSpread,
  parseSleepRange,
  rangeDays,
  SLEEP_RANGES,
  SLEEP_STAGE_META,
  type SleepRange,
  stageShares,
} from '@/lib/sleep'
import { cn } from '@/lib/utils'

export function SleepPage() {
  const asOf = useAsOf()
  const [params, setParams] = useSearchParams()
  const range = parseSleepRange(params.get('range'))
  const [view, setView] = useState<SleepView | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setError(null)
    getSleepView(asOf, rangeDays(range))
      .then((next) => {
        if (!cancelled) setView(next)
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setError(caught instanceof ApiError ? caught.message : 'Could not load sleep')
          setView(null)
        }
      })
    return () => {
      cancelled = true
    }
  }, [asOf, range])

  function setRange(next: SleepRange) {
    const copy = new URLSearchParams(params)
    if (next === 'week') copy.delete('range')
    else copy.set('range', next)
    setParams(copy, { replace: true })
  }

  if (error !== null) return <PageUnavailable tab title="Sleep" message={error} />
  if (view === null) return <PageLoading />

  const updated = lastUpdatedLabel(view.last_recorded_at)
  const hasData = view.last_recorded_at !== null

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <PageHeader
            tab
            title="Sleep"
            description="Rest and recovery, as recorded by your devices."
          />
          {updated !== null && <p className="text-xs text-muted">{updated}</p>}
        </div>
        {hasData && (
          <Segmented
            label="Sleep range"
            options={SLEEP_RANGES.map(({ id, label }) => ({ id, label }))}
            value={range}
            onChange={setRange}
          />
        )}
      </div>

      {!hasData ? (
        <EmptyState
          title="No sleep data yet"
          hint="It will appear here once a data source is connected."
        />
      ) : (
        <SleepDisplay view={view} />
      )}
    </div>
  )
}

function SleepDisplay({ view }: { view: SleepView }) {
  const total = view.days.length
  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Stat
          title="Average asleep"
          value={formatMinutes(view.average_asleep)}
          hint={`${view.nights_logged} of ${total} nights recorded`}
        />
        <Stat
          title="Average bedtime"
          value={formatClock(view.average_bed_offset)}
          hint={spreadHint(view.bed_spread)}
        />
        <Stat
          title="Average wake"
          value={formatClock(view.average_wake_offset)}
          hint={spreadHint(view.wake_spread)}
        />
        <Stat
          title="Missing nights"
          value={String(total - view.nights_logged)}
          hint={total - view.nights_logged === 0 ? 'Every night recorded' : 'Shown as No data'}
        />
      </div>

      {view.nights_logged === 0 ? (
        <EmptyState
          title="No nights in this range"
          hint="Pick a longer range to see earlier nights."
        />
      ) : (
        <>
          <div className="grid gap-4 xl:grid-cols-2">
            <Card>
              <CardHeader>
                <div>
                  <CardTitle className="text-base">Time asleep</CardTitle>
                  <CardDescription>Each night, with the average as a dashed line</CardDescription>
                </div>
              </CardHeader>
              <AsleepTrend view={view} />
              <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-muted">
                <span className="flex items-center gap-1.5">
                  <span className="size-2 rounded-sm bg-sleep" aria-hidden />
                  Asleep
                </span>
                <GapLegend />
              </div>
            </Card>
            <Card>
              <CardHeader>
                <div>
                  <CardTitle className="text-base">Bedtime and wake</CardTitle>
                  <CardDescription>
                    Dashed lines are your average bedtime and wake time
                  </CardDescription>
                </div>
              </CardHeader>
              <NightsChart view={view} width={640} height={200} showAverages />
              <div className="mt-2">
                <StageLegend withGap />
              </div>
            </Card>
          </div>

          <div className="grid items-start gap-4 lg:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]">
            <Card>
              <CardHeader>
                <div>
                  <CardTitle className="text-base">Average stage split</CardTitle>
                  <CardDescription>Per night, over nights with stages</CardDescription>
                </div>
              </CardHeader>
              {view.average_stages === null ? (
                <p className="text-sm text-muted">No sleep stages recorded in this range.</p>
              ) : (
                <StageSplit stages={view.average_stages} />
              )}
            </Card>
            <NightsList view={view} />
          </div>
        </>
      )}
    </>
  )
}

function spreadHint(spread: number | null): string {
  return spread === null
    ? consistencyLabel(spread)
    : `${consistencyLabel(spread)} · ${formatSpread(spread)}`
}

function Stat({ title, value, hint }: { title: string; value: string; hint: string }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <p className="text-3xl font-semibold tracking-tight tabular-nums">{value}</p>
      <p className="mt-1 text-sm text-muted">{hint}</p>
    </Card>
  )
}

function NightsList({ view }: { view: SleepView }) {
  return (
    <section className="flex flex-col gap-3" aria-labelledby="sleep-nights">
      <h2 id="sleep-nights" className="text-lg font-semibold text-ink">
        Nights
      </h2>
      <ul
        aria-label="Nights"
        className="flex max-h-[32rem] flex-col divide-y divide-line overflow-y-auto rounded-2xl border border-line bg-surface"
      >
        {daysNewestFirst(view).map((day) => (
          <NightRow key={day.date} date={day.date} night={day.night} />
        ))}
      </ul>
    </section>
  )
}

function NightRow({ date, night }: { date: string; night: SleepNight | null }) {
  return (
    <li className="flex flex-wrap items-center gap-x-4 gap-y-2 px-4 py-3 text-sm">
      <div className="min-w-0 flex-1">
        <p className={cn('font-medium', night === null ? 'text-muted' : 'text-ink')}>
          {longDateLabel(date)}
        </p>
        {night === null ? (
          <p className="text-muted">No data</p>
        ) : (
          <p className="text-muted">
            {formatClock(night.bed_offset)} → {formatClock(night.wake_offset)} · in bed{' '}
            {formatMinutes(night.in_bed_minutes)}
          </p>
        )}
      </div>
      {night !== null && (
        <div className="flex w-full items-center gap-3 sm:w-56">
          <StageBar night={night} />
          <span className="w-16 text-right font-semibold tabular-nums text-ink">
            {formatMinutes(night.asleep_minutes)}
          </span>
        </div>
      )}
    </li>
  )
}

function StageBar({ night }: { night: SleepNight }) {
  if (night.segments.length === 0) {
    return <span className="h-2 flex-1 rounded-full bg-sleep/60" title="No stages recorded" />
  }
  const shares = stageShares(night.stages)
  return (
    <span
      className="flex h-2 flex-1 overflow-hidden rounded-full bg-raised"
      title={shares
        .map((item) => `${SLEEP_STAGE_META[item.stage].label} ${formatMinutes(item.minutes)}`)
        .join(' · ')}
    >
      {shares.map((item) => (
        <span
          key={item.stage}
          className={cn('h-full', SLEEP_STAGE_META[item.stage].bg)}
          style={{ width: `${item.share * 100}%` }}
        />
      ))}
    </span>
  )
}
