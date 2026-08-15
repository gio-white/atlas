import { type FormEvent, useEffect, useMemo, useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { ApiError, type Comparator, createHabit, type Metric, type Period } from '@/lib/api'
import { HABIT_PERIOD_META, HABIT_PERIODS } from '@/lib/habitsSummary'
import { slugFromName } from '@/lib/horizons'
import { isValidSlug } from '@/lib/slug'
import { todayIso } from '@/lib/utils'

const COMPARATORS: Comparator[] = ['at_least', 'at_most', 'exactly']
const WEEKDAYS: [number, string][] = [
  [1, 'Mon'],
  [2, 'Tue'],
  [3, 'Wed'],
  [4, 'Thu'],
  [5, 'Fri'],
  [6, 'Sat'],
  [7, 'Sun'],
]

export function HabitCreateDialog({
  open,
  onOpenChange,
  metrics,
  onCreated,
  defaultPeriod = 'day',
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  metrics: Metric[]
  onCreated: () => Promise<void>
  defaultPeriod?: Period
}) {
  const trackable = useMemo(
    () => metrics.filter((metric) => metric.value_type !== 'text'),
    [metrics],
  )
  const [name, setName] = useState('')
  const [slug, setSlug] = useState('')
  const [metric, setMetric] = useState(trackable[0]?.slug ?? '')
  const [period, setPeriod] = useState<Period>(defaultPeriod)
  const [target, setTarget] = useState('1')
  const [comparator, setComparator] = useState<Comparator>('at_least')
  const [days, setDays] = useState<number[]>([])
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  useEffect(() => {
    if (!open) return
    setName('')
    setSlug('')
    setMetric(trackable[0]?.slug ?? '')
    setPeriod(defaultPeriod)
    setTarget('1')
    setComparator('at_least')
    setDays([])
    setError(null)
    setPending(false)
  }, [open, defaultPeriod, trackable])

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    const resolved = slug || slugFromName(name) || `${metric}-${period}`
    if (!isValidSlug(resolved)) {
      setError('slug must be lowercase letters, digits, and hyphens')
      return
    }
    if (metric === '') {
      setError('choose a metric to measure this habit')
      return
    }
    setError(null)
    setPending(true)
    try {
      await createHabit({
        slug: resolved,
        metric,
        period,
        target_value: Number(target),
        comparator,
        name: name || undefined,
        weekdays: period === 'day' && days.length > 0 ? days : null,
        active_from: todayIso(),
      })
      onOpenChange(false)
      await onCreated()
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Could not create habit')
    } finally {
      setPending(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>New habit</DialogTitle>
          <DialogDescription>
            A recurring commitment over a metric. Streaks are computed from entries, not from a
            checkbox of their own.
          </DialogDescription>
        </DialogHeader>
        <form className="grid gap-3" onSubmit={onSubmit}>
          <div className="flex flex-col gap-1">
            <Label htmlFor="habit-name">Name</Label>
            <Input
              id="habit-name"
              value={name}
              required
              onChange={(event) => setName(event.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1">
            <Label htmlFor="habit-slug">Slug (optional)</Label>
            <Input id="habit-slug" value={slug} onChange={(event) => setSlug(event.target.value)} />
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="flex flex-col gap-1">
              <Label htmlFor="habit-metric">Metric</Label>
              <Select
                id="habit-metric"
                value={metric}
                onChange={(event) => setMetric(event.target.value)}
              >
                {trackable.length === 0 ? (
                  <option value="">No trackable metrics</option>
                ) : (
                  trackable.map((item) => (
                    <option key={item.slug} value={item.slug}>
                      {item.name}
                    </option>
                  ))
                )}
              </Select>
            </div>
            <div className="flex flex-col gap-1">
              <Label htmlFor="habit-period">Period</Label>
              <Select
                id="habit-period"
                value={period}
                onChange={(event) => setPeriod(event.target.value as Period)}
              >
                {HABIT_PERIODS.map((item) => (
                  <option key={item} value={item}>
                    {HABIT_PERIOD_META[item].label}
                  </option>
                ))}
              </Select>
            </div>
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="flex flex-col gap-1">
              <Label htmlFor="habit-target">Target</Label>
              <Input
                id="habit-target"
                value={target}
                required
                onChange={(event) => setTarget(event.target.value)}
              />
            </div>
            <div className="flex flex-col gap-1">
              <Label htmlFor="habit-comparator">Comparator</Label>
              <Select
                id="habit-comparator"
                value={comparator}
                onChange={(event) => setComparator(event.target.value as Comparator)}
              >
                {COMPARATORS.map((item) => (
                  <option key={item} value={item}>
                    {item}
                  </option>
                ))}
              </Select>
            </div>
          </div>
          {period === 'day' && (
            <div>
              <Label>Weekdays (empty = every day)</Label>
              <div className="mt-1 flex flex-wrap gap-2">
                {WEEKDAYS.map(([value, label]) => (
                  <label key={value} className="flex items-center gap-1 text-xs">
                    <input
                      type="checkbox"
                      checked={days.includes(value)}
                      onChange={(event) =>
                        setDays(
                          event.target.checked
                            ? [...days, value].sort((left, right) => left - right)
                            : days.filter((day) => day !== value),
                        )
                      }
                    />
                    {label}
                  </label>
                ))}
              </div>
            </div>
          )}
          {error !== null && (
            <p className="text-sm text-bad" role="alert">
              {error}
            </p>
          )}
          <Button type="submit" disabled={pending || name.trim() === '' || metric === ''}>
            Create habit
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}
