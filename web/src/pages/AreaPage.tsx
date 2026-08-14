import { useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'

import { PaceBadge } from '@/components/PaceBadge'
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

  if (error !== null) return <p className="text-sm text-bad">{error}</p>
  if (view === null) return <p className="text-sm text-muted">Loading…</p>

  const search = params.toString()

  return (
    <div className="flex flex-col gap-6">
      <header>
        <h1 className="font-serif text-2xl tracking-tight">{view.name}</h1>
        {view.description !== null && <p className="mt-1 text-sm text-muted">{view.description}</p>}
      </header>
      <section>
        <h2 className="mb-3 font-serif text-lg">Metrics</h2>
        {view.metrics.length === 0 ? (
          <p className="text-sm text-muted">No metrics.</p>
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
        <h2 className="mb-3 font-serif text-lg">Habits</h2>
        {view.habits.length === 0 ? (
          <p className="text-sm text-muted">No habits.</p>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {view.habits.map((habit) => (
              <Link
                key={habit.slug}
                to={{ pathname: `/habit/${habit.slug}`, search }}
                className="rounded-xl border border-line bg-surface p-4 hover:bg-raised"
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
        <h2 className="mb-3 font-serif text-lg">Goals</h2>
        {view.goals.length === 0 ? (
          <p className="text-sm text-muted">No goals.</p>
        ) : (
          <div className="flex flex-col gap-3">
            {view.goals.map((goal) => (
              <Link
                key={goal.slug}
                to={{ pathname: `/goal/${goal.slug}`, search }}
                className="flex items-center justify-between rounded-xl border border-line bg-surface p-4 hover:bg-raised"
              >
                <div>
                  <p className="font-medium">{goal.name}</p>
                  <p className="font-mono text-xs text-muted">{formatPercent(goal.fraction)}</p>
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
