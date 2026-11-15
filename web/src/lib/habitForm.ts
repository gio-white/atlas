import type {
  Habit,
  HabitFrequency,
  HabitRuleInput,
  HabitSource,
  HabitThreshold,
  TimeOfDay,
} from './api'

/**
 * The New habit and Edit sheets (habits brief §9): the form's fields, the data sources it offers,
 * and turning the fields into a rule. The sources mirror the API's registry
 * (`src/atlas/domain/habit_sources.py`): its picker labels, thresholds, and defaults.
 */

export type SourceOption = {
  source: HabitSource
  /** The name in the source picker. */
  label: string
  /** The start of the rule line: "Wake time" in "Wake time before 07:00". */
  subject: string
  /** Minutes in a day, or a time of day. */
  measure: 'minutes' | 'time'
  thresholds: HabitThreshold[]
  threshold: HabitThreshold
  value: number
  /** What else to pick: a screen category or an app. */
  ref: 'category' | 'app' | null
}

const DURATION: HabitThreshold[] = ['at_least', 'at_most']
const TIME: HabitThreshold[] = ['before', 'after']

export const SOURCE_OPTIONS: SourceOption[] = [
  {
    source: 'wake_time',
    label: 'Wake time',
    subject: 'Wake time',
    measure: 'time',
    thresholds: TIME,
    threshold: 'before',
    value: 7 * 60,
    ref: null,
  },
  {
    source: 'bedtime',
    label: 'Bedtime',
    subject: 'Bedtime',
    measure: 'time',
    thresholds: TIME,
    threshold: 'before',
    value: 23 * 60,
    ref: null,
  },
  {
    source: 'time_asleep',
    label: 'Time asleep',
    subject: 'Time asleep',
    measure: 'minutes',
    thresholds: DURATION,
    threshold: 'at_least',
    value: 7 * 60,
    ref: null,
  },
  {
    source: 'screen_bad_apps',
    label: 'Screen time in Bad apps',
    subject: 'Bad apps',
    measure: 'minutes',
    thresholds: DURATION,
    threshold: 'at_most',
    value: 90,
    ref: null,
  },
  {
    source: 'screen_category',
    label: 'Screen time in a category',
    subject: 'Screen time in',
    measure: 'minutes',
    thresholds: DURATION,
    threshold: 'at_most',
    value: 60,
    ref: 'category',
  },
  {
    source: 'screen_app',
    label: 'Screen time in an app',
    subject: 'Screen time in',
    measure: 'minutes',
    thresholds: DURATION,
    threshold: 'at_most',
    value: 30,
    ref: 'app',
  },
  {
    source: 'screen_total',
    label: 'Screen time, total',
    subject: 'Screen time',
    measure: 'minutes',
    thresholds: DURATION,
    threshold: 'at_most',
    value: 3 * 60,
    ref: null,
  },
  {
    source: 'sessions_planned',
    label: 'Sessions planned',
    subject: 'A session planned',
    measure: 'time',
    thresholds: ['before'],
    threshold: 'before',
    value: 12 * 60,
    ref: null,
  },
]

export function sourceOption(source: HabitSource): SourceOption {
  const option = SOURCE_OPTIONS.find((item) => item.source === source)
  if (option === undefined) throw new Error(`unknown source ${source}`)
  return option
}

export const THRESHOLD_LABEL: Record<HabitThreshold, string> = {
  at_least: 'at least',
  at_most: 'at most',
  before: 'before',
  after: 'after',
}

export type HabitFields = {
  name: string
  frequency: HabitFrequency
  /** ISO weekdays, 1 (Monday) to 7, for Specific days. */
  weekdays: number[]
  timesAWeek: number
  timesAMonth: number
  check: 'manual' | 'data'
  source: HabitSource
  sourceRef: string
  threshold: HabitThreshold
  /** Minutes, or minutes after midnight for a time of day. */
  value: number
  timeOfDay: TimeOfDay
}

export const NEW_HABIT: HabitFields = {
  name: '',
  frequency: 'every_day',
  weekdays: [1, 2, 3, 4, 5],
  timesAWeek: 3,
  timesAMonth: 2,
  check: 'manual',
  source: 'wake_time',
  sourceRef: '',
  threshold: 'before',
  value: 7 * 60,
  timeOfDay: 'anytime',
}

