import { ChevronLeft, ChevronRight } from 'lucide-react'
import { type ReactNode, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { BlockEmpty, HomeBlock } from '@/components/home/HomeBlock'
import { PageError, PageLoading } from '@/components/PageState'
import { Button } from '@/components/ui/button'
import { ApiError, getThisWeek, type ThisWeek, type WeekNumbers } from '@/lib/api'
import { useShell } from '@/lib/asOf'
import { formatMinutes, formatPercent } from '@/lib/format'
import { formatClock } from '@/lib/sleep'
import {
  clockChange,
  countChange,
  minutesChange,
  shareChange,
  weekRangeLine,
  weekSteps,
  weekTitle,
} from '@/lib/thisWeek'
import { todayIso } from '@/lib/utils'

/**
 * Stats → This week: one Monday–Sunday week in five blocks, each compared with the same days of
 * the week before. The week is the one holding the shell's `?on=` date, counted up to that day.
 */
export function ThisWeekPage() {
  const { asOf } = useShell()
  const [params, setParams] = useSearchParams()
  const [week, setWeek] = useState<ThisWeek | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    getThisWeek(asOf)
      .then((next) => {
        if (!cancelled) {
          setWeek(next)
          setError(null)
        }
      })
      .catch((caught: unknown) => {
        if (!cancelled)
          setError(caught instanceof ApiError ? caught.message : 'Couldn’t load this week.')
      })
    return () => {
      cancelled = true
    }
  }, [asOf])

  if (error !== null) return <PageError message={error} />
  if (week === null) return <PageLoading />

  const today = todayIso()
  const steps = weekSteps(week.week_start, today)
  const search = params.toString()

  function goTo(on: string | null) {
    const next = new URLSearchParams(params)
    if (on === null) next.delete('on')
    else next.set('on', on)
    setParams(next)
  }

  const { current: now, previous: before } = week
  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <header className="flex flex-col gap-0.5">
          <h2 className="text-xl font-semibold tracking-tight text-ink">
            {weekTitle(week.week_start, today)}
          </h2>
          <p className="text-sm text-muted">
            {weekRangeLine(week.week_start, week.as_of, week.complete)}
          </p>
        </header>
        <nav aria-label="Week" className="flex items-center gap-1">
          <Button
            variant="outline"
            size="icon"
            aria-label="Previous week"
            onClick={() => goTo(steps.previous)}
          >
            <ChevronLeft className="size-4" aria-hidden />
          </Button>
          <Button
            variant="outline"
            size="icon"
            aria-label="Next week"
            disabled={steps.next === undefined}
            onClick={() => steps.next !== undefined && goTo(steps.next)}
          >
            <ChevronRight className="size-4" aria-hidden />
          </Button>
        </nav>
      </div>
      {!week.complete && (
        <p className="-mt-3 text-xs text-muted">Compared with the same days last week.</p>
      )}

      {/* Two columns that stack on their own from 1024px; below, one list in block order. */}
      <div className="flex flex-col gap-5 lg:grid lg:grid-cols-2 lg:items-start">
        <div className="contents lg:flex lg:flex-col lg:gap-5">
          <HomeBlock
            id="week-quests"
            title="Quests"
            to="/quests"
            search={search}
            className="order-1 lg:order-none"
          >
            <Numbers>
              <NumberRow
                label="Sessions kept"
                value={
                  now.sessions_total === 0 ? '—' : `${now.sessions_kept} of ${now.sessions_total}`
                }
                change={
                  before.sessions_total === 0
                    ? null
                    : `Last week ${before.sessions_kept} of ${before.sessions_total}`
                }
              />
              <NumberRow
                label="Tasks completed"
                value={String(now.tasks_completed)}
                change={countChange(now.tasks_completed, before.tasks_completed)}
              />
              <NumberRow
                label="Milestones completed"
                value={String(now.milestones_completed)}
                change={countChange(now.milestones_completed, before.milestones_completed)}
              />
            </Numbers>
          </HomeBlock>

          <HomeBlock
            id="week-sleep"
            title="Sleep"
            to="/stats/sleep"
            search={search}
            className="order-3 lg:order-none"
          >
            {now.sleep_nights === 0 ? (
              <BlockEmpty>No sleep data this week.</BlockEmpty>
            ) : (
              <Numbers>
                <NumberRow
                  label="Time asleep, average"
                  value={formatMinutes(now.sleep_average_minutes)}
                  change={minutesChange(now.sleep_average_minutes, before.sleep_average_minutes)}
                />
                <NumberRow
                  label="Bedtime, average"
                  value={formatClock(now.sleep_average_bedtime)}
                  change={clockChange(now.sleep_average_bedtime, before.sleep_average_bedtime)}
                />
                <NumberRow
                  label="Wake time, average"
                  value={formatClock(now.sleep_average_wake)}
                  change={clockChange(now.sleep_average_wake, before.sleep_average_wake)}
                />
                <NumberRow label="Missing nights" value={String(now.sleep_missing_nights)} />
              </Numbers>
            )}
          </HomeBlock>

          <HomeBlock
            id="week-library"
            title="Library"
            to="/library"
            search={search}
            className="order-5 lg:order-none"
          >
            <Numbers>
              <NumberRow
                label="Titles finished"
                value={String(now.titles_finished)}
                change={countChange(now.titles_finished, before.titles_finished)}
              />
            </Numbers>
          </HomeBlock>
        </div>
        <div className="contents lg:flex lg:flex-col lg:gap-5">
          <HomeBlock
            id="week-habits"
            title="Habits"
            to="/habits"
            search={search}
            className="order-2 lg:order-none"
          >
            <Numbers>
              <NumberRow
                label="Habits kept"
                value={formatPercent(now.habits_kept_share)}
                change={shareChange(now.habits_kept_share, before.habits_kept_share)}
              />
            </Numbers>
            {week.habits.length === 0 ? (
              <BlockEmpty>No habits yet.</BlockEmpty>
            ) : (
              <ul className="flex flex-col divide-y divide-line border-t border-line text-sm">
                {week.habits.map((row) => (
                  <li key={row.slug} className="py-2">
                    <span className="min-w-0 truncate text-ink">{row.name}</span>
                  </li>
                ))}
              </ul>
            )}
          </HomeBlock>

          <HomeBlock
            id="week-screen"
            title="Screen time"
            to="/stats/screen-time"
            search={search}
            className="order-4 lg:order-none"
          >
            {now.screen_total === null ? (
              <BlockEmpty>No screen time data this week.</BlockEmpty>
            ) : (
              <>
                <Numbers>
                  <NumberRow
                    label="Total"
                    value={formatMinutes(now.screen_total)}
                    change={minutesChange(now.screen_total, before.screen_total)}
                  />
                  <NumberRow
                    label="Daily average"
                    value={formatMinutes(now.screen_daily_average)}
                    change={minutesChange(now.screen_daily_average, before.screen_daily_average)}
                  />
                  <NumberRow
                    label="Score"
                    value={now.screen_score === null ? '—' : String(now.screen_score)}
                    change={countChange(now.screen_score, before.screen_score)}
                  />
                </Numbers>
                <ScreenSplit numbers={now} />
              </>
            )}
          </HomeBlock>
        </div>
      </div>
    </div>
  )
}

