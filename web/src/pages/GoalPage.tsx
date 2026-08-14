import { useCallback, useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'

import { PaceBadge } from '@/components/PaceBadge'
import { PageError, PageLoading, ProgressBar } from '@/components/PageState'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import {
  ApiError,
  type Goal,
  type GoalDetail,
  type GoalProgress,
  getGoal,
  getGoalProgress,
  listGoals,
  listTasks,
  type TaskItem,
  toggleMilestone,
  updateTask,
} from '@/lib/api'
import { useAsOf } from '@/lib/asOf'
import { formatPercent } from '@/lib/format'
import { HORIZON_META } from '@/lib/horizons'

export function GoalPage() {
  const { slug } = useParams()
  const asOf = useAsOf()
  const [params] = useSearchParams()
  const search = params.toString()
  const [report, setReport] = useState<GoalProgress | null>(null)
  const [detail, setDetail] = useState<GoalDetail | null>(null)
  const [children, setChildren] = useState<Goal[]>([])
  const [tasks, setTasks] = useState<TaskItem[]>([])
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    if (slug === undefined) return
    const [progress, goal, childRows, taskRows] = await Promise.all([
      getGoalProgress(slug, asOf),
      getGoal(slug),
      listGoals({ parent: slug }),
      listTasks({ goal: slug, include_done: true }),
    ])
    setReport(progress)
    setDetail(goal)
    setChildren(childRows)
    setTasks(taskRows)
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

  if (error !== null) return <PageError message={error} />
  if (report === null || detail === null) return <PageLoading />

  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <div>
            <p className="font-mono text-xs text-muted">
              {HORIZON_META[report.horizon].label}
              {report.parent !== null ? (
                <>
                  {' '}
                  · parent{' '}
                  <Link className="underline" to={{ pathname: `/goal/${report.parent}`, search }}>
                    {report.parent}
                  </Link>
                </>
              ) : null}
            </p>
            <CardTitle>{report.name}</CardTitle>
            <CardDescription className="mt-1">
              {report.description ?? (
                <span className="font-mono">
                  {report.kind}
                  {report.metric_slug !== null ? ` · ${report.metric_slug}` : ''} · due{' '}
                  {report.due_on}
                </span>
              )}
            </CardDescription>
          </div>
          <PaceBadge pace={report.pace} />
        </CardHeader>
        <dl className="grid gap-4 sm:grid-cols-3">
          <div>
            <dt className="text-xs text-muted">Progress</dt>
            <dd className="mt-1 font-mono text-xl">{formatPercent(report.fraction)}</dd>
            <div className="mt-2">
              <ProgressBar value={report.fraction} />
            </div>
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
                <label className="flex min-h-11 cursor-pointer items-center gap-3 text-sm">
                  <input
                    type="checkbox"
                    className="size-4 accent-accent"
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
      {children.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Next horizon</CardTitle>
          </CardHeader>
          <ul className="flex flex-col gap-2">
            {children.map((child) => (
              <li key={child.slug}>
                <Link
                  to={{ pathname: `/goal/${child.slug}`, search }}
                  className="flex min-h-11 items-center justify-between rounded-xl px-2 text-sm hover:bg-raised"
                >
                  <span>{child.name}</span>
                  <span className="font-mono text-xs text-muted">{child.horizon}</span>
                </Link>
              </li>
            ))}
          </ul>
        </Card>
      )}
      {tasks.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Linked tasks</CardTitle>
          </CardHeader>
          <ul className="flex flex-col gap-2">
            {tasks.map((task) => (
              <li key={task.id}>
                <label className="flex min-h-11 cursor-pointer items-center gap-3 text-sm">
                  <input
                    type="checkbox"
                    className="size-4 accent-accent"
                    checked={task.done_at !== null}
                    onChange={() => {
                      updateTask(task.id, { done: task.done_at === null })
                        .then(refresh)
                        .catch((caught: unknown) => {
                          setError(caught instanceof ApiError ? caught.message : 'Could not update')
                        })
                    }}
                  />
                  <span className={task.done_at !== null ? 'text-muted line-through' : undefined}>
                    {task.title}
                  </span>
                </label>
              </li>
            ))}
          </ul>
        </Card>
      )}
    </div>
  )
}
