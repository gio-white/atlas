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
import {
  ApiError,
  type Area,
  type Comparator,
  createGoal,
  type Goal,
  type GoalHorizon,
  type GoalKind,
  type Metric,
} from '@/lib/api'
import { HORIZON_META, PARENT_HORIZON, slugFromName } from '@/lib/horizons'
import { isValidSlug } from '@/lib/slug'
import { todayIso } from '@/lib/utils'

export function GoalCreateDialog({
  open,
  onOpenChange,
  horizon,
  areas,
  metrics,
  goals,
  onCreated,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  horizon: GoalHorizon
  areas: Area[]
  metrics: Metric[]
  goals: Goal[]
  onCreated: () => Promise<void>
}) {
  const numeric = useMemo(() => metrics.filter((metric) => metric.value_type !== 'text'), [metrics])
  const parentHorizon = PARENT_HORIZON[horizon]
  const parents = useMemo(
    () => (parentHorizon === null ? [] : goals.filter((goal) => goal.horizon === parentHorizon)),
    [goals, parentHorizon],
  )
  const [name, setName] = useState('')
  const [slug, setSlug] = useState('')
  const [area, setArea] = useState('')
  const [kind, setKind] = useState<GoalKind>('milestone')
  const [metric, setMetric] = useState(numeric[0]?.slug ?? '')
  const [target, setTarget] = useState('')
  const [comparator, setComparator] = useState<Comparator>('at_least')
  const [measure, setMeasure] = useState<'latest_value' | 'cumulative_since_start'>('latest_value')
  const [startOn, setStartOn] = useState(todayIso())
  const [dueOn, setDueOn] = useState(todayIso())
  const [parent, setParent] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) return
    setName('')
    setSlug('')
    setArea('')
    setKind('milestone')
    setMetric(numeric[0]?.slug ?? '')
    setTarget('')
    setStartOn(todayIso())
    setDueOn(todayIso())
    setParent('')
    setDescription('')
    setError(null)
  }, [open, numeric])

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    const resolved = slug || slugFromName(name)
    if (!isValidSlug(resolved)) {
      setError('slug must be lowercase letters, digits, and hyphens')
      return
    }
    setError(null)
    try {
      await createGoal({
        slug: resolved,
        area: area || null,
        kind,
        start_on: startOn,
        due_on: dueOn,
        name: name || undefined,
        horizon,
        parent: parent || null,
        description: description || null,
        metric: kind === 'metric_target' ? metric : null,
        target_value: kind === 'metric_target' ? Number(target) : null,
        comparator: kind === 'metric_target' ? comparator : null,
        measure: kind === 'metric_target' ? measure : null,
      })
      onOpenChange(false)
      await onCreated()
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Could not create goal')
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>New {HORIZON_META[horizon].label.toLowerCase()} goal</DialogTitle>
          <DialogDescription>{HORIZON_META[horizon].kicker}</DialogDescription>
        </DialogHeader>
        <form className="grid gap-3" onSubmit={onSubmit}>
          <Field label="Name" value={name} onChange={setName} required />
          <Field label="Slug (optional)" value={slug} onChange={setSlug} />
          <div className="grid gap-3 sm:grid-cols-2">
            <SelectField
              label="Area"
              value={area}
              onChange={setArea}
              options={['', ...areas.map((item) => item.slug)]}
              labels={{ '': 'None' }}
            />
            <SelectField
              label="Kind"
              value={kind}
              onChange={(value) => setKind(value as GoalKind)}
              options={['milestone', 'metric_target']}
            />
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <Field label="Start" value={startOn} onChange={setStartOn} type="date" />
            <Field label="Due" value={dueOn} onChange={setDueOn} type="date" />
          </div>
          {parentHorizon !== null && (
            <SelectField
              label="Parent"
              value={parent}
              onChange={setParent}
              options={['', ...parents.map((item) => item.slug)]}
              labels={{ '': 'None' }}
            />
          )}
          <div className="flex flex-col gap-1">
            <Label htmlFor="goal-description">Description</Label>
            <textarea
              id="goal-description"
              className="min-h-16 w-full rounded-lg border border-line bg-canvas px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </div>
          {kind === 'metric_target' && (
            <div className="grid gap-3 sm:grid-cols-2">
              <SelectField
                label="Metric"
                value={metric}
                onChange={setMetric}
                options={numeric.map((item) => item.slug)}
              />
              <Field label="Target" value={target} onChange={setTarget} required />
              <SelectField
                label="Comparator"
                value={comparator}
                onChange={(value) => setComparator(value as Comparator)}
                options={['at_least', 'at_most', 'exactly']}
              />
              <SelectField
                label="Measure"
                value={measure}
                onChange={(value) => setMeasure(value as 'latest_value' | 'cumulative_since_start')}
                options={['latest_value', 'cumulative_since_start']}
              />
            </div>
          )}
          {error !== null && (
            <p className="text-sm text-bad" role="alert">
              {error}
            </p>
          )}
          <Button type="submit">Create goal</Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function Field({
  label,
  value,
  onChange,
  required,
  type = 'text',
}: {
  label: string
  value: string
  onChange: (value: string) => void
  required?: boolean
  type?: string
}) {
  const id = `create-${label.toLowerCase().replaceAll(' ', '-')}`
  return (
    <div className="flex flex-col gap-1">
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        type={type}
        value={value}
        required={required}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  )
}

function SelectField({
  label,
  value,
  onChange,
  options,
  labels,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  options: string[]
  labels?: Record<string, string>
}) {
  const id = `create-${label.toLowerCase().replaceAll(' ', '-')}`
  return (
    <div className="flex flex-col gap-1">
      <Label htmlFor={id}>{label}</Label>
      <Select id={id} value={value} onChange={(event) => onChange(event.target.value)}>
        {options.map((option) => (
          <option key={option || 'none'} value={option}>
            {labels?.[option] ?? option}
          </option>
        ))}
      </Select>
    </div>
  )
}
