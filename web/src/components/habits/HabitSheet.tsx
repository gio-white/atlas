import { type FormEvent, useEffect, useId, useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import {
  ApiError,
  createHabit,
  type Habit,
  type HabitFrequency,
  listScreenApps,
  listScreenCategories,
  type ScreenApp,
  type ScreenCategory,
  type TimeOfDay,
  updateHabit,
} from '@/lib/api'
import {
  clockInput,
  type FieldErrors,
  fieldErrors,
  fieldsFromHabit,
  type HabitFields,
  NEW_HABIT,
  parseClockInput,
  ruleChanged,
  ruleFromFields,
  SOURCE_OPTIONS,
  sourceOption,
  THRESHOLD_LABEL,
  withSource,
} from '@/lib/habitForm'
import { TIME_OF_DAY_LABEL, TIME_OF_DAY_ORDER } from '@/lib/habits'

import { Choices, Question, Stepper, WeekdayPicker } from './Choices'

const FREQUENCIES: { id: HabitFrequency; label: string }[] = [
  { id: 'every_day', label: 'Every day' },
  { id: 'specific_days', label: 'Specific days' },
  { id: 'times_a_week', label: 'Times a week' },
]
const TIMES_A_MONTH = { id: 'times_a_month' as const, label: 'Times a month' }

const CHECKS: { id: HabitFields['check']; label: string }[] = [
  { id: 'manual', label: 'You tick it' },
  { id: 'data', label: 'From your data' },
]

const WHEN: { id: TimeOfDay; label: string }[] = TIME_OF_DAY_ORDER.map((id) => ({
  id,
  label: TIME_OF_DAY_LABEL[id],
}))

type Apply = 'from_today' | 'all_days'
const APPLY: { id: Apply; label: string }[] = [
  { id: 'from_today', label: 'From today' },
  { id: 'all_days', label: 'To all past days too' },
]

function saveError(caught: unknown): string {
  if (caught instanceof ApiError) {
    if (caught.status === 409) return 'You already have a habit with this name.'
    const text = caught.message.trim()
    return text.charAt(0).toUpperCase() + text.slice(1) + (/[.!?]$/.test(text) ? '' : '.')
  }
  return 'Couldn’t save the habit. Try again.'
}

/**
 * New habit and Edit (habits brief §9): one sheet with four questions — what, how often, how it
 * is checked, and when — plus "Apply this change" when an edit changes the schedule or the
 * check. `habit` set means Edit.
 */
export function HabitSheet({
  open,
  onOpenChange,
  habit,
  onSaved,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  habit?: Habit
  onSaved: (habit: Habit) => void
}) {
  const id = useId()
  const [fields, setFields] = useState<HabitFields>(NEW_HABIT)
  const [moreOptions, setMoreOptions] = useState(false)
  const [apply, setApply] = useState<Apply>('from_today')
  const [errors, setErrors] = useState<FieldErrors>({})
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [categories, setCategories] = useState<ScreenCategory[] | null>(null)
  const [apps, setApps] = useState<ScreenApp[] | null>(null)

  useEffect(() => {
    if (!open) return
    const start = habit === undefined ? NEW_HABIT : fieldsFromHabit(habit)
    setFields(start)
    setMoreOptions(start.frequency === 'times_a_month')
    setApply('from_today')
    setErrors({})
    setError(null)
  }, [open, habit])

  const option = sourceOption(fields.source)
  const wantsCategories = open && fields.check === 'data' && option.ref === 'category'
  const wantsApps = open && fields.check === 'data' && option.ref === 'app'

  useEffect(() => {
    if (wantsCategories && categories === null) {
      listScreenCategories()
        .then(setCategories)
        .catch(() => setCategories([]))
    }
  }, [wantsCategories, categories])

  useEffect(() => {
    if (wantsApps && apps === null) {
      listScreenApps()
        .then(setApps)
        .catch(() => setApps([]))
    }
  }, [wantsApps, apps])

  function set(patch: Partial<HabitFields>) {
    setFields((current) => ({ ...current, ...patch }))
  }

  const editing = habit !== undefined
  const changed = editing && ruleChanged(habit, fields)

  async function submit(event: FormEvent) {
    event.preventDefault()
    const found = fieldErrors(fields)
    setErrors(found)
    if (Object.keys(found).length > 0) return
    setSaving(true)
    setError(null)
    try {
      const name = fields.name.trim()
      const saved = editing
        ? await updateHabit(habit.slug, {
            name,
            time_of_day: fields.timeOfDay,
            ...(changed ? { rule: ruleFromFields(fields), apply } : {}),
          })
        : await createHabit({ name, time_of_day: fields.timeOfDay, rule: ruleFromFields(fields) })
      onSaved(saved)
      onOpenChange(false)
    } catch (caught: unknown) {
      setError(saveError(caught))
    } finally {
      setSaving(false)
    }
  }

  const refs =
    option.ref === 'category'
      ? (categories ?? []).map((item) => ({ slug: item.slug, name: item.name }))
      : (apps ?? []).map((item) => ({ slug: item.slug, name: item.name }))
  const refsLoaded = option.ref === 'category' ? categories !== null : apps !== null
  const frequencies =
    moreOptions || fields.frequency === 'times_a_month'
      ? [...FREQUENCIES, TIMES_A_MONTH]
      : FREQUENCIES

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90dvh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{editing ? 'Edit habit' : 'New habit'}</DialogTitle>
          <DialogDescription className="sr-only">
            Name the habit, say how often and how it is checked, and when in the day.
          </DialogDescription>
        </DialogHeader>
        <form className="flex flex-col gap-6" onSubmit={submit} noValidate>
          <div className="flex flex-col gap-2">
            <label htmlFor={`${id}-name`} className="text-sm font-medium text-ink">
              What do you want to do?
            </label>
            <Input
              id={`${id}-name`}
              autoFocus
              className="h-11"
              placeholder="Read 20 pages"
              value={fields.name}
              aria-invalid={errors.name !== undefined}
              aria-describedby={errors.name === undefined ? undefined : `${id}-name-error`}
              onChange={(event) => set({ name: event.target.value })}
            />
            <FieldError id={`${id}-name-error`} message={errors.name} />
          </div>

          <Question legend="How often?">
            <Choices
              name={`${id}-frequency`}
              options={frequencies}
              value={fields.frequency}
              onChange={(frequency) => set({ frequency })}
            />
            {!moreOptions && fields.frequency !== 'times_a_month' && (
              <button
                type="button"
                className="self-start text-sm text-accent hover:underline"
                onClick={() => setMoreOptions(true)}
              >
                More options
              </button>
            )}
            {fields.frequency === 'specific_days' && (
              <>
                <WeekdayPicker value={fields.weekdays} onChange={(weekdays) => set({ weekdays })} />
                <FieldError message={errors.weekdays} />
              </>
            )}
            {fields.frequency === 'times_a_week' && (
              <Stepper
                value={fields.timesAWeek}
                most={7}
                unit={fields.timesAWeek === 1 ? 'time a week' : 'times a week'}
                onChange={(timesAWeek) => set({ timesAWeek })}
              />
            )}
            {fields.frequency === 'times_a_month' && (
              <Stepper
                value={fields.timesAMonth}
                most={31}
                unit={fields.timesAMonth === 1 ? 'time a month' : 'times a month'}
                onChange={(timesAMonth) => set({ timesAMonth })}
              />
            )}
          </Question>

          <Question legend="How is it checked?">
            <Choices
              name={`${id}-check`}
              options={CHECKS}
              value={fields.check}
              onChange={(check) => set({ check })}
            />
            {fields.check === 'data' && (
              <div className="flex flex-col gap-3 rounded-xl bg-raised/60 p-3">
                <Select
                  aria-label="Source"
                  className="h-11"
                  value={fields.source}
                  onChange={(event) =>
                    setFields((current) =>
                      withSource(current, event.target.value as HabitFields['source']),
                    )
                  }
                >
                  {SOURCE_OPTIONS.map((item) => (
                    <option key={item.source} value={item.source}>
                      {item.label}
                    </option>
                  ))}
                </Select>
                <div className="flex flex-wrap items-center gap-2 text-sm text-ink">
                  <span>{option.subject}</span>
                  {option.ref !== null && (
                    <Select
                      aria-label={option.ref === 'category' ? 'Category' : 'App'}
                      className="h-11 w-auto min-w-36"
                      value={fields.sourceRef}
                      onChange={(event) => set({ sourceRef: event.target.value })}
                    >
                      <option value="">
                        {option.ref === 'category' ? 'Pick a category' : 'Pick an app'}
                      </option>
                      {refs.map((item) => (
                        <option key={item.slug} value={item.slug}>
                          {item.name}
                        </option>
                      ))}
                    </Select>
                  )}
                  {option.thresholds.length > 1 ? (
                    <Select
                      aria-label="Threshold"
                      className="h-11 w-auto"
                      value={fields.threshold}
                      onChange={(event) =>
                        set({ threshold: event.target.value as HabitFields['threshold'] })
                      }
                    >
                      {option.thresholds.map((threshold) => (
                        <option key={threshold} value={threshold}>
                          {THRESHOLD_LABEL[threshold]}
                        </option>
                      ))}
                    </Select>
                  ) : (
                    <span>{THRESHOLD_LABEL[option.threshold]}</span>
                  )}
                  {option.measure === 'time' ? (
                    <Input
                      type="time"
                      aria-label="Time"
                      className="h-11 w-32"
                      value={clockInput(fields.value)}
                      onChange={(event) => {
                        const minutes = parseClockInput(event.target.value)
                        set({ value: minutes ?? Number.NaN })
                      }}
                    />
                  ) : (
                    <DurationInput value={fields.value} onChange={(value) => set({ value })} />
                  )}
                </div>
                {option.ref !== null && refsLoaded && refs.length === 0 && (
                  <p className="text-xs text-muted">
                    {option.ref === 'category'
                      ? 'No screen time categories yet. Add them in Settings → Screen time setup.'
                      : 'No apps yet. They appear once a device sends screen time.'}
                  </p>
                )}
                <FieldError message={errors.sourceRef ?? errors.value} />
              </div>
            )}
          </Question>

          <Question legend="When?">
            <Choices
              name={`${id}-when`}
              options={WHEN}
              value={fields.timeOfDay}
              onChange={(timeOfDay) => set({ timeOfDay })}
            />
          </Question>

          {changed && (
            <Question legend="Apply this change">
              <Choices name={`${id}-apply`} options={APPLY} value={apply} onChange={setApply} />
              <p className="text-xs text-muted">
                {apply === 'from_today'
                  ? 'Days before today keep the rule they had.'
                  : 'Every past day is judged again by the new rule.'}
              </p>
            </Question>
          )}

          {error !== null && (
            <p className="text-sm text-bad" role="alert">
              {error}
            </p>
          )}

          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={saving}>
              {editing ? 'Save' : 'Create habit'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function FieldError({ id, message }: { id?: string; message: string | undefined }) {
  if (message === undefined) return null
  return (
    <p id={id} className="text-xs text-bad">
      {message}
    </p>
  )
}

/** Minutes as hours and minutes: "1 h 30 m". */
function DurationInput({ value, onChange }: { value: number; onChange: (value: number) => void }) {
  const safe = Number.isFinite(value) ? value : 0
  const hours = Math.floor(safe / 60)
  const minutes = Math.round(safe % 60)
  return (
    <span className="inline-flex items-center gap-1.5">
      <Input
        type="number"
        inputMode="numeric"
        aria-label="Hours"
        min={0}
        max={24}
        className="h-11 w-16"
        value={hours}
        onChange={(event) => onChange(Number(event.target.value || 0) * 60 + minutes)}
      />
      <span className="text-muted">h</span>
      <Input
        type="number"
        inputMode="numeric"
        aria-label="Minutes"
        min={0}
        max={59}
        className="h-11 w-16"
        value={minutes}
        onChange={(event) => onChange(hours * 60 + Number(event.target.value || 0))}
      />
      <span className="text-muted">m</span>
    </span>
  )
}
