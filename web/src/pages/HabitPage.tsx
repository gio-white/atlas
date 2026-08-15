import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'

import { HomeLink, PageLoading, PageUnavailable } from '@/components/PageState'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { WeekGrid } from '@/components/WeekGrid'
import {
  ApiError,
  getHabitStatus,
  getHabitsCalendar,
  type HabitStatus,
  type HabitsCalendar,
  listMetrics,
  logEntry,
  type Metric,
  type Period,
} from '@/lib/api'
import { useAsOf, useShell } from '@/lib/asOf'
import { formatComparator, formatPercent } from '@/lib/format'
import { HABIT_PERIOD_META, parseHabitPeriod } from '@/lib/habitsSummary'
import { cn } from '@/lib/utils'

const VIEW_PERIODS: { id: Period; label: string }[] = [
  { id: 'day', label: 'Day' },
  { id: 'week', label: 'Week' },
  { id: 'month', label: 'Month' },
]

const CALENDAR_TITLE: Record<Period, string> = {
  day: 'This day',
  week: 'This week',
  month: 'This month',
}

export function HabitPage() {
  const { slug } = useParams()
  const asOf = useAsOf()
  const { openLog } = useShell()
  const [params, setParams] = useSearchParams()
  const search = params.toString()
  const period = parseHabitPeriod(params.get('period'))
  const [status, setStatus] = useState<HabitStatus | null>(null)
  const [calendar, setCalendar] = useState<HabitsCalendar | null>(null)
  const [metrics, setMetrics] = useState<Metric[]>([])
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  const refresh = useCallback(async () => {
    if (slug === undefined) return
    const [nextStatus, nextCalendar, nextMetrics] = await Promise.all([
      getHabitStatus(slug, asOf),
      getHabitsCalendar(period, asOf),
      listMetrics(),
    ])
    setStatus(nextStatus)
    setCalendar(nextCalendar)
    setMetrics(nextMetrics)
  }, [slug, asOf, period])

  useEffect(() => {
    let cancelled = false
    setError(null)
    refresh().catch((caught: unknown) => {
      if (!cancelled) {
        setError(caught instanceof ApiError ? caught.message : 'Could not load habit')
        setStatus(null)
        setCalendar(null)
      }
    })
    return () => {
      cancelled = true
    }
  }, [refresh])

  const metric = useMemo(
    () => metrics.find((item) => item.slug === status?.metric_slug) ?? null,
    [metrics, status],
  )
  const calendarHabit = useMemo(
    () => calendar?.habits.find((habit) => habit.slug === slug) ?? null,
    [calendar, slug],
  )

  function setPeriod(next: Period) {
    const copy = new URLSearchParams(params)
    if (next === 'week') copy.delete('period')
    else copy.set('period', next)
    setParams(copy, { replace: true })
  }

  const weekBoardSearch = useMemo(() => {
    const copy = new URLSearchParams(params)
    copy.set('period', 'week')
    return copy.toString()
  }, [params])

  async function onLog() {
    if (status === null || status.satisfied) return
    if (metric?.value_type !== 'bool') {
      openLog()
      return
    }
    setPending(true)
    try {
      await logEntry({ metric: status.metric_slug, occurred_on: asOf })
      await refresh()
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Could not log')
    } finally {
      setPending(false)
    }
  }

  if (error !== null) {
    return <PageUnavailable title={slug ?? 'Habit'} message={error} />
  }
  if (status === null) return <PageLoading />

  const isBool = metric?.value_type === 'bool'
  const logLabel = status.satisfied ? 'Done' : isBool ? 'Mark done' : 'Log value'

  return (
    <div className="flex flex-col gap-3">
      <HomeLink />
      <Link to={{ pathname: '/habit', search }} className="text-sm text-muted hover:text-ink">
        Habits
      </Link>
      <Card>
        <CardHeader>
          <div>
            <CardTitle>{status.name}</CardTitle>
            <CardDescription className="mt-1 font-mono">
              {status.metric_slug} · {formatComparator(status.comparator)} {status.target_value}
            </CardDescription>
          </div>
          <div className="flex flex-wrap justify-end gap-1">
            <Badge>{HABIT_PERIOD_META[status.period].label}</Badge>
            <Badge tone={status.satisfied ? 'good' : status.scheduled ? 'warn' : 'default'}>
              {status.satisfied ? 'done' : status.scheduled ? 'open' : 'off'}
            </Badge>
          </div>
        </CardHeader>
        <dl className="grid gap-4 sm:grid-cols-3">
          <Stat label="Current streak" value={String(status.current_streak)} />
          <Stat label="Longest streak" value={String(status.longest_streak)} />
          <Stat label="Adherence" value={formatPercent(status.adherence)} />
          <Stat
            label="This bucket"
            value={status.current_value === null ? '—' : String(status.current_value)}
          />
          <Stat label="Scheduled" value={status.scheduled ? 'yes' : 'no'} />
          <Stat label="As of" value={status.as_of} />
        </dl>
        {status.scheduled && (
          <Button
            type="button"
            className="mt-4"
            disabled={pending || status.satisfied}
            onClick={() => void onLog()}
          >
            {logLabel}
          </Button>
        )}
      </Card>
      {calendarHabit !== null && calendar !== null && (
        <Card>
          <CardHeader>
            <div>
              <CardTitle>{CALENDAR_TITLE[period]}</CardTitle>
              <CardDescription className="mt-1">
                {calendar.range_start} → {calendar.range_end}. Displayed from the habit calendar.
                Streaks are not recomputed here.
              </CardDescription>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <div className="flex rounded-full border border-line bg-surface p-1" role="tablist">
                {VIEW_PERIODS.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    role="tab"
                    aria-selected={period === item.id}
                    className={cn(
                      'rounded-full px-3 py-1 text-sm motion-safe:transition-colors',
                      period === item.id ? 'bg-goal/20 text-ink' : 'text-muted hover:text-ink',
                    )}
                    onClick={() => setPeriod(item.id)}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
              <Link
                to={{ pathname: '/habit', search: weekBoardSearch }}
                className="text-xs font-medium hover:underline"
              >
                Full grid
              </Link>
            </div>
          </CardHeader>
          <WeekGrid habits={[calendarHabit]} search={search} compact={period === 'month'} />
        </Card>
      )}
    </div>
  )
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="mt-1 font-mono text-xl">{value}</dd>
    </div>
  )
}
