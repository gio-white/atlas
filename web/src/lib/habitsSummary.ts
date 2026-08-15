import type { HabitStatus, Period } from './api'

export const HABIT_PERIODS: Period[] = ['day', 'week', 'month']

export const HABIT_PERIOD_META: Record<Period, { label: string; kicker: string }> = {
  day: { label: 'Daily', kicker: 'Show up every scheduled day.' },
  week: { label: 'Weekly', kicker: 'The target applies to the ISO week.' },
  month: { label: 'Monthly', kicker: 'The target applies to the calendar month.' },
}

export function parseHabitPeriod(raw: string | null): Period {
  if (raw === 'day' || raw === 'week' || raw === 'month') return raw
  return 'week'
}

export function flattenHabits(board: {
  day: HabitStatus[]
  week: HabitStatus[]
  month: HabitStatus[]
}): HabitStatus[] {
  return [...board.day, ...board.week, ...board.month]
}

export function groupHabitsByPeriod(habits: HabitStatus[]): Record<Period, HabitStatus[]> {
  const grouped: Record<Period, HabitStatus[]> = { day: [], week: [], month: [] }
  for (const habit of habits) {
    grouped[habit.period].push(habit)
  }
  return grouped
}

export function bucketProgress(current: number | null, target: number): number | null {
  if (current === null || target <= 0) return null
  return Math.min(1, Math.max(0, current / target))
}

export function summarizeHabits(habits: Pick<HabitStatus, 'scheduled' | 'satisfied'>[]): {
  scheduled: number
  satisfied: number
  fraction: number | null
} {
  const scheduled = habits.filter((habit) => habit.scheduled).length
  const satisfied = habits.filter((habit) => habit.scheduled && habit.satisfied).length
  return {
    scheduled,
    satisfied,
    fraction: scheduled === 0 ? null : satisfied / scheduled,
  }
}
