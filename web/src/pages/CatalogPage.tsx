import { type FormEvent, useCallback, useEffect, useState } from 'react'

import { PageError, PageHeader } from '@/components/PageState'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import {
  type Aggregation,
  ApiError,
  type Area,
  archiveArea,
  archiveMetric,
  type Comparator,
  createArea,
  createGoal,
  createHabit,
  createMetric,
  type Direction,
  type Goal,
  type GoalHorizon,
  type GoalKind,
  type GoalStatus,
  type Habit,
  listAreas,
  listGoals,
  listHabits,
  listMetrics,
  type Metric,
  type Period,
  updateArea,
  updateGoal,
  updateHabit,
  updateMetric,
  type ValueType,
} from '@/lib/api'
import { HORIZONS, PARENT_HORIZON } from '@/lib/horizons'
import { isValidSlug } from '@/lib/slug'
import { todayIso } from '@/lib/utils'

const VALUE_TYPES: ValueType[] = ['bool', 'count', 'quantity', 'duration', 'rating', 'text']
const AGGS: Aggregation[] = ['sum', 'last', 'mean', 'max', 'min']
const DIRECTIONS: Direction[] = ['higher_is_better', 'lower_is_better', 'neutral']
const PERIODS: Period[] = ['day', 'week', 'month']
const COMPARATORS: Comparator[] = ['at_least', 'at_most', 'exactly']
const WEEKDAYS = [
  [1, 'Mon'],
  [2, 'Tue'],
  [3, 'Wed'],
  [4, 'Thu'],
  [5, 'Fri'],
  [6, 'Sat'],
  [7, 'Sun'],
] as const

export function CatalogPage() {
  const [areas, setAreas] = useState<Area[]>([])
  const [metrics, setMetrics] = useState<Metric[]>([])
  const [habits, setHabits] = useState<Habit[]>([])
  const [goals, setGoals] = useState<Goal[]>([])
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    const [areaRows, metricRows, habitRows, goalRows] = await Promise.all([
      listAreas(),
      listMetrics(),
      listHabits(),
      listGoals(),
    ])
    setAreas(areaRows)
    setMetrics(metricRows)
    setHabits(habitRows)
    setGoals(goalRows)
  }, [])

  useEffect(() => {
    refresh().catch((caught: unknown) => {
      setError(caught instanceof ApiError ? caught.message : 'Could not load catalog')
    })
  }, [refresh])

  if (error !== null) return <PageError message={error} />

  return (
    <div className="flex flex-col gap-8">
      <PageHeader title="Catalog" description="Define what you track. Capture stays on Today." />
      <AreaSection areas={areas} onChange={refresh} />
      <MetricSection areas={areas} metrics={metrics} onChange={refresh} />
      <HabitSection metrics={metrics} habits={habits} onChange={refresh} />
      <GoalSection areas={areas} metrics={metrics} goals={goals} onChange={refresh} />
    </div>
  )
}

function AreaSection({ areas, onChange }: { areas: Area[]; onChange: () => Promise<void> }) {
  const [slug, setSlug] = useState('')
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState<string | null>(null)

  async function onCreate(event: FormEvent) {
    event.preventDefault()
    if (!isValidSlug(slug)) {
      setError('slug must be lowercase letters, digits, and hyphens')
      return
    }
    setError(null)
    try {
      await createArea({
        slug,
        name: name || undefined,
        description: description || undefined,
      })
      setSlug('')
      setName('')
      setDescription('')
      await onChange()
    } catch (caught) {
      setError(messageOf(caught))
    }
  }

  return (
    <section className="flex flex-col gap-3">
      <h2 className="font-serif text-lg font-medium tracking-tight">Areas</h2>
      <Card>
        <form className="grid gap-3 sm:grid-cols-4" onSubmit={onCreate}>
          <Field label="Slug" value={slug} onChange={setSlug} required />
          <Field label="Name" value={name} onChange={setName} />
          <Field label="Description" value={description} onChange={setDescription} />
          <div className="flex items-end">
            <Button type="submit">Add area</Button>
          </div>
        </form>
        {error !== null && (
          <p className="mt-2 text-sm text-bad" role="alert">
            {error}
          </p>
        )}
      </Card>
      {areas.map((area) => (
        <EditableArea key={area.slug} area={area} onChange={onChange} />
      ))}
    </section>
  )
}

