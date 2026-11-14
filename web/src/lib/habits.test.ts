import { describe, expect, it } from 'vitest'

import type { Habit, HabitRule } from './api'
import {
  checkLabel,
  dueOn,
  frequencyLabel,
  ruleSummary,
  sourceLine,
  timeGroups,
  weekdaysLabel,
} from './habits'

function rule(overrides: Partial<HabitRule> = {}): HabitRule {
  return {
    starts_on: '2026-08-01',
    frequency: 'every_day',
    check: 'manual',
    weekdays: null,
    times: null,
    source: null,
    source_ref: null,
    source_ref_name: null,
    threshold: null,
    value: null,
    ...overrides,
  }
}

function habit(slug: string, overrides: Partial<Habit> = {}): Habit {
  return {
    id: 1,
    slug,
    name: slug,
    time_of_day: 'anytime',
    first_day: '2026-08-01',
    archived_at: null,
    rule: rule(),
    ...overrides,
  }
}

describe('frequencyLabel', () => {
  it('names each way a habit can repeat', () => {
    expect(frequencyLabel(rule())).toBe('Every day')
    expect(frequencyLabel(rule({ frequency: 'specific_days', weekdays: [5, 1, 3] }))).toBe(
      'Mon, Wed, Fri',
    )
    expect(frequencyLabel(rule({ frequency: 'times_a_week', times: 3 }))).toBe('3× a week')
    expect(frequencyLabel(rule({ frequency: 'times_a_month', times: 2 }))).toBe('2× a month')
  })

  it('shortens weekdays and weekends', () => {
    expect(weekdaysLabel([1, 2, 3, 4, 5])).toBe('Weekdays')
    expect(weekdaysLabel([7, 6])).toBe('Weekends')
    expect(weekdaysLabel(null)).toBe('Every day')
  })
})

describe('sourceLine', () => {
  it('reads a data rule as one line, in minutes or as a time of day', () => {
    const wake = rule({ check: 'data', source: 'wake_time', threshold: 'before', value: 420 })
    expect(sourceLine(wake)).toBe('Wake time before 07:00')
    const bad = { source: 'screen_bad_apps', threshold: 'at_most', value: 90 } as const
    expect(sourceLine(rule({ check: 'data', ...bad }))).toBe('Bad apps at most 1h 30m')
    const planned = { source: 'sessions_planned', threshold: 'before', value: 720 } as const
    expect(sourceLine(rule({ check: 'data', ...planned }))).toBe('A session planned before 12:00')
  })

  it('names the app or category a screen rule is on', () => {
    const app = rule({
      check: 'data',
      source: 'screen_app',
      source_ref: 'instagram',
      source_ref_name: 'Instagram',
      threshold: 'at_most',
      value: 30,
    })
    expect(sourceLine(app)).toBe('Screen time in Instagram at most 30m')
  })

  it('is empty for a habit you tick', () => {
    expect(sourceLine(rule())).toBeNull()
  })
})

describe('ruleSummary', () => {
  it('joins how often, how it is checked, and the time of day', () => {
    const wake = rule({ check: 'data', source: 'wake_time', threshold: 'before', value: 420 })
    expect(ruleSummary(habit('wake', { rule: wake, time_of_day: 'morning' }))).toBe(
      'Every day · From your data: wake time before 07:00 · Morning',
    )
    expect(ruleSummary(habit('read'))).toBe('Every day · You tick it')
    expect(checkLabel(rule())).toBe('You tick it')
    const bad = rule({ check: 'data', source: 'screen_bad_apps', threshold: 'at_most', value: 90 })
    expect(checkLabel(bad)).toBe('From your data: Bad apps at most 1h 30m')
  })
})

describe('dueOn and timeGroups', () => {
  it('shows a specific-days habit only on its days', () => {
    const weekdays = rule({ frequency: 'specific_days', weekdays: [1, 2, 3, 4, 5] })
    expect(dueOn(weekdays, 1)).toBe(true)
    expect(dueOn(weekdays, 6)).toBe(false)
    expect(dueOn(rule({ frequency: 'times_a_week', times: 3 }), 6)).toBe(true)
  })

  it('groups habits Morning to Anytime and drops empty groups', () => {
    const groups = timeGroups([
      habit('read', { time_of_day: 'evening' }),
      habit('run'),
      habit('wake', { time_of_day: 'morning' }),
    ])
    expect(groups.map((group) => group.id)).toEqual(['morning', 'evening', 'anytime'])
  })
})
