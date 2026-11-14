import { ChevronLeft, ChevronRight, Settings2 } from 'lucide-react'
import { useCallback, useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { Sparkline } from '@/components/home/Charts'
import { EmptyState, PageHeader, PageLoading, PageUnavailable } from '@/components/PageState'
import {
  ComparisonLines,
  categorySlices,
  deviceSlices,
  HourHeatmap,
  JUDGMENT_BG,
  JUDGMENT_LABEL,
  ScoreRing,
  ShareDonut,
  StackedJudgmentBars,
} from '@/components/screen/Charts'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ApiError, getScreenDashboard, type Period, type ScreenDashboard } from '@/lib/api'
import { useAsOf } from '@/lib/asOf'
import { shiftPeriodDate, shortDateLabel } from '@/lib/dates'
import { formatDeltaFraction, formatMinutes, formatPercent } from '@/lib/format'
import { lastUpdatedLabel } from '@/lib/freshness'
import { cn, todayIso } from '@/lib/utils'

const PERIODS: { id: Period; label: string }[] = [
  { id: 'day', label: 'Day' },
  { id: 'week', label: 'Week' },
  { id: 'month', label: 'Month' },
]

const JUDGMENT_ORDER = ['useful', 'neutral', 'waste'] as const

export const SCORE_EXPLANATION =
  'How much of your screen time went to apps you count as Good. Neutral time counts for half.'

function parsePeriod(raw: string | null): Period {
  if (raw === 'day' || raw === 'week' || raw === 'month') return raw
  return 'week'
}

export function ScreenPage() {
  const asOf = useAsOf()
  const [params, setParams] = useSearchParams()
  const period = parsePeriod(params.get('period'))
  const [dash, setDash] = useState<ScreenDashboard | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [breakdown, setBreakdown] = useState(true)

  const refresh = useCallback(async () => {
    setDash(await getScreenDashboard(period, asOf))
  }, [asOf, period])

  useEffect(() => {
    let cancelled = false
    setError(null)
    refresh().catch((caught: unknown) => {
      if (!cancelled) {
        setError(caught instanceof ApiError ? caught.message : 'Could not load screen time')
        setDash(null)
      }
    })
    return () => {
      cancelled = true
    }
  }, [refresh])

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

  if (error !== null) {
    return <PageUnavailable tab title="Screen time" message={error} />
  }
  if (dash === null) return <PageLoading />

  const updated = lastUpdatedLabel(dash.last_recorded_at)
  const hasData = dash.last_recorded_at !== null

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div className="flex flex-col gap-1">
          <PageHeader
            tab
            title="Screen time"
            description={`${shortDateLabel(dash.range_start)} – ${shortDateLabel(dash.range_end)}`}
          />
          {updated !== null && <p className="text-xs text-muted">{updated}</p>}
        </div>
        {hasData && (
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex rounded-full border border-line bg-surface p-1" role="tablist">
              {PERIODS.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  role="tab"
                  aria-selected={period === item.id}
                  className={cn(
                    'rounded-full px-3 py-1 text-sm motion-safe:transition-colors',
                    period === item.id ? 'bg-screen/20 text-ink' : 'text-muted hover:text-ink',
                  )}
                  onClick={() => setPeriod(item.id)}
                >
                  {item.label}
                </button>
              ))}
            </div>
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
        )}
      </div>

      {hasData ? (
        <ScreenDisplay
          dash={dash}
          period={period}
          breakdown={breakdown}
          onToggleBreakdown={() => setBreakdown((value) => !value)}
        />
      ) : (
        <EmptyState
          title="No screen time data yet"
          hint="It will appear here once a data source is connected."
        />
      )}

      <SetupLink />
    </div>
  )
}