function EditableArea({ area, onChange }: { area: Area; onChange: () => Promise<void> }) {
  const [name, setName] = useState(area.name)
  const [description, setDescription] = useState(area.description ?? '')
  const [error, setError] = useState<string | null>(null)

  async function onSave(event: FormEvent) {
    event.preventDefault()
    setError(null)
    try {
      await updateArea(area.slug, { name, description: description || null })
      await onChange()
    } catch (caught) {
      setError(messageOf(caught))
    }
  }

  return (
    <Card>
      <form className="flex flex-wrap items-end gap-3" onSubmit={onSave}>
        <p className="w-32 font-mono text-sm">{area.slug}</p>
        <Field label="Name" value={name} onChange={setName} />
        <Field label="Description" value={description} onChange={setDescription} />
        <Button type="submit" size="sm">
          Save
        </Button>
        <Button
          type="button"
          size="sm"
          variant="ghost"
          onClick={() =>
            archiveArea(area.slug)
              .then(onChange)
              .catch((caught) => setError(messageOf(caught)))
          }
        >
          Archive
        </Button>
      </form>
      {error !== null && (
        <p className="mt-2 text-sm text-bad" role="alert">
          {error}
        </p>
      )}
    </Card>
  )
}

function MetricSection({
  areas,
  metrics,
  onChange,
}: {
  areas: Area[]
  metrics: Metric[]
  onChange: () => Promise<void>
}) {
  const [slug, setSlug] = useState('')
  const [area, setArea] = useState(areas[0]?.slug ?? '')
  const [valueType, setValueType] = useState<ValueType>('count')
  const [aggregation, setAggregation] = useState<Aggregation>('sum')
  const [unit, setUnit] = useState('')
  const [direction, setDirection] = useState<Direction>('neutral')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (area === '' && areas[0] !== undefined) setArea(areas[0].slug)
  }, [area, areas])

  async function onCreate(event: FormEvent) {
    event.preventDefault()
    if (!isValidSlug(slug)) {
      setError('slug must be lowercase letters, digits, and hyphens')
      return
    }
    setError(null)
    try {
      await createMetric({
        slug,
        area,
        value_type: valueType,
        aggregation,
        unit: unit || undefined,
        direction,
      })
      setSlug('')
      setUnit('')
      await onChange()
    } catch (caught) {
      setError(messageOf(caught))
    }
  }

  return (
    <section className="flex flex-col gap-3">
      <h2 className="font-serif text-lg font-medium tracking-tight">Metrics</h2>
      <Card>
        <form className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6" onSubmit={onCreate}>
          <Field label="Slug" value={slug} onChange={setSlug} required />
          <SelectField
            label="Area"
            value={area}
            onChange={setArea}
            options={areas.map((item) => item.slug)}
          />
          <SelectField
            label="Type"
            value={valueType}
            onChange={(value) => setValueType(value as ValueType)}
            options={VALUE_TYPES}
          />
          <SelectField
            label="Aggregation"
            value={aggregation}
            onChange={(value) => setAggregation(value as Aggregation)}
            options={AGGS}
          />
          <Field label="Unit" value={unit} onChange={setUnit} />
          <SelectField
            label="Direction"
            value={direction}
            onChange={(value) => setDirection(value as Direction)}
            options={DIRECTIONS}
          />
          <div className="sm:col-span-3 lg:col-span-6">
            <Button type="submit">Add metric</Button>
          </div>
        </form>
        {error !== null && (
          <p className="mt-2 text-sm text-bad" role="alert">
            {error}
          </p>
        )}
      </Card>
      {metrics.map((metric) => (
        <EditableMetric key={metric.slug} metric={metric} onChange={onChange} />
      ))}
    </section>
  )
}

function EditableMetric({ metric, onChange }: { metric: Metric; onChange: () => Promise<void> }) {
  const [name, setName] = useState(metric.name)
  const [unit, setUnit] = useState(metric.unit ?? '')
  const [direction, setDirection] = useState(metric.direction)
  const [error, setError] = useState<string | null>(null)

  async function onSave(event: FormEvent) {
    event.preventDefault()
    setError(null)
    try {
      await updateMetric(metric.slug, { name, unit: unit || null, direction })
      await onChange()
    } catch (caught) {
      setError(messageOf(caught))
    }
  }

  return (
    <Card>
      <form className="flex flex-wrap items-end gap-3" onSubmit={onSave}>
        <p className="w-32 font-mono text-sm">{metric.slug}</p>
        <Field label="Name" value={name} onChange={setName} />
        <Field label="Unit" value={unit} onChange={setUnit} />
        <SelectField
          label="Direction"
          value={direction}
          onChange={(value) => setDirection(value as Direction)}
          options={DIRECTIONS}
        />
        <Button type="submit" size="sm">
          Save
        </Button>
        <Button
          type="button"
          size="sm"
          variant="ghost"
          onClick={() =>
            archiveMetric(metric.slug)
              .then(onChange)
              .catch((caught) => setError(messageOf(caught)))
          }
        >
          Archive
        </Button>
      </form>
      {error !== null && (
        <p className="mt-2 text-sm text-bad" role="alert">
          {error}
        </p>
      )}
    </Card>
  )
}

