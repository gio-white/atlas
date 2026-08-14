import { ChevronLeft, ChevronRight } from 'lucide-react'
import { type FormEvent, useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { Sparkline } from '@/components/home/Charts'
import { EmptyState, PageHeader, PageLoading, PageUnavailable } from '@/components/PageState'
import {
  ComparisonLines,
  deviceSlices,
  HourHeatmap,
  JUDGMENT_BG,
  JUDGMENT_LABEL,
  JUDGMENT_STROKE,
  ScoreRing,
  ShareDonut,
  StackedJudgmentBars,
} from '@/components/screen/Charts'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import {
  ApiError,
  createScreenApp,
  createScreenCategory,
  createScreenDevice,
  getScreenDashboard,
  listScreenApps,
  listScreenCategories,
  listScreenDevices,
  logScreenSession,
  type Period,
  type ScreenApp,
  type ScreenCategory,
  type ScreenDashboard,
  type ScreenDevice,
  type ScreenJudgment,
} from '@/lib/api'
import { useAsOf } from '@/lib/asOf'
import { shiftPeriodDate, shortDateLabel } from '@/lib/dates'
import { formatDeltaFraction, formatMinutes, formatPercent } from '@/lib/format'
import { isValidSlug } from '@/lib/slug'
import { cn, todayIso } from '@/lib/utils'

const PERIODS: { id: Period; label: string }[] = [
  { id: 'day', label: 'Day' },
  { id: 'week', label: 'Week' },
  { id: 'month', label: 'Month' },
]

function parsePeriod(raw: string | null): Period {
  if (raw === 'day' || raw === 'week' || raw === 'month') return raw
  return 'week'
}

export function ScreenPage() {
  const asOf = useAsOf()
  const [params, setParams] = useSearchParams()
  const period = parsePeriod(params.get('period'))
  const [dash, setDash] = useState<ScreenDashboard | null>(null)
  const [apps, setApps] = useState<ScreenApp[]>([])
  const [categories, setCategories] = useState<ScreenCategory[]>([])
  const [devices, setDevices] = useState<ScreenDevice[]>([])
  const [error, setError] = useState<string | null>(null)
  const [breakdown, setBreakdown] = useState(true)

  const refresh = useCallback(async () => {
    const [nextDash, nextApps, nextCategories, nextDevices] = await Promise.all([
      getScreenDashboard(period, asOf),
      listScreenApps().catch(() => []),
      listScreenCategories().catch(() => []),
      listScreenDevices().catch(() => []),
    ])
    setDash(nextDash)
    setApps(nextApps)
    setCategories(nextCategories)
    setDevices(nextDevices)
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
    return <PageUnavailable title="Screen Time" message={error} />
  }
  if (dash === null) return <PageLoading />

  const delta = formatDeltaFraction(dash.delta_fraction)
  const empty = dash.total === null

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageHeader
          title="Screen Time"
          description={`${shortDateLabel(dash.range_start)} – ${shortDateLabel(dash.range_end)}`}
          homeLink
        />
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
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Total</CardTitle>
            <CardDescription>vs last period</CardDescription>
          </CardHeader>
          <p className="text-3xl font-semibold tracking-tight">{formatMinutes(dash.total)}</p>
          <p className="mt-1 text-sm text-muted">
            {delta === null ? 'No previous minutes to compare.' : delta}
          </p>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Daily average</CardTitle>
          </CardHeader>
          <p className="text-3xl font-semibold tracking-tight">
            {formatMinutes(dash.daily_average)}
          </p>
          <p className="mt-1 text-sm text-muted">Zeros included across the clipped range.</p>
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
              ? 'No sessions in range.'
              : shortDateLabel(dash.longest_day.date)}
          </p>
        </Card>
        <Card className="flex items-center gap-4">
          <ScoreRing score={dash.score} band={dash.score_band} />
          <div>
            <p className="text-sm font-medium">Score</p>
            <p className="mt-1 text-xs text-muted">
              Good + half of Neutral, over total. UI labels Good / Bad / Neutral.
            </p>
          </div>
        </Card>
      </div>

      {empty ? (
        <EmptyState
          title="No screen sessions in this range"
          hint="Log an interval or a duration below, or seed the demo dataset."
        />
      ) : (
        <>
          <div className="grid gap-4 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Daily bars</CardTitle>
                <button
                  type="button"
                  className="text-xs font-medium text-screen hover:underline"
                  onClick={() => setBreakdown((value) => !value)}
                >
                  {breakdown ? 'Show total' : 'Show breakdown'}
                </button>
              </CardHeader>
              <StackedJudgmentBars days={dash.daily} breakdown={breakdown} />
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Vs last period</CardTitle>
                <CardDescription>Solid is current, dashed is previous</CardDescription>
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
              <ShareDonut
                slices={dash.categories.map((category) => ({
                  slug: category.slug,
                  name: category.name,
                  minutes: category.minutes,
                  stroke: JUDGMENT_STROKE[category.judgment],
                  swatch: JUDGMENT_BG[category.judgment],
                }))}
                label="Categories"
              />
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Hours</CardTitle>
                <CardDescription>Interval sessions only</CardDescription>
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
                <p className="text-sm text-muted">No prescriptions for this range.</p>
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
                <CardTitle className="text-base">Budgets</CardTitle>
              </CardHeader>
              {dash.budgets.length === 0 ? (
                <p className="text-sm text-muted">Add a waste cap so overages show up here.</p>
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

      <CaptureForm apps={apps} devices={devices} asOf={asOf} onLogged={refresh} />
      <ManagePanel apps={apps} categories={categories} devices={devices} onChanged={refresh} />
    </div>
  )
}

function CaptureForm({
  apps,
  devices,
  asOf,
  onLogged,
}: {
  apps: ScreenApp[]
  devices: ScreenDevice[]
  asOf: string
  onLogged: () => Promise<void>
}) {
  const [mode, setMode] = useState<'interval' | 'duration'>('interval')
  const [app, setApp] = useState(apps[0]?.slug ?? '')
  const [device, setDevice] = useState('')
  const [minutes, setMinutes] = useState('30')
  const [started, setStarted] = useState(`${asOf}T20:00`)
  const [ended, setEnded] = useState(`${asOf}T20:30`)
  const [occurredOn, setOccurredOn] = useState(asOf)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    if (app === '' && apps[0] !== undefined) setApp(apps[0].slug)
  }, [app, apps])

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setMessage(null)
    try {
      if (mode === 'interval') {
        await logScreenSession({
          app,
          device: device || null,
          started_at: new Date(started).toISOString(),
          ended_at: new Date(ended).toISOString(),
        })
      } else {
        await logScreenSession({
          app,
          device: device || null,
          minutes: Number(minutes),
          occurred_on: occurredOn,
        })
      }
      await onLogged()
    } catch (caught: unknown) {
      setMessage(caught instanceof ApiError ? caught.message : 'Could not log session')
    } finally {
      setBusy(false)
    }
  }

  if (apps.length === 0) return null

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Log a session</CardTitle>
        <CardDescription>Interval or duration — not a mix</CardDescription>
      </CardHeader>
      <form className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4" onSubmit={onSubmit}>
        <div className="flex flex-col gap-1">
          <Label htmlFor="screen-app">App</Label>
          <Select id="screen-app" value={app} onChange={(event) => setApp(event.target.value)}>
            {apps.map((row) => (
              <option key={row.slug} value={row.slug}>
                {row.name}
              </option>
            ))}
          </Select>
        </div>
        <div className="flex flex-col gap-1">
          <Label htmlFor="screen-device">Device</Label>
          <Select
            id="screen-device"
            value={device}
            onChange={(event) => setDevice(event.target.value)}
          >
            <option value="">Unknown</option>
            {devices.map((row) => (
              <option key={row.slug} value={row.slug}>
                {row.name}
              </option>
            ))}
          </Select>
        </div>
        <div className="flex flex-col gap-1 sm:col-span-2">
          <Label>Shape</Label>
          <div className="flex gap-2">
            <Button
              type="button"
              size="sm"
              variant={mode === 'interval' ? 'default' : 'secondary'}
              onClick={() => setMode('interval')}
            >
              Interval
            </Button>
            <Button
              type="button"
              size="sm"
              variant={mode === 'duration' ? 'default' : 'secondary'}
              onClick={() => setMode('duration')}
            >
              Duration
            </Button>
          </div>
        </div>
        {mode === 'interval' ? (
          <>
            <div className="flex flex-col gap-1">
              <Label htmlFor="screen-from">From</Label>
              <Input
                id="screen-from"
                type="datetime-local"
                value={started}
                onChange={(event) => setStarted(event.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1">
              <Label htmlFor="screen-to">To</Label>
              <Input
                id="screen-to"
                type="datetime-local"
                value={ended}
                onChange={(event) => setEnded(event.target.value)}
              />
            </div>
          </>
        ) : (
          <>
            <div className="flex flex-col gap-1">
              <Label htmlFor="screen-minutes">Minutes</Label>
              <Input
                id="screen-minutes"
                type="number"
                min="0.01"
                step="0.01"
                value={minutes}
                onChange={(event) => setMinutes(event.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1">
              <Label htmlFor="screen-on">On</Label>
              <Input
                id="screen-on"
                type="date"
                value={occurredOn}
                onChange={(event) => setOccurredOn(event.target.value)}
              />
            </div>
          </>
        )}
        <div className="flex items-end">
          <Button type="submit" disabled={busy || app === ''}>
            Log
          </Button>
        </div>
        {message !== null && (
          <p className="text-sm text-bad sm:col-span-2 lg:col-span-4" role="alert">
            {message}
          </p>
        )}
      </form>
    </Card>
  )
}

function ManagePanel({
  apps,
  categories,
  devices,
  onChanged,
}: {
  apps: ScreenApp[]
  categories: ScreenCategory[]
  devices: ScreenDevice[]
  onChanged: () => Promise<void>
}) {
  const [open, setOpen] = useState(false)
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">Manage</CardTitle>
        <button
          type="button"
          className="text-xs font-medium text-screen hover:underline"
          onClick={() => setOpen((value) => !value)}
        >
          {open ? 'Hide' : 'Show'}
        </button>
      </CardHeader>
      <p className="text-sm text-muted">
        {apps.length} apps · {categories.length} categories · {devices.length} devices
      </p>
      {open && (
        <div className="mt-4 grid gap-4 lg:grid-cols-3">
          <TaxonomyForm
            title="Category"
            onCreate={async (slug, extra) => {
              await createScreenCategory({
                slug,
                judgment: (extra || 'waste') as ScreenJudgment,
              })
              await onChanged()
            }}
            extraLabel="Judgment"
            extraOptions={['useful', 'waste', 'neutral']}
            rows={categories.map((row) => `${row.name} · ${JUDGMENT_LABEL[row.judgment]}`)}
          />
          <TaxonomyForm
            title="App"
            onCreate={async (slug, extra) => {
              await createScreenApp({ slug, category: extra })
              await onChanged()
            }}
            extraLabel="Category"
            extraOptions={categories.map((row) => row.slug)}
            rows={apps.map((row) => `${row.name} · ${row.category}`)}
          />
          <TaxonomyForm
            title="Device"
            onCreate={async (slug) => {
              await createScreenDevice({ slug })
              await onChanged()
            }}
            rows={devices.map((row) => row.name)}
          />
        </div>
      )}
    </Card>
  )
}

function TaxonomyForm({
  title,
  onCreate,
  extraLabel,
  extraOptions,
  rows,
}: {
  title: string
  onCreate: (slug: string, extra: string) => Promise<void>
  extraLabel?: string
  extraOptions?: string[]
  rows: string[]
}) {
  const [slug, setSlug] = useState('')
  const extraDefault = extraOptions?.[0] ?? ''
  const [extra, setExtra] = useState(extraDefault)
  const extraValue = extraOptions === undefined ? extra : extra || extraDefault
  const [message, setMessage] = useState<string | null>(null)
  const canSubmit = isValidSlug(slug) && (extraOptions === undefined || extraValue !== '')

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setMessage(null)
    try {
      await onCreate(slug, extraValue)
      setSlug('')
    } catch (caught: unknown) {
      setMessage(
        caught instanceof ApiError ? caught.message : `Could not create ${title.toLowerCase()}`,
      )
    }
  }

  return (
    <div>
      <p className="mb-2 text-sm font-medium">{title}</p>
      <ul className="mb-3 max-h-28 overflow-auto text-xs text-muted">
        {rows.map((row) => (
          <li key={row}>{row}</li>
        ))}
      </ul>
      <form className="flex flex-col gap-2" onSubmit={onSubmit}>
        <Input
          value={slug}
          onChange={(event) => setSlug(event.target.value)}
          placeholder="slug"
          aria-label={`${title} slug`}
        />
        {extraOptions !== undefined && extraLabel !== undefined && (
          <Select
            value={extraValue}
            onChange={(event) => setExtra(event.target.value)}
            aria-label={extraLabel}
          >
            {extraOptions.map((option) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </Select>
        )}
        <Button type="submit" size="sm" disabled={!canSubmit}>
          Add {title.toLowerCase()}
        </Button>
        {message !== null && (
          <p className="text-xs text-bad" role="alert">
            {message}
          </p>
        )}
      </form>
    </div>
  )
}
