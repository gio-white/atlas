import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { PaceBadge } from '@/components/PaceBadge'
import { ApiError, getGoalProgress, listGoals, type GoalProgress } from '@/lib/api'
import { useAsOf } from '@/lib/asOf'
import { formatPercent } from '@/lib/format'

export function GoalsPage() {
  const asOf = useAsOf()
  const [params] = useSearchParams()
  const [reports, setReports] = useState<GoalProgress[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setError(null)
    listGoals()
      .then((goals) => Promise.all(goals.map((goal) => getGoalProgress(goal.slug, asOf))))
      .then((data) => {
        if (!cancelled) setReports(data)
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setError(caught instanceof ApiError ? caught.message : 'Could not load goals')
          setReports(null)
        }
      })
    return () => {
      cancelled = true
    }
  }, [asOf])

  if (error !== null) return <p className="text-sm text-bad">{error}</p>
  if (reports === null) return <p className="text-sm text-muted">Loading…</p>

  return (
    <div className="flex flex-col gap-4">
      <h1 className="font-serif text-2xl tracking-tight">Goals</h1>
      {reports.length === 0 ? (
        <p className="text-sm text-muted">No goals yet.</p>
      ) : (
        <ul className="flex flex-col gap-3">
          {reports.map((goal) => (
            <li key={goal.slug}>
              <Link
                to={{ pathname: `/goal/${goal.slug}`, search: params.toString() }}
                className="flex items-center justify-between rounded-xl border border-line bg-surface p-4 hover:bg-raised"
              >
                <div>
                  <p className="font-medium">{goal.name}</p>
                  <p className="font-mono text-xs text-muted">
                    {formatPercent(goal.fraction)} · {goal.status} · due {goal.due_on}
                  </p>
                </div>
                <PaceBadge pace={goal.pace} />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