/** The sheet's fields for an existing habit, from its rule in force today. */
export function fieldsFromHabit(habit: Habit): HabitFields {
  const { rule } = habit
  const source = rule.source ?? NEW_HABIT.source
  const option = sourceOption(source)
  return {
    name: habit.name,
    frequency: rule.frequency,
    weekdays:
      rule.frequency === 'specific_days' && rule.weekdays !== null
        ? [...rule.weekdays].sort((a, b) => a - b)
        : NEW_HABIT.weekdays,
    timesAWeek: rule.frequency === 'times_a_week' ? (rule.times ?? 1) : NEW_HABIT.timesAWeek,
    timesAMonth: rule.frequency === 'times_a_month' ? (rule.times ?? 1) : NEW_HABIT.timesAMonth,
    check: rule.check,
    source,
    sourceRef: rule.source_ref ?? '',
    threshold: rule.threshold ?? option.threshold,
    value: rule.value ?? option.value,
    timeOfDay: habit.time_of_day,
  }
}

/** Picking a source starts from its default threshold and value. */
export function withSource(fields: HabitFields, source: HabitSource): HabitFields {
  const option = sourceOption(source)
  return { ...fields, source, sourceRef: '', threshold: option.threshold, value: option.value }
}

/** The rule the fields describe, as the API takes it. */
export function ruleFromFields(fields: HabitFields): HabitRuleInput {
  const data = fields.check === 'data'
  const ref = data && sourceOption(fields.source).ref !== null ? fields.sourceRef : null
  return {
    frequency: fields.frequency,
    check: fields.check,
    weekdays:
      fields.frequency === 'specific_days' ? [...fields.weekdays].sort((a, b) => a - b) : null,
    times:
      fields.frequency === 'times_a_week'
        ? fields.timesAWeek
        : fields.frequency === 'times_a_month'
          ? fields.timesAMonth
          : null,
    source: data ? fields.source : null,
    source_ref: ref,
    threshold: data ? fields.threshold : null,
    value: data ? fields.value : null,
  }
}

/** Whether the schedule or the check differs from the habit's rule in force today: only then
 * does Edit ask how to apply the change. Name and time of day are not versioned. */
export function ruleChanged(habit: Habit, fields: HabitFields): boolean {
  const next = ruleFromFields(fields)
  const { rule } = habit
  const sameDays =
    (rule.weekdays === null ? null : [...rule.weekdays].sort((a, b) => a - b).join(',')) ===
    (next.weekdays === null ? null : next.weekdays.join(','))
  return !(
    rule.frequency === next.frequency &&
    sameDays &&
    rule.times === next.times &&
    rule.check === next.check &&
    rule.source === next.source &&
    (rule.source_ref ?? null) === next.source_ref &&
    rule.threshold === next.threshold &&
    rule.value === next.value
  )
}

export type FieldErrors = Partial<Record<'name' | 'weekdays' | 'sourceRef' | 'value', string>>

/** What stops the sheet from saving, per field, in plain words. */
export function fieldErrors(fields: HabitFields): FieldErrors {
  const errors: FieldErrors = {}
  if (fields.name.trim() === '') errors.name = 'Give the habit a name.'
  if (fields.frequency === 'specific_days' && fields.weekdays.length === 0) {
    errors.weekdays = 'Pick at least one day.'
  }
  if (fields.check === 'data') {
    const option = sourceOption(fields.source)
    if (option.ref !== null && fields.sourceRef === '') {
      errors.sourceRef = option.ref === 'category' ? 'Pick a category.' : 'Pick an app.'
    }
    if (option.measure === 'minutes' && !(fields.value > 0 && fields.value <= 24 * 60)) {
      errors.value = 'Enter a time between 1 minute and 24 hours.'
    }
    if (option.measure === 'time' && !(fields.value >= 0 && fields.value < 24 * 60)) {
      errors.value = 'Enter a time of day.'
    }
  }
  return errors
}

/** Minutes after midnight as "07:00" for a time input; empty while the time is not valid. */
export function clockInput(minutes: number): string {
  if (!Number.isFinite(minutes)) return ''
  const hours = Math.floor(minutes / 60)
  const mins = Math.round(minutes % 60)
  return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}`
}

/** A time input's "07:00" as minutes after midnight; null when empty or broken. */
export function parseClockInput(value: string): number | null {
  const match = /^(\d{1,2}):(\d{2})$/.exec(value)
  if (match === null) return null
  const hours = Number(match[1])
  const mins = Number(match[2])
  if (hours > 23 || mins > 59) return null
  return hours * 60 + mins
}
