import { type FormEvent, useCallback, useEffect, useState } from 'react'

import { EmptyState, PageError, PageHeader, PageLoading } from '@/components/PageState'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import {
  type Aggregation,
  ApiError,
  archiveMetric,
  createMetric,
  type Direction,
  listMetrics,
  type Metric,
  updateMetric,
  type ValueType,
} from '@/lib/api'
import {
  AGGREGATION_LABEL,
  AGGREGATIONS,
  DIRECTION_LABEL,
  DIRECTIONS,
  isManagedMetric,
  metricSummary,
  VALUE_TYPE_LABEL,
  VALUE_TYPES,
} from '@/lib/labels'

/** What to tell someone when a save fails, without passing on the API's own wording. */
function saveError(caught: unknown): string {
  if (caught instanceof ApiError) {
    if (caught.status === 0) return caught.message
    if (caught.status === 409) return 'A metric with that name already exists.'
    if (caught.status === 400) return "That name can't be used. Try letters and numbers."
  }
  return "Couldn't save. Try again."
}

/**
 * Settings → Metrics: the things you measure. Create one, rename it, change its unit or which
 * way is better, or archive it. App metrics and the journal's metric are not listed: Atlas
 * keeps those itself.
 */
export function MetricsPage() {
  const [metrics, setMetrics] = useState<Metric[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    const metricRows = await listMetrics()
    setMetrics(metricRows.filter(isManagedMetric).sort((a, b) => a.name.localeCompare(b.name)))
  }, [])

  useEffect(() => {
    load().catch((caught: unknown) =>
      setError(
        caught instanceof ApiError && caught.status === 0
          ? caught.message
          : "Couldn't load your metrics.",
      ),
    )
  }, [load])

  return (
    <div className="flex max-w-3xl flex-col gap-5">
      <PageHeader
        tab
        title="Metrics"
        description="The things you measure. To log a value, use Add, then Entry."
      />
      {error !== null && <PageError message={error} />}
      {metrics === null ? (
        error === null && <PageLoading />
      ) : (
        <>
          <NewMetric onCreated={load} />
          {metrics.length === 0 ? (
            <EmptyState title="No metrics yet" hint="Add one above." />
          ) : (
            <ul className="flex flex-col gap-3">
              {metrics.map((metric) => (
                <li key={metric.slug}>
                  <MetricRow metric={metric} onChanged={load} />
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </div>
  )
}

function NewMetric({ onCreated }: { onCreated: () => Promise<void> }) {
  const [name, setName] = useState('')
  const [valueType, setValueType] = useState<ValueType>('count')
  const [aggregation, setAggregation] = useState<Aggregation>('sum')
  const [direction, setDirection] = useState<Direction>('neutral')
  const [unit, setUnit] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  function chooseType(next: ValueType) {
    setValueType(next)
    // A note cannot be added up; the latest one is the only choice that means anything.
    if (next === 'text') setAggregation('last')
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    const trimmed = name.trim()
    if (trimmed === '' || pending) return
    setError(null)
    setPending(true)
    try {
      await createMetric({
        name: trimmed,
        value_type: valueType,
        aggregation,
        direction,
        unit: unit.trim() || undefined,
      })
      setName('')
      setUnit('')
      await onCreated()
    } catch (caught) {
      setError(saveError(caught))
    } finally {
      setPending(false)
    }
  }

  return (
    <Card>
      <form className="flex flex-col gap-3" onSubmit={onSubmit} aria-labelledby="new-metric">
        <h3 id="new-metric" className="text-base font-semibold text-ink">
          New metric
        </h3>
        <div className="grid gap-3 sm:grid-cols-2">
          <div className="flex flex-col gap-1">
            <Label htmlFor="metric-name">Name</Label>
            <Input
              id="metric-name"
              value={name}
              placeholder="Glasses of water"
              onChange={(event) => setName(event.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1">
            <Label htmlFor="metric-unit">Unit (optional)</Label>
            <Input
              id="metric-unit"
              value={unit}
              placeholder="glasses"
              onChange={(event) => setUnit(event.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1">
            <Label htmlFor="metric-type">What you record</Label>
            <Select
              id="metric-type"
              value={valueType}
              onChange={(event) => chooseType(event.target.value as ValueType)}
            >
              {VALUE_TYPES.map((value) => (
                <option key={value} value={value}>
                  {VALUE_TYPE_LABEL[value]}
                </option>
              ))}
            </Select>
          </div>
          <div className="flex flex-col gap-1">
            <Label htmlFor="metric-aggregation">Several values in one day</Label>
            <Select
              id="metric-aggregation"
              value={aggregation}
              disabled={valueType === 'text'}
              onChange={(event) => setAggregation(event.target.value as Aggregation)}
            >
              {AGGREGATIONS.map((value) => (
                <option key={value} value={value}>
                  {AGGREGATION_LABEL[value]}
                </option>
              ))}
            </Select>
          </div>
          <div className="flex flex-col gap-1">
            <Label htmlFor="metric-direction">Which way is better</Label>
            <Select
              id="metric-direction"
              value={direction}
              onChange={(event) => setDirection(event.target.value as Direction)}
            >
              {DIRECTIONS.map((value) => (
                <option key={value} value={value}>
                  {DIRECTION_LABEL[value]}
                </option>
              ))}
            </Select>
          </div>
        </div>
        {error !== null && (
          <p className="text-sm text-bad" role="alert">
            {error}
          </p>
        )}
        <div>
          <Button type="submit" disabled={pending || name.trim() === ''}>
            Add metric
          </Button>
        </div>
      </form>
    </Card>
  )
}

type Mode = 'view' | 'edit' | 'archive'

function MetricRow({ metric, onChanged }: { metric: Metric; onChanged: () => Promise<void> }) {
  const [mode, setMode] = useState<Mode>('view')
  const [name, setName] = useState(metric.name)
  const [unit, setUnit] = useState(metric.unit ?? '')
  const [direction, setDirection] = useState(metric.direction)
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const id = `metric-${metric.id}`

  function startEdit() {
    setName(metric.name)
    setUnit(metric.unit ?? '')
    setDirection(metric.direction)
    setError(null)
    setMode('edit')
  }

  async function run(action: () => Promise<unknown>) {
    setError(null)
    setPending(true)
    try {
      await action()
      setMode('view')
      await onChanged()
    } catch (caught) {
      setError(saveError(caught))
    } finally {
      setPending(false)
    }
  }

  function onSave(event: FormEvent) {
    event.preventDefault()
    const trimmed = name.trim()
    if (trimmed === '') return
    void run(() =>
      updateMetric(metric.slug, { name: trimmed, unit: unit.trim() || null, direction }),
    )
  }

  return (
    <Card className="flex flex-col gap-3">
      {mode === 'edit' ? (
        <form className="flex flex-col gap-3" onSubmit={onSave} aria-label={`Edit ${metric.name}`}>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="flex flex-col gap-1">
              <Label htmlFor={`${id}-name`}>Name</Label>
              <Input
                id={`${id}-name`}
                value={name}
                onChange={(event) => setName(event.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1">
              <Label htmlFor={`${id}-unit`}>Unit (optional)</Label>
              <Input
                id={`${id}-unit`}
                value={unit}
                onChange={(event) => setUnit(event.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1">
              <Label htmlFor={`${id}-direction`}>Which way is better</Label>
              <Select
                id={`${id}-direction`}
                value={direction}
                onChange={(event) => setDirection(event.target.value as Direction)}
              >
                {DIRECTIONS.map((value) => (
                  <option key={value} value={value}>
                    {DIRECTION_LABEL[value]}
                  </option>
                ))}
              </Select>
            </div>
          </div>
          <div className="flex gap-2">
            <Button type="submit" size="sm" disabled={pending || name.trim() === ''}>
              Save
            </Button>
            <Button type="button" size="sm" variant="ghost" onClick={() => setMode('view')}>
              Cancel
            </Button>
          </div>
        </form>
      ) : (
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="flex flex-wrap items-center gap-2 font-medium text-ink">
              {metric.name}
              {metric.origin === 'habit' && <Badge className="normal-case">Made for a habit</Badge>}
            </p>
            <p className="text-sm text-muted">{metricSummary(metric)}</p>
          </div>
          {mode === 'view' && (
            <div className="flex gap-2">
              <Button type="button" size="sm" variant="outline" onClick={startEdit}>
                Edit
              </Button>
              <Button
                type="button"
                size="sm"
                variant="ghost"
                onClick={() => {
                  setError(null)
                  setMode('archive')
                }}
              >
                Archive
              </Button>
            </div>
          )}
        </div>
      )}
      {mode === 'archive' && (
        <div className="flex flex-col gap-2 rounded-xl border border-warn/40 bg-warn/10 p-3">
          <p className="text-sm text-ink">
            Archive {metric.name}? Its entries are kept, but it leaves this list and you can no
            longer log to it.
          </p>
          <div className="flex gap-2">
            <Button
              type="button"
              size="sm"
              variant="destructive"
              disabled={pending}
              onClick={() => void run(() => archiveMetric(metric.slug))}
            >
              Archive metric
            </Button>
            <Button type="button" size="sm" variant="ghost" onClick={() => setMode('view')}>
              Cancel
            </Button>
          </div>
        </div>
      )}
      {error !== null && (
        <p className="text-sm text-bad" role="alert">
          {error}
        </p>
      )}
    </Card>
  )
}
