import { describe, expect, it } from 'vitest'

import type { HabitStatus } from './api'
import {
  formatAmount,
  frequencyLabel,
  goalLabel,
  isOverLimit,
  periodHabits,
  progressOf,
  quickAmounts,
  streakCount,
  streakLabel,
  todayGroups,
  todaySummary,
} from './habits'

function status(overrides: Partial<HabitStatus> & Pick<HabitStatus, 'slug'>): HabitStatus {
  return {
    name: overrides.slug,
    metric_slug: overrides.slug,
    period: 'day',
    target_value: 1,
    comparator: 'at_least',
    current_streak: 0,
    longest_streak: 0,
    adherence: null,
    current_value: null,
    satisfied: false,
    scheduled: true,
    as_of: '2026-08-13',
    kind: 'check',
    time_of_day: 'anytime',
    unit: null,
    goal_slug: null,
    archived: false,
    bucket_start: '2026-08-13',
    bucket_end: '2026-08-13',
    days_left: 0,
    effective_target: 1,
    excused: false,
    skipped_today: false,
    today_value: null,
    last_entry_on: null,
    ...overrides,
  }
}

describe('todayGroups', () => {
  it('groups daily habits due today by time of day, in day order', () => {
    const groups = todayGroups([
      status({ slug: 'read', time_of_day: 'evening' }),
      status({ slug: 'stretch', time_of_day: 'morning' }),
      status({ slug: 'runs', period: 'week' }),
      status({ slug: 'gym', scheduled: false }),
    ])
    expect(groups.map((group) => [group.id, group.habits.map((h) => h.slug)])).toEqual([
      ['morning', ['stretch']],
      ['evening', ['read']],
    ])
    expect(periodHabits([status({ slug: 'runs', period: 'week' })])).toHaveLength(1)
  })

  it('counts done out of due, leaving skipped habits out', () => {
    expect(
      todaySummary([
        status({ slug: 'a', satisfied: true }),
        status({ slug: 'b' }),
        status({ slug: 'c', excused: true }),
      ]),
    ).toEqual({ due: 2, done: 1 })
  })
})

describe('progress and labels', () => {
  it('measures progress against the scaled target', () => {
    const runs = status({
      slug: 'runs',
      kind: 'count',
      period: 'week',
      target_value: 3,
      effective_target: 2,
      current_value: 1,
    })
    expect(progressOf(runs)).toBe(0.5)
    expect(progressOf(status({ slug: 'quit', kind: 'quit', comparator: 'at_most' }))).toBeNull()
    const coffee = status({
      slug: 'coffee',
      kind: 'count',
      comparator: 'at_most',
      current_value: 2,
      satisfied: false,
    })
    expect(progressOf(coffee)).toBe(1)
    expect(isOverLimit(coffee)).toBe(true)
  })

  it('formats amounts by kind', () => {
    expect(formatAmount(90, 'duration', 'min')).toBe('1h 30m')
    expect(formatAmount(12, 'count', 'pages')).toBe('12 pages')
    expect(formatAmount(null, 'count', null)).toBe('0')
  })

  it('offers quick amounts that fit the target', () => {
    expect(quickAmounts({ kind: 'count', target_value: 40 })).toEqual([1, 10])
    expect(quickAmounts({ kind: 'count', target_value: 3 })).toEqual([1])
    expect(quickAmounts({ kind: 'duration', target_value: 60 })).toEqual([5, 15, 30])
    expect(quickAmounts({ kind: 'check', target_value: 1 })).toEqual([])
  })

  it('describes frequency, goal, and streak in plain words', () => {
    const base = { comparator: 'at_least' as const }
    expect(
      frequencyLabel({
        ...base,
        kind: 'check',
        period: 'day',
        target_value: 1,
        weekdays: [1, 2, 3, 4, 5],
      }),
    ).toBe('Weekdays')
    expect(
      frequencyLabel({ ...base, kind: 'check', period: 'day', target_value: 1, weekdays: [1, 3] }),
    ).toBe('Mon, Wed')
    expect(
      frequencyLabel({ ...base, kind: 'check', period: 'week', target_value: 3, weekdays: null }),
    ).toBe('3× a week')
    expect(goalLabel(status({ slug: 'p', kind: 'count', target_value: 40, unit: 'reps' }))).toBe(
      '40 reps',
    )
    expect(
      goalLabel(status({ slug: 'c', kind: 'count', comparator: 'at_most', unit: 'cups' })),
    ).toBe('At most 1 cups')
    expect(streakLabel(status({ slug: 'q', kind: 'quit', current_streak: 1 }))).toBe('1 day clean')
    expect(streakCount({ kind: 'check', period: 'day' }, 19)).toBe('19 days')
    expect(streakLabel(status({ slug: 'r', period: 'week', current_streak: 4 }))).toBe(
      '4-week streak',
    )
  })
})
