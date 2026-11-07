import { type FormEvent, useState } from 'react'
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

const VALUE_PLACEHOLDER: Record<ValueType, string> = {
  bool: '',
  count: 'How many?',
  quantity: 'Amount',
  duration: 'Minutes',
  rating: '1 to 10',
  text: 'Write something',
}

export function LogForm({ metrics, occurredOn, initialMetric, onLogged }: LogFormProps) {
  const [metricSlug, setMetricSlug] = useState(
    initialMetric ?? (metrics.length === 1 ? (metrics[0]?.slug ?? '') : ''),
  )
  const [raw, setRaw] = useState('')
  const [boolValue, setBoolValue] = useState(true)
  const [note, setNote] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  const metric = metrics.find((item) => item.slug === metricSlug)
  const unit = metric?.unit ?? (metric?.value_type === 'duration' ? 'min' : null)

  if (metrics.length === 0) {
    return <p className="text-sm text-muted">No metrics yet. Add one in Catalog.</p>
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (metric === undefined) {
      setError('Choose what you are logging.')
      return
    }
    setError(null)
    setPending(true)
    try {
      const value = parseLogValue(metric.value_type, raw, boolValue)
      await logEntry({
        metric: metric.slug,
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
            value={metricSlug}
            required
            onChange={(event) => {
              setMetricSlug(event.target.value)
              setRaw('')
            }}
          >
            <option value="" disabled>
              Choose…
            </option>
            {metrics.map((item) => (
              <option key={item.slug} value={item.slug}>
                {item.name}
              </option>
            ))}
          </Select>
        </div>
        {metric?.value_type === 'bool' ? (
          <div className="flex flex-col gap-1">
            <Label htmlFor="log-bool">Done</Label>
            <Select
              id="log-bool"
              value={boolValue ? 'true' : 'false'}
              onChange={(event) => setBoolValue(event.target.value === 'true')}
            >
              <option value="true">Yes</option>
              <option value="false">No</option>
            </Select>
          </div>
        ) : (
          <div className="flex flex-col gap-1">
            <Label htmlFor="log-value">Value</Label>
            <div className="flex items-center gap-2">
              <Input
                id="log-value"
                value={raw}
                onChange={(event) => setRaw(event.target.value)}
                placeholder={metric === undefined ? '' : VALUE_PLACEHOLDER[metric.value_type]}
                inputMode={
                  metric === undefined || metric.value_type === 'text' ? undefined : 'decimal'
                }
                disabled={metric === undefined}
                required
              />
              {unit !== null && (
                <span className="shrink-0 text-sm text-muted" data-testid="log-unit">
                  {unit}
                </span>
              )}
            </div>
          </div>
        )}
      </div>
      <div className="flex flex-col gap-1">
        <Label htmlFor="log-note">Note</Label>
        <Input
          id="log-note"
          value={note}
          onChange={(event) => setNote(event.target.value)}
          placeholder="Optional"
        />
      </div>
      {error !== null && (
        <p className="text-sm text-bad" role="alert">
          {error}
        </p>
      )}
      <Button type="submit" disabled={pending}>
        {pending ? 'Saving…' : 'Save'}
      </Button>
    </form>
  )
}
