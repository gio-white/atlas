import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { WeekGrid } from '@/components/WeekGrid'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
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

  if (error !== null) return <p className="text-sm text-bad">{error}</p>
  if (view === null) return <p className="text-sm text-muted">Loading…</p>

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
      <WeekGrid view={view} search={params.toString()} />
    </Card>
  )
}
