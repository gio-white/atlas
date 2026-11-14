import type { Habit, HabitDayResult, HabitRule } from '@/lib/api'

/** Shared habits for the Habits page tests. */
export const MANUAL: HabitRule = {
  starts_on: '2026-11-01',
  frequency: 'every_day',
  check: 'manual',
  weekdays: null,
  times: null,
  source: null,
  source_ref: null,
  source_ref_name: null,
  threshold: null,
  value: null,
}

export function habit(slug: string, name: string, overrides: Partial<Habit> = {}): Habit {
  return {
    id: 1,
    slug,
    name,
    time_of_day: 'anytime',
    first_day: '2026-11-01',
    archived_at: null,
    rule: MANUAL,
    ...overrides,
  }
}

export function dayResult(
  day: string,
  status: HabitDayResult['status'],
  overrides: Partial<HabitDayResult> = {},
): HabitDayResult {
  return { day, status, reason: null, value: null, ...overrides }
}

export const WAKE = habit('wake', 'Wake up early', {
  time_of_day: 'morning',
  rule: { ...MANUAL, check: 'data', source: 'wake_time', threshold: 'before', value: 420 },
})

export const READ = habit('read', 'Read 30 minutes')

export const WEEK_DAYS = [
  '2026-11-09',
  '2026-11-10',
  '2026-11-11',
  '2026-11-12',
  '2026-11-13',
  '2026-11-14',
  '2026-11-15',
]
