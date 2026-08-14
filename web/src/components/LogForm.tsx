import { type FormEvent, useMemo, useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { ApiError, logEntry, type Metric, type ValueType } from '@/lib/api'
import { parseLogValue } from '@/lib/value'

type LogFormProps = {
  metrics: Metric[]
  occurredOn: string
  initialMetric?: string
  onLogged: () => Promise<void> | void
}

const NUMERIC: ValueType[] = ['count', 'quantity', 'duration', 'rating']

export function LogForm({ metrics, occurredOn, initialMetric, onLogged }: LogFormProps) {
  const [metricSlug, setMetricSlug] = useState(initialMetric ?? metrics[0]?.slug ?? '')
  const [raw, setRaw] = useState('')
  const [boolValue, setBoolValue] = useState(true)
  const [note, setNote] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  const metric = useMemo(
    () => metrics.find((item) => item.slug === metricSlug) ?? metrics[0],
    [metrics, metricSlug],
  )

  if (metrics.length === 0 || metric === undefined) {
    return (
      <p className="text-sm text-muted">No metrics yet. Define one in Catalog or via the CLI.</p>
    )
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    setPending(true)
    try {
      const selected = metrics.find((item) => item.slug === metricSlug) ?? metrics[0]
      if (selected === undefined) return
      const value = parseLogValue(selected.value_type, raw, boolValue)
      await logEntry({
        metric: selected.slug,
        value,
        occurred_on: occurredOn,
        note: note.trim() === '' ? null : note.trim(),
      })
      setRaw('')
      setNote('')
      await onLogged()
    } catch (caught) {
      setError(
        caught instanceof ApiError || caught instanceof Error ? caught.message : 'Could not log',
      )
    } finally {
      setPending(false)
    }
  }

  return (
    <form className="flex flex-col gap-3" onSubmit={onSubmit}>
      <div className="grid gap-3 sm:grid-cols-2">
        <div className="flex flex-col gap-1">
          <Label htmlFor="log-metric">Metric</Label>
          <Select
            id="log-metric"
            value={metric.slug}
            onChange={(event) => setMetricSlug(event.target.value)}
          >
            {metrics.map((item) => (
              <option key={item.slug} value={item.slug}>
                {item.name}
              </option>
            ))}
          </Select>
        </div>
        {metric.value_type === 'bool' ? (
          <div className="flex flex-col gap-1">
            <Label htmlFor="log-bool">Done</Label>
            <Select
              id="log-bool"
              value={boolValue ? 'true' : 'false'}
              onChange={(event) => setBoolValue(event.target.value === 'true')}
            >
              <option value="true">yes</option>
              <option value="false">no</option>
            </Select>
          </div>
        ) : (
          <div className="flex flex-col gap-1">
            <Label htmlFor="log-value">{metric.unit ?? 'Value'}</Label>
            <Input
              id="log-value"
              value={raw}
              onChange={(event) => setRaw(event.target.value)}
              placeholder={NUMERIC.includes(metric.value_type) ? '0' : ''}
              required
            />
          </div>
        )}
      </div>
      <div className="flex flex-col gap-1">
        <Label htmlFor="log-note">Note</Label>
        <Input
          id="log-note"
          value={note}
          onChange={(event) => setNote(event.target.value)}
          placeholder="optional"
        />
      </div>
      {error !== null && (
        <p className="text-sm text-bad" role="alert">
          {error}
        </p>
      )}
      <Button type="submit" disabled={pending}>
        {pending ? 'Logging…' : 'Log'}
      </Button>
    </form>
  )
}