function ScreenDisplay({
  dash,
  period,
  breakdown,
  onToggleBreakdown,
}: {
  dash: ScreenDashboard
  period: Period
  breakdown: boolean
  onToggleBreakdown: () => void
}) {
  const delta = formatDeltaFraction(dash.delta_fraction)
  return (
    <>
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Total</CardTitle>
            <CardDescription>vs last period</CardDescription>
          </CardHeader>
          <p className="text-3xl font-semibold tracking-tight">{formatMinutes(dash.total)}</p>
          <p className="mt-1 text-sm text-muted">
            {delta === null ? 'Nothing to compare with yet.' : delta}
          </p>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Daily average</CardTitle>
          </CardHeader>
          <p className="text-3xl font-semibold tracking-tight">
            {formatMinutes(dash.daily_average)}
          </p>
          <p className="mt-1 text-sm text-muted">Per day so far in this period</p>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Longest day</CardTitle>
          </CardHeader>
          <p className="text-3xl font-semibold tracking-tight">
            {dash.longest_day === null ? '—' : formatMinutes(dash.longest_day.minutes)}
          </p>
          <p className="mt-1 text-sm text-muted">
            {dash.longest_day === null
              ? 'No screen time in this period.'
              : shortDateLabel(dash.longest_day.date)}
          </p>
        </Card>
        <Card className="flex items-center gap-4">
          <ScoreRing score={dash.score} band={dash.score_band} />
          <div>
            <p className="text-sm font-medium">Score</p>
            <p className="mt-1 text-xs text-muted">{SCORE_EXPLANATION}</p>
          </div>
        </Card>
      </div>

      {dash.total === null ? (
        <EmptyState
          title="No screen time in this period"
          hint="Step back to an earlier period, or pick a longer one."
        />
      ) : (
        <>
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Each day</CardTitle>
                <button
                  type="button"
                  className="text-xs font-medium text-screen hover:underline"
                  onClick={onToggleBreakdown}
                >
                  {breakdown ? 'Show total only' : 'Split by Good / Bad'}
                </button>
              </CardHeader>
              <StackedJudgmentBars days={dash.daily} breakdown={breakdown} />
              {breakdown && (
                <ul className="mt-2 flex flex-wrap gap-x-3 text-[11px] text-muted">
                  {JUDGMENT_ORDER.map((judgment) => (
                    <li key={judgment} className="flex items-center gap-1.5">
                      <span className={cn('size-2 rounded-sm', JUDGMENT_BG[judgment])} />
                      {JUDGMENT_LABEL[judgment]}
                    </li>
                  ))}
                </ul>
              )}
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Vs last period</CardTitle>
                <CardDescription>Solid is this period, dashed is the one before</CardDescription>
              </CardHeader>
              <ComparisonLines points={dash.comparison} />
            </Card>
          </div>

          <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Devices</CardTitle>
              </CardHeader>
              <ShareDonut slices={deviceSlices(dash.devices)} label="Devices" />
            </Card>
            <Card className="xl:col-span-1">
              <CardHeader>
                <CardTitle className="text-base">Top apps</CardTitle>
              </CardHeader>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="text-xs text-muted">
                    <tr>
                      <th className="pb-2 font-medium">App</th>
                      <th className="pb-2 font-medium">Time</th>
                      <th className="pb-2 font-medium">Share</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dash.apps.map((app) => (
                      <tr key={app.slug} className="border-t border-line/70">
                        <td className="py-2">
                          <p className="font-medium">{app.name}</p>
                          <p className="text-xs text-muted">{app.category_name}</p>
                        </td>
                        <td className="py-2">{formatMinutes(app.minutes)}</td>
                        <td className="py-2">
                          <Badge
                            tone={
                              app.judgment === 'useful'
                                ? 'good'
                                : app.judgment === 'waste'
                                  ? 'bad'
                                  : 'warn'
                            }
                          >
                            {JUDGMENT_LABEL[app.judgment]} {formatPercent(app.share)}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Categories</CardTitle>
              </CardHeader>
              <ShareDonut slices={categorySlices(dash.categories)} label="Categories" />
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Hours</CardTitle>
                <CardDescription>Sessions with a start and end time</CardDescription>
              </CardHeader>
              <HourHeatmap hours={dash.hours} period={period} />
            </Card>
          </div>

          <div className="grid gap-4 lg:grid-cols-3">
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle className="text-base">Insights</CardTitle>
              </CardHeader>
              {dash.insights.length === 0 ? (
                <p className="text-sm text-muted">Nothing to flag in this period.</p>
              ) : (
                <ul className="flex flex-col gap-3">
                  {dash.insights.map((insight) => (
                    <li key={insight.kind} className="rounded-xl bg-raised/80 p-3">
                      <p className="text-sm font-medium">{insight.summary}</p>
                      <p className="mt-1 text-sm text-muted">{insight.prescription}</p>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">8-week trend</CardTitle>
                <CardDescription>Daily average</CardDescription>
              </CardHeader>
              <div className="text-screen">
                <Sparkline
                  values={dash.trend.map((point) => point.daily_average ?? 0)}
                  className="h-16 w-full"
                />
              </div>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Caps</CardTitle>
              </CardHeader>
              {dash.budgets.length === 0 ? (
                <p className="text-sm text-muted">No caps set. Add one in Settings.</p>
              ) : (
                <ul className="flex flex-col gap-2 text-sm">
                  {dash.budgets.map((budget) => (
                    <li key={budget.slug} className="flex items-center justify-between gap-2">
                      <span>{budget.name}</span>
                      <Badge tone={budget.satisfied ? 'good' : 'bad'}>
                        {formatMinutes(budget.current_value)} / {formatMinutes(budget.target_value)}
                      </Badge>
                    </li>
                  ))}
                </ul>
              )}
            </Card>
          </div>
        </>
      )}
    </>
  )
}

/** Configuration lives in Settings, apart from the data shown here. This is the way to it. */
function SetupLink() {
  const [params] = useSearchParams()
  const on = params.get('on')
  const search = on === null ? '' : new URLSearchParams({ on }).toString()
  return (
    <p className="border-t border-line pt-5">
      <Link
        to={{ pathname: '/settings/screen-time', search }}
        className="inline-flex items-center gap-2 text-sm font-medium text-iris hover:underline"
      >
        <Settings2 className="size-4" aria-hidden />
        Set up apps, categories and caps
      </Link>
    </p>
  )
}
