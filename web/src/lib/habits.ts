import type {
  Habit,
  HabitDayReason,
  HabitDayResult,
  HabitDayRow,
  HabitDayStatus,
  HabitFreeze,
  HabitProgress,
  HabitRule,
  HabitSource,
  HabitStreak,
  HabitThreshold,
  Period,
  TimeOfDay,
} from './api'
import { dayLabel, parseIsoDate, shiftPeriodDate } from './dates'
import { formatMinutes } from './format'
import { formatClock } from './sleep'

export const TIME_OF_DAY_ORDER: TimeOfDay[] = ['morning', 'afternoon', 'evening', 'anytime']

export const TIME_OF_DAY_LABEL: Record<TimeOfDay, string> = {
  morning: 'Morning',
  afternoon: 'Afternoon',
  evening: 'Evening',
  anytime: 'Any time',
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

/** Habits grouped Morning → Any time, in list order; empty groups are dropped. */
export function timeGroups(habits: Habit[]): TimeGroup[] {
  return TIME_OF_DAY_ORDER.map((id) => ({
    id,
    label: TIME_OF_DAY_LABEL[id],
    habits: habits.filter((habit) => habit.time_of_day === id),
  })).filter((group) => group.habits.length > 0)
}

const PERIOD_UNIT: Record<Period, [string, string]> = {
  day: ['day', 'days'],
  week: ['week', 'weeks'],
  month: ['month', 'months'],
}

/** "12 days", "1 week", "2 months"; null for no streak, which shows nothing. */
export function streakLabel(streak: HabitStreak): string | null {
  if (streak.count <= 0) return null
  const [one, many] = PERIOD_UNIT[streak.period]
  return `${streak.count} ${streak.count === 1 ? one : many}`
}

/** "2 of 4 this week", "1 of 2 this month"; null for a daily habit. */
export function progressLabel(progress: HabitProgress | null): string | null {
  if (progress === null || progress.period === 'day') return null
  return `${progress.done} of ${progress.target} this ${progress.period}`
}

/** "3 of 6 done": the day's scheduled habits that are not frozen, and how many are Done. */
export function dayCountLabel(done: number, total: number): string {
  return `${done} of ${total} done`
}

/** "Saturday 14 Nov 2026", the Day tab's heading. */
export function dayHeading(isoDate: string): string {
  const date = parseIsoDate(isoDate)
  const weekday = date.toLocaleDateString('en-GB', { weekday: 'long' })
  return `${weekday} ${dayLabel(isoDate)}`
}

const REASON_LABEL: Record<HabitDayReason, string> = {
  no_data: 'No data received',
  data_incomplete: 'Data incomplete',
  waiting_for_data: 'Waiting for data',
  over_limit: 'Over the limit',
  set_by_you: 'Set by you',
  frozen: 'Frozen',
}

const SLEEP_SOURCES: ReadonlySet<HabitSource> = new Set(['wake_time', 'bedtime', 'time_asleep'])

/** "20 of 30m" under an hour, else "1h 10m of 1h 30m". */
function minutesOf(value: number, limit: number): string {
  if (Math.round(value) < 60 && Math.round(limit) < 60) {
    return `${Math.max(0, Math.round(value))} of ${formatMinutes(limit)}`
  }
  return `${formatMinutes(value)} of ${formatMinutes(limit)}`
}

/** The line under a habit's name on the Day tab, or null when there is nothing to say: a reason
 * ("No data received", "Set by you", "Frozen"), today's screen time so far ("On track · 40m of
 * 1h 30m", "20 of 30m"), or the reading behind a judged day ("06:48 · from sleep", "Session planned
 * at 08:10", "40m · from screen time"). */
export function reasonLine(row: Pick<HabitDayRow, 'habit' | 'result'>): string | null {
  const { result } = row
  const { rule } = row.habit
  if (result.reason !== null) return REASON_LABEL[result.reason]
  const value = result.value
  if (rule.check !== 'data' || rule.source === null || value === null) return null
  if (result.status === 'in_progress' && rule.value !== null) {
    const figure = minutesOf(value, rule.value)
    return rule.threshold === 'at_most' ? `On track · ${figure}` : figure
  }
  if (result.status !== 'done' && result.status !== 'not_done' && result.status !== 'blank') {
    return null
  }
  if (rule.source === 'sessions_planned') {
    return value < 0
      ? `Session planned the day before at ${formatClock(value)}`
      : `Session planned at ${formatClock(value)}`
  }
  if (SLEEP_SOURCES.has(rule.source)) {
    const reading = rule.source === 'time_asleep' ? formatMinutes(value) : formatClock(value)
    return `${reading} · from sleep`
  }
  return `${formatMinutes(value)} · from screen time`
}

/** How far today's screen time is towards the rule's value, for the In progress ring. */
export function progressShare(row: Pick<HabitDayRow, 'habit' | 'result'>): number {
  const limit = row.habit.rule.value
  const value = row.result.value
  if (limit === null || value === null || limit <= 0) return 0
  return Math.min(1, Math.max(0, value / limit))
}

export type RowAction = 'mark_done' | 'mark_not_done' | 'use_data' | 'freeze' | 'unfreeze' | 'open'

/** The freeze a row's Unfreeze removes: only this habit's own one-day freeze on the day. A longer
 * freeze, or one for every habit, is not undone from a single row. */
export function ownDayFreeze(
  freezes: HabitFreeze[],
  slug: string,
  day: string,
): HabitFreeze | undefined {
  return freezes.find(
    (freeze) => freeze.habit === slug && freeze.start_on === day && freeze.end_on === day,
  )
}

/** The row menu's actions, only those that apply: Mark done · Mark not done · Use data again
 * (when set by you) · Freeze this day / Unfreeze · Open habit. A frozen day takes no answer (a
 * freeze wins over a mark). */
export function rowActions(result: HabitDayResult, canUnfreeze: boolean): RowAction[] {
  if (result.status === 'frozen') return canUnfreeze ? ['unfreeze', 'open'] : ['open']
  const actions: RowAction[] = []
  if (result.status !== 'done') actions.push('mark_done')
  if (result.status !== 'not_done') actions.push('mark_not_done')
  if (result.reason === 'set_by_you') actions.push('use_data')
  actions.push('freeze', 'open')
  return actions
}

export const ROW_ACTION_LABEL: Record<RowAction, string> = {
  mark_done: 'Mark done',
  mark_not_done: 'Mark not done',
  use_data: 'Use data again',
  freeze: 'Freeze this day',
  unfreeze: 'Unfreeze',
  open: 'Open habit',
}

/** The status in words, for screen readers and the icon's label. */
export const DAY_STATUS_LABEL: Record<HabitDayStatus, string> = {
  not_scheduled: 'Not scheduled',
  upcoming: 'Upcoming',
  frozen: 'Frozen',
  done: 'Done',
  not_done: 'Not done',
  open: 'Not done yet',
  in_progress: 'In progress',
  waiting: 'Waiting for data',
  blank: 'Not done',
}

/** The week strip's arrows: the same weekday a week earlier, and a week later up to today (none
 * once the next week starts after today). */
export function stripSteps(
  selected: string,
  weekStart: string,
  today: string,
): { previous: string; next: string | undefined } {
  const nextMonday = shiftPeriodDate(weekStart, 'week', 1)
  const later = shiftPeriodDate(selected, 'week', 1)
  return {
    previous: shiftPeriodDate(selected, 'week', -1),
    next: nextMonday > today ? undefined : later > today ? today : later,
  }
}

/** Habits on the Day tab grouped Morning → Any time; empty groups dropped. One group without a
 * heading when no habit shown has a time of day. */
export function dayGroups(
  rows: HabitDayRow[],
): { id: TimeOfDay; label: string | null; rows: HabitDayRow[] }[] {
  if (rows.every((row) => row.habit.time_of_day === 'anytime')) {
    return rows.length === 0 ? [] : [{ id: 'anytime', label: null, rows }]
  }
  return TIME_OF_DAY_ORDER.map((id) => ({
    id,
    label: TIME_OF_DAY_LABEL[id],
    rows: rows.filter((row) => row.habit.time_of_day === id),
  })).filter((group) => group.rows.length > 0)
}
