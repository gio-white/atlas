import { useCallback, useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'

import { PaceBadge } from '@/components/PaceBadge'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  ApiError,
  type GoalDetail,
  type GoalProgress,
  getGoal,
  getGoalProgress,
  toggleMilestone,
} from '@/lib/api'
import { useAsOf } from '@/lib/asOf'
import { formatPercent } from '@/lib/format'

export function GoalPage() {
  const { slug } = useParams()
  const asOf = useAsOf()
  const [report, setReport] = useState<GoalProgress | null>(null)
  const [detail, setDetail] = useState<GoalDetail | null>(null)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    if (slug === undefined) return
    const [progress, goal] = await Promise.all([getGoalProgress(slug, asOf), getGoal(slug)])
    setReport(progress)
    setDetail(goal)
  }, [slug, asOf])

  useEffect(() => {
    let cancelled = false
    setError(null)
    refresh().catch((caught: unknown) => {
      if (!cancelled) {
        setError(caught instanceof ApiError ? caught.message : 'Could not load goal')
        setReport(null)
        setDetail(null)
      }
    })
    return () => {
      cancelled = true
    }
  }, [refresh])

  if (error !== null) return <p className="text-sm text-bad">{error}</p>
  if (report === null || detail === null) return <p className="text-sm text-muted">Loading…</p>

  return (
    <div className="flex flex-col gap-6">
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
      {detail.milestones.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Milestones</CardTitle>
          </CardHeader>
          <ul className="flex flex-col gap-2">
            {detail.milestones.map((milestone) => (
              <li key={milestone.name}>
                <label className="flex items-center gap-3 text-sm">
                  <input
                    type="checkbox"
                    checked={milestone.done_at !== null}
                    onChange={() => {
                      toggleMilestone(detail.slug, milestone.name, milestone.done_at === null)
                        .then(refresh)
                        .catch((caught: unknown) => {
                          setError(caught instanceof ApiError ? caught.message : 'Could not toggle')
                        })
                    }}
                  />
                  <span>{milestone.name}</span>
                  {milestone.due_on !== null && (
                    <span className="font-mono text-xs text-muted">{milestone.due_on}</span>
                  )}
                </label>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  )
}
