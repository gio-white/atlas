import { useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'

import { PaceBadge } from '@/components/PaceBadge'
import {
  EmptyState,
  PageHeader,
  PageLoading,
  PageUnavailable,
  ProgressBar,
} from '@/components/PageState'
import { Badge } from '@/components/ui/badge'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ApiError, type AreaView, getAreaView } from '@/lib/api'
import { useAsOf } from '@/lib/asOf'
import { formatComparator, formatPercent } from '@/lib/format'

export function AreaPage() {
  const { slug } = useParams()
  const asOf = useAsOf()
  const [params] = useSearchParams()
  const [view, setView] = useState<AreaView | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (slug === undefined) return
    let cancelled = false
    setError(null)
    getAreaView(slug, asOf)
      .then((data) => {
        if (!cancelled) setView(data)
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setError(caught instanceof ApiError ? caught.message : 'Could not load area')
          setView(null)
        }
      })
    return () => {
      cancelled = true
    }
  }, [slug, asOf])

  if (error !== null) {
    return <PageUnavailable title={slug ?? 'Area'} message={error} />
  }
  if (view === null) return <PageLoading />

  const search = params.toString()

  return (
    <div className="flex flex-col gap-5">
      <PageHeader title={view.name} description={view.description ?? undefined} homeLink />
      <section>
        <h2 className="mb-3 font-serif text-lg font-medium tracking-tight">Metrics</h2>
        {view.metrics.length === 0 ? (
          <EmptyState
            title="No metrics"
            hint="Define what you measure in Catalog."
            actionLabel="Open catalog"
            actionTo="/catalog"
          />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {view.metrics.map((metric) => (
              <Card key={metric.slug}>
                <CardHeader>
                  <div>
                    <CardTitle className="text-base">{metric.name}</CardTitle>
                    <CardDescription className="mt-1 font-mono text-xs">
                      {metric.slug}
                      {metric.unit !== null ? ` · ${metric.unit}` : ''}
                    </CardDescription>
                  </div>
                </CardHeader>
                <p className="font-mono text-2xl">
                  {metric.latest_value === null ? '—' : metric.latest_value}
                </p>
                <p className="mt-1 text-xs text-muted">{metric.latest_on ?? 'no readings'}</p>
              </Card>
            ))}
          </div>
        )}
      </section>
      <section>
        <h2 className="mb-3 font-serif text-lg font-medium tracking-tight">Habits</h2>
        {view.habits.length === 0 ? (
          <EmptyState title="No habits" />
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {view.habits.map((habit) => (
              <Link
                key={habit.slug}
                to={{ pathname: `/habit/${habit.slug}`, search }}
                className="rounded-2xl border border-line bg-surface p-4 shadow-[var(--shadow-card)] motion-safe:transition-colors motion-safe:duration-200 hover:bg-raised"
              >
                <div className="flex items-start justify-between gap-2">
                  <p className="font-medium">{habit.name}</p>
                  <Badge tone={habit.satisfied ? 'good' : 'warn'}>
                    {habit.satisfied ? 'done' : 'open'}
                  </Badge>
                </div>
                <p className="mt-2 font-mono text-xs text-muted">
                  {formatComparator(habit.comparator)} {habit.target_value} · streak{' '}
                  {habit.current_streak}
                </p>
              </Link>
            ))}
          </div>
        )}
      </section>
      <section>
        <h2 className="mb-3 font-serif text-lg font-medium tracking-tight">Goals</h2>
        {view.goals.length === 0 ? (
          <EmptyState title="No goals" />
        ) : (
          <div className="flex flex-col gap-3">
            {view.goals.map((goal) => (
              <Link
                key={goal.slug}
                to={{ pathname: `/goal/${goal.slug}`, search }}
                className="flex items-center justify-between rounded-2xl border border-line bg-surface p-4 shadow-[var(--shadow-card)] motion-safe:transition-colors motion-safe:duration-200 hover:bg-raised"
              >
                <div>
                  <p className="font-medium">{goal.name}</p>
                  <p className="font-mono text-xs text-muted">{formatPercent(goal.fraction)}</p>
                  <div className="mt-2 w-40">
                    <ProgressBar value={goal.fraction} />
                  </div>
                </div>
                <PaceBadge pace={goal.pace} />
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  )
}