function Numbers({ children }: { children: ReactNode }) {
  return <dl className="flex flex-col gap-2.5 text-sm">{children}</dl>
}

function NumberRow({
  label,
  value,
  change = null,
}: {
  label: string
  value: string
  change?: string | null
}) {
  return (
    <div className="grid grid-cols-[minmax(0,1fr)_auto] items-baseline gap-x-4">
      <dt className="text-muted">{label}</dt>
      <dd className="text-right font-semibold tabular-nums text-ink">{value}</dd>
      {change !== null && (
        <dd className="col-span-2 text-right text-xs text-muted sm:col-span-1 sm:col-start-2">
          {change}
        </dd>
      )}
    </div>
  )
}

const SPLIT = [
  { key: 'screen_good', label: 'Good', bar: 'bg-data-good' },
  { key: 'screen_neutral', label: 'Neutral', bar: 'bg-data-neutral' },
  { key: 'screen_bad', label: 'Bad', bar: 'bg-data-bad' },
] as const

/** The week's Good / Neutral / Bad minutes as one bar with a legend. */
function ScreenSplit({ numbers }: { numbers: WeekNumbers }) {
  const parts = SPLIT.map((part) => ({ ...part, minutes: numbers[part.key] ?? 0 }))
  const total = parts.reduce((sum, part) => sum + part.minutes, 0)
  if (total <= 0) return null
  return (
    <div className="flex flex-col gap-2">
      <div className="flex h-2 overflow-hidden rounded-full bg-raised" aria-hidden>
        {parts.map((part) => (
          <div
            key={part.key}
            className={part.bar}
            style={{ width: `${(part.minutes / total) * 100}%` }}
          />
        ))}
      </div>
      <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted">
        {parts.map((part) => (
          <li key={part.key} className="inline-flex items-center gap-1.5">
            <span className={`size-2 rounded-full ${part.bar}`} aria-hidden />
            {part.label} {formatMinutes(part.minutes)}
          </li>
        ))}
      </ul>
    </div>
  )
}