function HabitSection({
  metrics,
  habits,
  onChange,
}: {
  metrics: Metric[]
  habits: Habit[]
  onChange: () => Promise<void>
}) {
  const trackable = metrics.filter((metric) => metric.value_type !== 'text')
  const [slug, setSlug] = useState('')
  const [metric, setMetric] = useState(trackable[0]?.slug ?? '')
  const [period, setPeriod] = useState<Period>('day')
  const [target, setTarget] = useState('1')
  const [comparator, setComparator] = useState<Comparator>('at_least')
  const [days, setDays] = useState<number[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (metric === '' && trackable[0] !== undefined) setMetric(trackable[0].slug)
  }, [metric, trackable])

  async function onCreate(event: FormEvent) {
    event.preventDefault()
    const resolved = slug || `${metric}-${period}`
    if (!isValidSlug(resolved)) {
      setError('slug must be lowercase letters, digits, and hyphens')
      return
    }
    setError(null)
    try {
      await createHabit({
        slug: resolved,
        metric,
        period,
        target_value: Number(target),
        comparator,
        weekdays: period === 'day' && days.length > 0 ? days : null,
        active_from: todayIso(),
      })
      setSlug('')
      setDays([])
      await onChange()
    } catch (caught) {
      setError(messageOf(caught))
    }
  }

  return (
    <section className="flex flex-col gap-3">
      <h2 className="font-serif text-lg font-medium tracking-tight">Habits</h2>
      <Card>
        <form className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6" onSubmit={onCreate}>
          <Field label="Slug (optional)" value={slug} onChange={setSlug} />
          <SelectField
            label="Metric"
            value={metric}
            onChange={setMetric}
            options={trackable.map((item) => item.slug)}
          />
          <SelectField
            label="Period"
            value={period}
            onChange={(value) => setPeriod(value as Period)}
            options={PERIODS}
          />
          <Field label="Target" value={target} onChange={setTarget} />
          <SelectField
            label="Comparator"
            value={comparator}
            onChange={(value) => setComparator(value as Comparator)}
            options={COMPARATORS}
          />
          <div className="flex items-end">
            <Button type="submit">Add habit</Button>
          </div>
          {period === 'day' && (
            <div className="sm:col-span-3 lg:col-span-6">
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
                            ? [...days, value].sort()
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
        </form>
        {error !== null && (
          <p className="mt-2 text-sm text-bad" role="alert">
            {error}
          </p>
        )}
      </Card>
      {habits.map((habit) => (
        <EditableHabit key={habit.slug} habit={habit} onChange={onChange} />
      ))}
    </section>
  )
}

function EditableHabit({ habit, onChange }: { habit: Habit; onChange: () => Promise<void> }) {
  const [name, setName] = useState(habit.name)
  const [target, setTarget] = useState(String(habit.target_value))
  const [comparator, setComparator] = useState(habit.comparator)
  const [activeTo, setActiveTo] = useState(habit.active_to ?? '')
  const [error, setError] = useState<string | null>(null)

  async function onSave(event: FormEvent) {
    event.preventDefault()
    setError(null)
    try {
      await updateHabit(habit.slug, {
        name,
        target_value: Number(target),
        comparator,
        active_to: activeTo || null,
      })
      await onChange()
    } catch (caught) {
      setError(messageOf(caught))
    }
  }

  return (
    <Card>
      <form className="flex flex-wrap items-end gap-3" onSubmit={onSave}>
        <p className="w-40 font-mono text-sm">{habit.slug}</p>
        <Field label="Name" value={name} onChange={setName} />
        <Field label="Target" value={target} onChange={setTarget} />
        <SelectField
          label="Comparator"
          value={comparator}
          onChange={(value) => setComparator(value as Comparator)}
          options={COMPARATORS}
        />
        <Field label="Active to" value={activeTo} onChange={setActiveTo} type="date" />
        <Button type="submit" size="sm">
          Save
        </Button>
      </form>
      {error !== null && (
        <p className="mt-2 text-sm text-bad" role="alert">
          {error}
        </p>
      )}
    </Card>
  )
}

function GoalSection({
  areas,
  metrics,
  goals,
  onChange,
}: {
  areas: Area[]
  metrics: Metric[]
  goals: Goal[]
  onChange: () => Promise<void>
}) {
  const numeric = metrics.filter((metric) => metric.value_type !== 'text')
  const [slug, setSlug] = useState('')
  const [name, setName] = useState('')
  const [area, setArea] = useState(areas[0]?.slug ?? '')
  const [kind, setKind] = useState<GoalKind>('metric_target')
  const [metric, setMetric] = useState(numeric[0]?.slug ?? '')
  const [target, setTarget] = useState('')
  const [comparator, setComparator] = useState<Comparator>('at_least')
  const [measure, setMeasure] = useState<'latest_value' | 'cumulative_since_start'>('latest_value')
  const [startOn, setStartOn] = useState(todayIso())
  const [dueOn, setDueOn] = useState(todayIso())
  const [milestones, setMilestones] = useState('')
  const [horizon, setHorizon] = useState<GoalHorizon>('medium')
  const [parent, setParent] = useState('')
  const [description, setDescription] = useState('')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (area === '' && areas[0] !== undefined) setArea(areas[0].slug)
    if (metric === '' && numeric[0] !== undefined) setMetric(numeric[0].slug)
  }, [area, areas, metric, numeric])

  async function onCreate(event: FormEvent) {
    event.preventDefault()
    const resolved =
      slug ||
      name
        .toLowerCase()
        .replaceAll(/[^a-z0-9]+/g, '-')
        .replaceAll(/^-|-$/g, '')
    if (!isValidSlug(resolved)) {
      setError('slug must be lowercase letters, digits, and hyphens')
      return
    }
    setError(null)
    try {
      await createGoal({
        slug: resolved,
        area,
        kind,
        start_on: startOn,
        due_on: dueOn,
        name: name || undefined,
        metric: kind === 'metric_target' ? metric : null,
        target_value: kind === 'metric_target' ? Number(target) : null,
        comparator: kind === 'metric_target' ? comparator : null,
        measure: kind === 'metric_target' ? measure : null,
        horizon,
        parent: parent || null,
        description: description || null,
        milestones:
          kind === 'milestone'
            ? milestones
                .split('\n')
                .map((line) => line.trim())
                .filter(Boolean)
                .map((item) => ({ name: item }))
            : null,
      })
      setSlug('')
      setName('')
      setTarget('')
      setMilestones('')
      setDescription('')
      await onChange()
    } catch (caught) {
      setError(messageOf(caught))
    }
  }

  return (
    <section className="flex flex-col gap-3">
      <h2 className="font-serif text-lg font-medium tracking-tight">Goals</h2>
      <Card>
        <form className="grid gap-3 sm:grid-cols-3" onSubmit={onCreate}>
          <Field label="Name" value={name} onChange={setName} required />
          <Field label="Slug (optional)" value={slug} onChange={setSlug} />
          <SelectField
            label="Area"
            value={area}
            onChange={setArea}
            options={areas.map((item) => item.slug)}
          />
          <SelectField
            label="Kind"
            value={kind}
            onChange={(value) => setKind(value as GoalKind)}
            options={['metric_target', 'milestone']}
          />
          <Field label="Start" value={startOn} onChange={setStartOn} type="date" />
          <Field label="Due" value={dueOn} onChange={setDueOn} type="date" />
          <SelectField
            label="Horizon"
            value={horizon}
            onChange={(value) => {
              setHorizon(value as GoalHorizon)
              setParent('')
            }}
            options={[...HORIZONS]}
          />
          {PARENT_HORIZON[horizon] !== null && (
            <SelectField
              label="Parent"
              value={parent}
              onChange={setParent}
              options={[
                '',
                ...goals
                  .filter((goal) => goal.horizon === PARENT_HORIZON[horizon])
                  .map((goal) => goal.slug),
              ]}
              labels={{ '': 'None' }}
              required={false}
            />
          )}
          <div className="sm:col-span-3">
            <Label htmlFor="goal-description">Description</Label>
            <textarea
              id="goal-description"
              className="mt-1 min-h-16 w-full rounded-lg border border-line bg-canvas px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </div>
          {kind === 'metric_target' ? (
            <>
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
                options={COMPARATORS}
              />
              <SelectField
                label="Measure"
                value={measure}
                onChange={(value) => setMeasure(value as 'latest_value' | 'cumulative_since_start')}
                options={['latest_value', 'cumulative_since_start']}
              />
            </>
          ) : (
            <div className="sm:col-span-3">
              <Label htmlFor="milestones">Milestones (one per line)</Label>
              <textarea
                id="milestones"
                className="mt-1 min-h-20 w-full rounded-lg border border-line bg-canvas px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                value={milestones}
                onChange={(event) => setMilestones(event.target.value)}
              />
            </div>
          )}
          <div className="sm:col-span-3">
            <Button type="submit">Add goal</Button>
          </div>
        </form>
        {error !== null && (
          <p className="mt-2 text-sm text-bad" role="alert">
            {error}
          </p>
        )}
      </Card>
      {goals.map((goal) => (
        <EditableGoal key={goal.slug} goal={goal} goals={goals} onChange={onChange} />
      ))}
    </section>
  )
}

