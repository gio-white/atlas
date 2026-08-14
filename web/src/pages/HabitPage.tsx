import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import { HomeLink, PageLoading, PageUnavailable } from '@/components/PageState'
import { Badge } from '@/components/ui/badge'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ApiError, getHabitStatus, type HabitStatus } from '@/lib/api'
import { useAsOf } from '@/lib/asOf'
import { formatComparator, formatPercent } from '@/lib/format'

export function HabitPage() {
  const { slug } = useParams()
  const asOf = useAsOf()
  const [status, setStatus] = useState<HabitStatus | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (slug === undefined) return
    let cancelled = false
    setError(null)
    getHabitStatus(slug, asOf)
      .then((data) => {
        if (!cancelled) setStatus(data)
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setError(caught instanceof ApiError ? caught.message : 'Could not load habit')
          setStatus(null)
        }
      })
    return () => {
      cancelled = true
    }
  }, [slug, asOf])

  if (error !== null) {
    return <PageUnavailable title={slug ?? 'Habit'} message={error} />
  }
  if (status === null) return <PageLoading />

  return (
    <div className="flex flex-col gap-3">
      <HomeLink />
      <Card>
        <CardHeader>
          <div>
            <CardTitle>{status.name}</CardTitle>
            <CardDescription className="mt-1 font-mono">
              {status.metric_slug} · {formatComparator(status.comparator)} {status.target_value} /{' '}
              {status.period}
            </CardDescription>
          </div>
          <Badge tone={status.satisfied ? 'good' : 'warn'}>
            {status.satisfied ? 'done' : 'open'}
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
      </Card>
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
