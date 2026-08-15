import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { EmptyState, PageLoading, PageUnavailable } from '@/components/PageState'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { WeekGrid } from '@/components/WeekGrid'
import { ApiError, getWeek, type WeekView } from '@/lib/api'
import { useAsOf } from '@/lib/asOf'

export function WeekPage() {
  const asOf = useAsOf()
  const [params] = useSearchParams()
  const [view, setView] = useState<WeekView | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setError(null)
    getWeek(asOf)
      .then((data) => {
        if (!cancelled) setView(data)
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setError(caught instanceof ApiError ? caught.message : 'Could not load week')
          setView(null)
        }
      })
    return () => {
      cancelled = true
    }
  }, [asOf])

  if (error !== null) {
    return <PageUnavailable title="Week" message={error} />
  }
  if (view === null) return <PageLoading />

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle>Week</CardTitle>
          <CardDescription className="mt-1 font-mono">
            {view.week_start} → {view.week_end}
          </CardDescription>
        </div>
      </CardHeader>
      {view.habits.length === 0 ? (
        <EmptyState
          title="No habits this week"
          hint="Add a habit on the Habits board to fill the grid."
          actionLabel="Open habits"
          actionTo="/habit"
        />
      ) : (
        <WeekGrid view={view} search={params.toString()} />
      )}
    </Card>
  )
}
