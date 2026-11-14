import type { Habit, HabitRule, HabitSource, HabitThreshold, TimeOfDay } from './api'
import { formatMinutes } from './format'
import { formatClock } from './sleep'

export const TIME_OF_DAY_ORDER: TimeOfDay[] = ['morning', 'afternoon', 'evening', 'anytime']

export const TIME_OF_DAY_LABEL: Record<TimeOfDay, string> = {
  morning: 'Morning',
  afternoon: 'Afternoon',
  evening: 'Evening',
  anytime: 'Anytime',
}

export const WEEKDAY_SHORT = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

/** The start of a data rule's line, e.g. "Wake time" in "Wake time before 07:00". Mirrors the
 * API's source registry (src/atlas/domain/habit_sources.py). */
const SOURCE_SUBJECT: Record<HabitSource, string> = {
  wake_time: 'Wake time',
  bedtime: 'Bedtime',
  time_asleep: 'Time asleep',
  screen_bad_apps: 'Bad apps',
  screen_category: 'Screen time in',
  screen_app: 'Screen time in',
  screen_total: 'Screen time',
  sessions_planned: 'A session planned',
}

const TIME_SOURCES: ReadonlySet<HabitSource> = new Set(['wake_time', 'bedtime', 'sessions_planned'])

const THRESHOLD_WORD: Record<HabitThreshold, string> = {
  at_least: 'at least',
  at_most: 'at most',
  before: 'before',
  after: 'after',
}

export function weekdaysLabel(weekdays: number[] | null): string {
  if (weekdays === null || weekdays.length === 7) return 'Every day'
  const sorted = [...weekdays].sort((a, b) => a - b)
  if (sorted.join(',') === '1,2,3,4,5') return 'Weekdays'
  if (sorted.join(',') === '6,7') return 'Weekends'
  return sorted.map((day) => WEEKDAY_SHORT[day - 1]).join(', ')
}

/** "Every day", "Weekdays", "3× a week", "2× a month". */
export function frequencyLabel(rule: Pick<HabitRule, 'frequency' | 'weekdays' | 'times'>): string {
  switch (rule.frequency) {
    case 'every_day':
      return 'Every day'
    case 'specific_days':
      return weekdaysLabel(rule.weekdays)
    case 'times_a_week':
      return `${rule.times ?? 1}× a week`
    case 'times_a_month':
      return `${rule.times ?? 1}× a month`
  }
}

/** A data rule as one readable line: "Wake time before 07:00", "Bad apps at most 1h 30m",
 * "Screen time in Instagram at most 30m". Null for a habit you tick. */
export function sourceLine(
  rule: Pick<HabitRule, 'source' | 'source_ref_name' | 'source_ref' | 'threshold' | 'value'>,
): string | null {
  if (rule.source === null || rule.threshold === null || rule.value === null) return null
  const ref = rule.source_ref_name ?? rule.source_ref
  const subject =
    rule.source === 'screen_category' || rule.source === 'screen_app'
      ? `${SOURCE_SUBJECT[rule.source]} ${ref ?? '…'}`
      : SOURCE_SUBJECT[rule.source]
  const value = TIME_SOURCES.has(rule.source) ? formatClock(rule.value) : formatMinutes(rule.value)
  return `${subject} ${THRESHOLD_WORD[rule.threshold]} ${value}`
}

/** How a habit is checked: "You tick it", or "From your data: wake time before 07:00". */
export function checkLabel(rule: HabitRule): string {
  const line = sourceLine(rule)
  if (rule.check === 'manual' || line === null) return 'You tick it'
  // Bad (and Good, Neutral) is a screen-time label and keeps its capital mid-sentence.
  const keepsCapital = /^(Bad|Good|Neutral) /.test(line)
  return `From your data: ${keepsCapital ? line : line.charAt(0).toLowerCase() + line.slice(1)}`
}

/** The habit's one-line summary: how often · how it is checked · time of day. */
export function ruleSummary(habit: Pick<Habit, 'rule' | 'time_of_day'>): string {
  const parts = [frequencyLabel(habit.rule), checkLabel(habit.rule)]
  if (habit.time_of_day !== 'anytime') parts.push(TIME_OF_DAY_LABEL[habit.time_of_day])
  return parts.join(' · ')
}

/** Whether a habit is due on a day: a daily rule on its days; N× a week or a month every day. */
export function dueOn(
  rule: Pick<HabitRule, 'frequency' | 'weekdays'>,
  isoWeekday: number,
): boolean {
  if (rule.frequency !== 'specific_days') return true
  return (rule.weekdays ?? []).includes(isoWeekday)
}

export type TimeGroup = { id: TimeOfDay; label: string; habits: Habit[] }

/** Habits grouped Morning → Anytime, in list order; empty groups are dropped. */
export function timeGroups(habits: Habit[]): TimeGroup[] {
  return TIME_OF_DAY_ORDER.map((id) => ({
    id,
    label: TIME_OF_DAY_LABEL[id],
    habits: habits.filter((habit) => habit.time_of_day === id),
  })).filter((group) => group.habits.length > 0)
}
