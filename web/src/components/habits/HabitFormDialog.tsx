import { type FormEvent, type ReactNode, useEffect, useState } from 'react'

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
import {
  ApiError,
  type Comparator,
  createHabit,
  type Habit,
  type HabitKind,
  type Period,
  type TimeOfDay,
  updateHabit,
} from '@/lib/api'
import { KIND_META, TIME_OF_DAY_LABEL, TIME_OF_DAY_ORDER, WEEKDAY_SHORT } from '@/lib/habits'
import { cn, todayIso } from '@/lib/utils'

type Frequency = 'daily' | 'weekdays' | 'week' | 'month'

const FREQUENCIES: { id: Frequency; label: string }[] = [
  { id: 'daily', label: 'Every day' },
  { id: 'weekdays', label: 'Some days' },
  { id: 'week', label: 'Per week' },
  { id: 'month', label: 'Per month' },
]

const KINDS: HabitKind[] = ['check', 'count', 'duration', 'quit']

function frequencyOf(habit: Habit): Frequency {
  if (habit.period === 'week') return 'week'
  if (habit.period === 'month') return 'month'
  return habit.weekdays === null ? 'daily' : 'weekdays'
}

/** Create a habit (habit-first: its measurement is made for it) or edit one. */
export function HabitFormDialog({
  open,
  onOpenChange,
  habit = null,
  onSaved,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  habit?: Habit | null
  onSaved: (habit: Habit) => Promise<void> | void
}) {
  const editing = habit !== null
  const [name, setName] = useState('')
  const [kind, setKind] = useState<HabitKind>('check')
  const [frequency, setFrequency] = useState<Frequency>('daily')
  const [weekdays, setWeekdays] = useState<number[]>([1, 2, 3, 4, 5])
  const [target, setTarget] = useState('1')
  const [unit, setUnit] = useState('')
  const [comparator, setComparator] = useState<Comparator>('at_least')
  const [timeOfDay, setTimeOfDay] = useState<TimeOfDay>('anytime')
  const [startOn, setStartOn] = useState(todayIso())
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  useEffect(() => {
    if (!open) return
    setName(habit?.name ?? '')
    setKind(habit?.kind ?? 'check')
    setFrequency(habit ? frequencyOf(habit) : 'daily')
    setWeekdays(habit?.weekdays ?? [1, 2, 3, 4, 5])
    setTarget(String(habit?.target_value ?? 1))
    setUnit(habit?.unit ?? '')
    setComparator(habit?.comparator ?? 'at_least')
    setTimeOfDay(habit?.time_of_day ?? 'anytime')
    setStartOn(todayIso())
    setError(null)
    setPending(false)
  }, [open, habit])

  const needsTarget = kind === 'count' || kind === 'duration' || frequency !== 'daily'
  const showTarget =
    kind !== 'quit' && (kind !== 'check' || frequency === 'week' || frequency === 'month')
  const targetLabel =
    kind === 'check'
      ? `Times ${frequency === 'month' ? 'a month' : 'a week'}`
      : kind === 'duration'
        ? 'Minutes'
        : 'Target'

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    const cleaned = name.trim()
    if (cleaned === '') {
      setError('Give the habit a name.')
      return
    }
    const targetValue = Number(target)
    if (showTarget && (!Number.isFinite(targetValue) || targetValue <= 0)) {
      setError('The target must be a positive number.')
      return
    }
    if (frequency === 'weekdays' && weekdays.length === 0) {
      setError('Pick at least one day.')
      return
    }
    const period: Period = frequency === 'week' ? 'week' : frequency === 'month' ? 'month' : 'day'
    const days = frequency === 'weekdays' ? [...weekdays].sort((a, b) => a - b) : null
    setPending(true)
    setError(null)
    try {
      const saved = editing
        ? await updateHabit(habit.slug, {
            name: cleaned,
            time_of_day: timeOfDay,
            ...(habit.kind !== 'quit' && showTarget ? { target_value: targetValue } : {}),
            ...(habit.kind === 'count' ? { comparator, unit: unit.trim() || null } : {}),
            ...(habit.period === 'day' && habit.kind !== 'quit' ? { weekdays: days } : {}),
          })
        : await createHabit({
            name: cleaned,
            kind,
            period: kind === 'quit' ? 'day' : period,
            target_value: kind === 'quit' ? null : needsTarget && showTarget ? targetValue : 1,
            comparator: kind === 'count' ? comparator : 'at_least',
            unit: kind === 'count' ? unit.trim() || null : null,
            weekdays: kind === 'quit' ? null : days,
            time_of_day: timeOfDay,
            active_from: startOn,
          })
      onOpenChange(false)
      await onSaved(saved)
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Could not save the habit')
    } finally {
      setPending(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[calc(100dvh-2rem)] max-w-xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{editing ? 'Edit habit' : 'New habit'}</DialogTitle>
          <DialogDescription>
            {editing
              ? 'Changes apply to how past days are judged too.'
              : 'Pick what kind of habit it is; Atlas sets up the tracking.'}
          </DialogDescription>
        </DialogHeader>
        <form className="flex flex-col gap-4" onSubmit={onSubmit}>
          <div className="flex flex-col gap-1">
            <Label htmlFor="habit-name">Name</Label>
            <Input
              id="habit-name"
              value={name}
              placeholder="Morning pushups, Read, No doomscrolling…"
              onChange={(event) => setName(event.target.value)}
              autoFocus
            />
          </div>

          {editing ? null : (
            <fieldset className="flex flex-col gap-2">
              <legend className="mb-1 text-xs font-medium text-muted">Type</legend>
              <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
                {KINDS.map((item) => (
                  <label
                    key={item}
                    className={cn(
                      'flex cursor-pointer flex-col gap-1 rounded-xl border p-3 text-sm',
                      kind === item
                        ? 'border-update bg-update/10 text-ink'
                        : 'border-line text-muted hover:text-ink',
                    )}
                  >
                    <input
                      type="radio"
                      name="habit-kind"
                      className="sr-only"
                      checked={kind === item}
                      onChange={() => setKind(item)}
                    />
                    <span className="font-medium">{KIND_META[item].label}</span>
                  </label>
                ))}
              </div>
              <p className="text-xs text-muted">{KIND_META[kind].hint}</p>
            </fieldset>
          )}

          {kind === 'quit' || (editing && habit.period !== 'day') ? null : (
            <Choice
              legend="How often"
              options={FREQUENCIES.filter(
                (item) => !editing || item.id === 'daily' || item.id === 'weekdays',
              )}
              value={frequency}
              onChange={setFrequency}
            />
          )}

          {frequency === 'weekdays' && kind !== 'quit' ? (
            <fieldset className="flex flex-wrap gap-1.5">
              <legend className="sr-only">Days</legend>
              {WEEKDAY_SHORT.map((label, index) => {
                const day = index + 1
                const checked = weekdays.includes(day)
                return (
                  <label
                    key={label}
                    className={cn(
                      'cursor-pointer rounded-full border px-3 py-1 text-xs',
                      checked ? 'border-update bg-update/15 text-ink' : 'border-line text-muted',
                    )}
                  >
                    <input
                      type="checkbox"
                      className="sr-only"
                      checked={checked}
                      onChange={() =>
                        setWeekdays((current) =>
                          checked ? current.filter((value) => value !== day) : [...current, day],
                        )
                      }
                    />
                    {label}
                  </label>
                )
              })}
            </fieldset>
          ) : null}

          {showTarget ? (
            <div className="grid gap-3 sm:grid-cols-3">
              {kind === 'count' ? (
                <Choice
                  legend="Goal"
                  options={[
                    { id: 'at_least', label: 'At least' },
                    { id: 'at_most', label: 'At most' },
                  ]}
                  value={comparator === 'exactly' ? 'at_least' : comparator}
                  onChange={(value) => setComparator(value as Comparator)}
                />
              ) : null}
              <div className="flex flex-col gap-1">
                <Label htmlFor="habit-target">{targetLabel}</Label>
                <Input
                  id="habit-target"
                  type="number"
                  min="0"
                  step="any"
                  value={target}
                  onChange={(event) => setTarget(event.target.value)}
                />
              </div>
              {kind === 'count' ? (
                <div className="flex flex-col gap-1">
                  <Label htmlFor="habit-unit">Unit</Label>
                  <Input
                    id="habit-unit"
                    value={unit}
                    placeholder="reps, pages, glasses"
                    onChange={(event) => setUnit(event.target.value)}
                  />
                </div>
              ) : null}
            </div>
          ) : null}

          <Choice
            legend="Time of day"
            options={TIME_OF_DAY_ORDER.map((id) => ({ id, label: TIME_OF_DAY_LABEL[id] }))}
            value={timeOfDay}
            onChange={setTimeOfDay}
          />

          {editing ? null : (
            <div className="flex flex-col gap-1">
              <Label htmlFor="habit-start">Start</Label>
              <Input
                id="habit-start"
                type="date"
                className="w-auto"
                value={startOn}
                onChange={(event) => setStartOn(event.target.value)}
              />
            </div>
          )}

          {error !== null ? (
            <p className="text-sm text-bad" role="alert">
              {error}
            </p>
          ) : null}
          <Button type="submit" disabled={pending}>
            {editing ? 'Save' : 'Create habit'}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function Choice<T extends string>({
  legend,
  options,
  value,
  onChange,
}: {
  legend: ReactNode
  options: { id: T; label: string }[]
  value: T
  onChange: (next: T) => void
}) {
  return (
    <fieldset className="flex flex-col gap-1">
      <legend className="mb-1 text-xs font-medium text-muted">{legend}</legend>
      <div className="flex flex-wrap gap-1 rounded-lg bg-raised p-1">
        {options.map((option) => (
          <label
            key={option.id}
            className={cn(
              'flex-1 cursor-pointer rounded-md px-3 py-1.5 text-center text-xs font-medium whitespace-nowrap',
              value === option.id ? 'bg-surface text-ink shadow-sm' : 'text-muted hover:text-ink',
            )}
          >
            <input
              type="radio"
              className="sr-only"
              checked={value === option.id}
              onChange={() => onChange(option.id)}
            />
            {option.label}
          </label>
        ))}
      </div>
    </fieldset>
  )
}
