import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { PaceBadge } from '@/components/PaceBadge'
import { EmptyState, PageError, PageHeader, PageLoading, ProgressBar } from '@/components/PageState'
import { ApiError, type GoalProgress, getGoalProgress, listGoals } from '@/lib/api'
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

  if (error !== null) return <PageError message={error} />
  if (reports === null) return <PageLoading />

  return (
    <div className="flex flex-col gap-4">
      <PageHeader title="Goals" description="Outcomes by a date, with pace computed on read." />
      {reports.length === 0 ? (
        <EmptyState
          title="No goals yet"
          hint="Define an outcome in Catalog."
          actionLabel="Open catalog"
          actionTo="/catalog"
        />
      ) : (
        <ul className="flex flex-col gap-3">
          {reports.map((goal) => (
            <li key={goal.slug}>
              <Link
                to={{ pathname: `/goal/${goal.slug}`, search: params.toString() }}
                className="flex items-center justify-between gap-4 rounded-2xl border border-line bg-surface p-4 shadow-[var(--shadow-card)] motion-safe:transition-colors motion-safe:duration-200 hover:bg-raised"
              >
                <div className="min-w-0 flex-1">
                  <p className="font-medium">{goal.name}</p>
                  <p className="font-mono text-xs text-muted">
                    {formatPercent(goal.fraction)} · {goal.status} · due {goal.due_on}
                  </p>
                  <div className="mt-2">
                    <ProgressBar value={goal.fraction} />
                  </div>
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
