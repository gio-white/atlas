import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import { PaceBadge } from '@/components/PaceBadge'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ApiError, getGoalProgress, type GoalProgress } from '@/lib/api'
import { useAsOf } from '@/lib/asOf'
import { formatPercent } from '@/lib/format'

export function GoalPage() {
  const { slug } = useParams()
  const asOf = useAsOf()
  const [report, setReport] = useState<GoalProgress | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (slug === undefined) return
    let cancelled = false
    setError(null)
    getGoalProgress(slug, asOf)
      .then((data) => {
        if (!cancelled) setReport(data)
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setError(caught instanceof ApiError ? caught.message : 'Could not load goal')
          setReport(null)
        }
      })
    return () => {
      cancelled = true
    }
  }, [slug, asOf])

  if (error !== null) return <p className="text-sm text-bad">{error}</p>
  if (report === null) return <p className="text-sm text-muted">Loading…</p>

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>{report.name}</CardTitle>
          <CardDescription className="mt-1 font-mono">
            {report.kind}
            {report.metric_slug !== null ? ` · ${report.metric_slug}` : ''} · due {report.due_on}
          </CardDescription>
        </div>
        <PaceBadge pace={report.pace} />
      </CardHeader>
      <dl className="grid gap-4 sm:grid-cols-3">
        <div>
          <dt className="text-xs text-muted">Progress</dt>
          <dd className="mt-1 font-mono text-xl">{formatPercent(report.fraction)}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted">Current</dt>
          <dd className="mt-1 font-mono text-xl">
            {report.current === null ? '—' : report.current}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-muted">Target</dt>
          <dd className="mt-1 font-mono text-xl">
            {report.target_value === null ? '—' : report.target_value}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-muted">Status</dt>
          <dd className="mt-1 capitalize">{report.status}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted">Window</dt>
          <dd className="mt-1 font-mono text-sm">
            {report.start_on} → {report.due_on}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-muted">Target met</dt>
          <dd className="mt-1">{report.target_met ? 'yes' : 'no'}</dd>
        </div>
      </dl>
    </Card>
  )
}
