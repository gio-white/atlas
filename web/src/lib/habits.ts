import type { Habit, HabitKind, HabitStatus, Period, TimeOfDay } from './api'
import { formatMinutes } from './format'

export const TIME_OF_DAY_ORDER: TimeOfDay[] = ['morning', 'afternoon', 'evening', 'anytime']

export const TIME_OF_DAY_LABEL: Record<TimeOfDay, string> = {
  morning: 'Morning',
  afternoon: 'Afternoon',
  evening: 'Evening',
  anytime: 'Anytime',
}

export const KIND_META: Record<HabitKind, { label: string; hint: string }> = {
  check: { label: 'Yes / no', hint: 'Did it or didn’t: meditate, floss, call home.' },
  count: { label: 'Count', hint: 'A number to reach: pushups, pages, glasses of water.' },
  duration: { label: 'Time', hint: 'Minutes to put in: deep work, practice, reading.' },
  quit: { label: 'Quit', hint: 'Something to stop: count clean days, log slips.' },
}

export const WEEKDAY_SHORT = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

export type TimeGroup = { id: TimeOfDay; label: string; habits: HabitStatus[] }

/** Daily habits due today, grouped Morning → Anytime; empty groups are dropped. */
export function todayGroups(statuses: HabitStatus[]): TimeGroup[] {
  const due = statuses.filter((status) => status.period === 'day' && status.scheduled)
  return TIME_OF_DAY_ORDER.map((id) => ({
    id,
    label: TIME_OF_DAY_LABEL[id],
    habits: due.filter((status) => status.time_of_day === id),
  })).filter((group) => group.habits.length > 0)
}

/** Weekly and monthly habits, which read as progress over their period. */
export function periodHabits(statuses: HabitStatus[]): HabitStatus[] {
  return statuses.filter((status) => status.period !== 'day' && status.scheduled)
}

export function targetFor(status: HabitStatus): number {
  return status.effective_target ?? status.target_value
}

/** Share of the current target reached (or of a limit used), 0…1; null for quit habits. */
export function progressOf(status: HabitStatus): number | null {
  if (status.kind === 'quit') return null
  const target = targetFor(status)
  if (target <= 0) return null
  return Math.min(1, Math.max(0, (status.current_value ?? 0) / target))
}

/** A ceiling habit whose limit is already crossed. */
export function isOverLimit(status: HabitStatus): boolean {
  return status.comparator === 'at_most' && status.kind !== 'quit' && !status.satisfied
}

export function formatAmount(value: number | null, kind: HabitKind, unit: string | null): string {
  if (kind === 'duration') return value === null ? '0m' : formatMinutes(value)
  const number = value === null ? '0' : String(Math.round(value * 100) / 100)
  return unit ? `${number} ${unit}` : number
}

/** Buttons offered on a card for one-tap logging. */
export function quickAmounts(status: Pick<HabitStatus, 'kind' | 'target_value'>): number[] {
  if (status.kind === 'duration') return [5, 15, 30]
  if (status.kind !== 'count') return []
  const target = status.target_value
  if (target <= 5) return [1]
  const step = target >= 40 ? 10 : target >= 15 ? 5 : 2
  return [1, step]
}

export function frequencyLabel(
  habit: Pick<Habit, 'kind' | 'period' | 'target_value' | 'weekdays' | 'comparator'>,
): string {
  if (habit.kind === 'quit') return 'Every day'
  if (habit.period === 'day') return weekdaysLabel(habit.weekdays)
  const times = habit.kind === 'check' ? `${habit.target_value}×` : ''
  const per = habit.period === 'week' ? 'a week' : 'a month'
  return times ? `${times} ${per}` : `Every ${habit.period}`
}

export function weekdaysLabel(weekdays: number[] | null): string {
  if (weekdays === null || weekdays.length === 7) return 'Every day'
  const sorted = [...weekdays].sort((a, b) => a - b)
  if (sorted.join(',') === '1,2,3,4,5') return 'Weekdays'
  if (sorted.join(',') === '6,7') return 'Weekends'
  return sorted.map((day) => WEEKDAY_SHORT[day - 1]).join(', ')
}

export function goalLabel(
  status: Pick<HabitStatus, 'kind' | 'comparator' | 'target_value' | 'unit' | 'period'>,
): string {
  if (status.kind === 'quit') return 'Stay clean'
  if (status.kind === 'check' && status.period === 'day') return 'Do it'
  const amount = formatAmount(status.target_value, status.kind, status.unit)
  const verb =
    status.comparator === 'at_most' ? 'At most' : status.comparator === 'exactly' ? 'Exactly' : ''
  const per = PERIOD_WORD[status.period]
  return `${verb ? `${verb} ` : ''}${amount}${per}`
}

const PERIOD_WORD: Record<Period, string> = { day: '', week: ' this week', month: ' this month' }

export function daysLeftLabel(status: Pick<HabitStatus, 'days_left' | 'period'>): string {
  if (status.days_left === 0) return status.period === 'week' ? 'last day of the week' : 'last day'
  return status.days_left === 1 ? '1 day left' : `${status.days_left} days left`
}

export function streakLabel(
  status: Pick<HabitStatus, 'kind' | 'current_streak' | 'period'>,
): string {
  if (status.kind === 'quit') return `${streakCount(status, status.current_streak)} clean`
  const unit = status.period === 'day' ? 'day' : status.period
  return `${status.current_streak}-${unit} streak`
}

/** "19 days", "4 weeks", "1 month": a streak length on its own. */
export function streakCount(status: Pick<HabitStatus, 'kind' | 'period'>, count: number): string {
  const unit = status.kind === 'quit' || status.period === 'day' ? 'day' : status.period
  return `${count} ${unit}${count === 1 ? '' : 's'}`
}

export function todaySummary(statuses: HabitStatus[]): { due: number; done: number } {
  const due = statuses.filter(
    (status) => status.period === 'day' && status.scheduled && !status.excused,
  )
  return { due: due.length, done: due.filter((status) => status.satisfied).length }
}
