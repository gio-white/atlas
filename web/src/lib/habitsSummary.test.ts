import { describe, expect, it } from 'vitest'

import type { HabitStatus } from './api'
import {
  bucketProgress,
  flattenHabits,
  groupHabitsByPeriod,
  parseHabitPeriod,
  summarizeHabits,
} from './habitsSummary'

function habit(
  overrides: Partial<HabitStatus> & Pick<HabitStatus, 'slug' | 'period'>,
): HabitStatus {
  return {
    name: overrides.slug,
    metric_slug: 'pushups',
    target_value: 1,
    comparator: 'at_least',
    current_streak: 0,
    longest_streak: 0,
    adherence: null,
    current_value: null,
    satisfied: false,
    scheduled: true,
    as_of: '2026-08-13',
    ...overrides,
  }
}

describe('parseHabitPeriod', () => {
  it('defaults to week and accepts day, week, month', () => {
    expect(parseHabitPeriod(null)).toBe('week')
    expect(parseHabitPeriod('day')).toBe('day')
    expect(parseHabitPeriod('month')).toBe('month')
    expect(parseHabitPeriod('nope')).toBe('week')
  })
})

describe('flattenHabits', () => {
  it('concatenates day, week, and month columns', () => {
    const rows = flattenHabits({
      day: [habit({ slug: 'daily', period: 'day' })],
      week: [habit({ slug: 'weekly', period: 'week' })],
      month: [habit({ slug: 'monthly', period: 'month' })],
    })
    expect(rows.map((item) => item.slug)).toEqual(['daily', 'weekly', 'monthly'])
  })
})

describe('bucketProgress', () => {
  it('clamps current over target', () => {
    expect(bucketProgress(3, 6)).toBeCloseTo(0.5)
    expect(bucketProgress(9, 6)).toBe(1)
    expect(bucketProgress(null, 6)).toBeNull()
    expect(bucketProgress(1, 0)).toBeNull()
  })
})

describe('groupHabitsByPeriod', () => {
  it('groups habits into day, week, and month', () => {
    const grouped = groupHabitsByPeriod([
      habit({ slug: 'monthly', period: 'month' }),
      habit({ slug: 'daily', period: 'day' }),
      habit({ slug: 'weekly', period: 'week' }),
      habit({ slug: 'also-daily', period: 'day' }),
    ])
    expect(grouped.day.map((item) => item.slug)).toEqual(['daily', 'also-daily'])
    expect(grouped.week.map((item) => item.slug)).toEqual(['weekly'])
    expect(grouped.month.map((item) => item.slug)).toEqual(['monthly'])
  })
})

describe('summarizeHabits', () => {
  it('counts scheduled and satisfied current buckets', () => {
    const summary = summarizeHabits([
      habit({ slug: 'a', period: 'day', scheduled: true, satisfied: true }),
      habit({ slug: 'b', period: 'day', scheduled: true, satisfied: false }),
      habit({ slug: 'c', period: 'week', scheduled: false, satisfied: false }),
    ])
    expect(summary.scheduled).toBe(2)
    expect(summary.satisfied).toBe(1)
    expect(summary.fraction).toBeCloseTo(0.5)
  })

  it('returns a null fraction when nothing is scheduled', () => {
    expect(summarizeHabits([]).fraction).toBeNull()
    expect(
      summarizeHabits([habit({ slug: 'off', period: 'day', scheduled: false })]).fraction,
    ).toBeNull()
  })
})
