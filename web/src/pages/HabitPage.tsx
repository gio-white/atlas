import { useCallback, useEffect, useMemo, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'

import { HomeLink, PageLoading, PageUnavailable } from '@/components/PageState'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { DayDot } from '@/components/WeekGrid'
import {
  ApiError,
  getHabitStatus,
  getWeek,
  type HabitStatus,
  listMetrics,
  logEntry,
  type Metric,
  type WeekHabit,
} from '@/lib/api'
import { useAsOf, useShell } from '@/lib/asOf'
import { weekdayLabel } from '@/lib/dates'
import { formatComparator, formatPercent } from '@/lib/format'

export function HabitPage() {
  const { slug } = useParams()
  const asOf = useAsOf()
  const { openLog } = useShell()
  const [params] = useSearchParams()
  const search = params.toString()
  const [status, setStatus] = useState<HabitStatus | null>(null)
  const [weekHabit, setWeekHabit] = useState<WeekHabit | null>(null)
  const [metrics, setMetrics] = useState<Metric[]>([])
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  const refresh = useCallback(async () => {
    if (slug === undefined) return
    const [nextStatus, week, nextMetrics] = await Promise.all([
      getHabitStatus(slug, asOf),
      getWeek(asOf),
      listMetrics(),
    ])
    setStatus(nextStatus)
    setWeekHabit(week.habits.find((habit) => habit.slug === slug) ?? null)
    setMetrics(nextMetrics)
  }, [slug, asOf])

  useEffect(() => {
    let cancelled = false
    setError(null)
    refresh().catch((caught: unknown) => {
      if (!cancelled) {
        setError(caught instanceof ApiError ? caught.message : 'Could not load habit')
        setStatus(null)
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
              {status.metric_slug} · {formatComparator(status.comparator)} {status.target_value} /{' '}
              {status.period}
            </CardDescription>
          </div>
          <Badge tone={status.satisfied ? 'good' : status.scheduled ? 'warn' : 'default'}>
            {status.satisfied ? 'done' : status.scheduled ? 'open' : 'off'}
          </Badge>
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
        {status.scheduled && !status.satisfied && (
          <Button type="button" className="mt-4" disabled={pending} onClick={() => void onLog()}>
            Log {status.metric_slug}
          </Button>
        )}
      </Card>
      {weekHabit !== null && (
        <Card>
          <CardHeader>
            <div>
              <CardTitle>This week</CardTitle>
              <CardDescription className="mt-1">
                Displayed from the week view. Streaks are not recomputed here.
              </CardDescription>
            </div>
            <Link
              to={{ pathname: '/week', search }}
              className="text-xs font-medium hover:underline"
            >
              Full grid
            </Link>
          </CardHeader>
          <ol className="flex flex-wrap gap-2">
            {weekHabit.days.map((cell) => (
              <li key={cell.day} className="flex flex-col items-center gap-1">
                <span className="font-mono text-[10px] text-muted">{weekdayLabel(cell.day)}</span>
                <DayDot cell={cell} />
              </li>
            ))}
          </ol>
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