function EditableGoal({
  goal,
  goals,
  onChange,
}: {
  goal: Goal
  goals: Goal[]
  onChange: () => Promise<void>
}) {
  const [name, setName] = useState(goal.name)
  const [dueOn, setDueOn] = useState(goal.due_on)
  const [target, setTarget] = useState(goal.target_value === null ? '' : String(goal.target_value))
  const [status, setStatus] = useState(goal.status)
  const [horizon, setHorizon] = useState(goal.horizon)
  const [parent, setParent] = useState(goal.parent ?? '')
  const [description, setDescription] = useState(goal.description ?? '')
  const [error, setError] = useState<string | null>(null)
  const parentHorizon = PARENT_HORIZON[horizon]
  const parentOptions =
    parentHorizon === null
      ? []
      : goals
          .filter((item) => item.slug !== goal.slug && item.horizon === parentHorizon)
          .map((item) => item.slug)

  async function onSave(event: FormEvent) {
    event.preventDefault()
    setError(null)
    try {
      await updateGoal(goal.slug, {
        name,
        due_on: dueOn,
        target_value: goal.kind === 'metric_target' && target !== '' ? Number(target) : undefined,
        status: status === 'achieved' ? undefined : (status as Exclude<GoalStatus, 'achieved'>),
        horizon,
        parent: parent || null,
        description: description || null,
      })
      await onChange()
    } catch (caught) {
      setError(messageOf(caught))
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="font-mono text-base">{goal.slug}</CardTitle>
      </CardHeader>
      <form className="flex flex-wrap items-end gap-3" onSubmit={onSave}>
        <Field label="Name" value={name} onChange={setName} />
        <Field label="Due" value={dueOn} onChange={setDueOn} type="date" />
        {goal.kind === 'metric_target' && (
          <Field label="Target" value={target} onChange={setTarget} />
        )}
        <SelectField
          label="Status"
          value={status}
          onChange={(value) => setStatus(value as GoalStatus)}
          options={['active', 'paused', 'abandoned', 'achieved']}
        />
        <SelectField
          label="Horizon"
          value={horizon}
          onChange={(value) => {
            const next = value as GoalHorizon
            setHorizon(next)
            setParent('')
          }}
          options={[...HORIZONS]}
        />
        {parentHorizon !== null && (
          <SelectField
            label="Parent"
            value={parent}
            onChange={setParent}
            options={['', ...parentOptions]}
            labels={{ '': 'None' }}
            required={false}
          />
        )}
        <div className="min-w-32 flex-1">
          <Label htmlFor={`${goal.slug}-description`}>Description</Label>
          <textarea
            id={`${goal.slug}-description`}
            className="mt-1 min-h-16 w-full rounded-lg border border-line bg-canvas px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
        </div>
        <Button type="submit" size="sm">
          Save
        </Button>
      </form>
      {error !== null && (
        <p className="mt-2 text-sm text-bad" role="alert">
          {error}
        </p>
      )}
    </Card>
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
  const id = label.toLowerCase().replaceAll(' ', '-')
  return (
    <div className="flex min-w-32 flex-1 flex-col gap-1">
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
  required = true,
}: {
  label: string
  value: string
  onChange: (value: string) => void
  options: string[]
  labels?: Record<string, string>
  required?: boolean
}) {
  const id = label.toLowerCase().replaceAll(' ', '-')
  return (
    <div className="flex min-w-32 flex-1 flex-col gap-1">
      <Label htmlFor={id}>{label}</Label>
      <Select
        id={id}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        required={required}
      >
        {options.map((option) => (
          <option key={option || 'none'} value={option}>
            {labels?.[option] ?? option}
          </option>
        ))}
      </Select>
    </div>
  )
}

function messageOf(caught: unknown): string {
  return caught instanceof ApiError || caught instanceof Error ? caught.message : 'Request failed'
}
