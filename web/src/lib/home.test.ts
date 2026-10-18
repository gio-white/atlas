import { describe, expect, it } from 'vitest'

import type { ScreenDashboard, TaskItem, WeekHabit } from './api'
import { habitCellState, habitWeekSummary, screenHeadline, screenRows, visibleTasks } from './home'

function dashboard(overrides: Partial<ScreenDashboard> = {}): ScreenDashboard {
  return {
    period: 'week',
    as_of: '2026-08-13',
    range_start: '2026-08-10',
    range_end: '2026-08-13',
    previous_start: '2026-08-03',
    previous_end: '2026-08-06',
    total: 400,
    daily_average: 100,
    longest_day: null,
    delta_minutes: null,
    delta_fraction: null,
    score: null,
    score_band: null,
    judgments: { useful: 0, waste: 0, neutral: 0, total: 0 },
    apps: [],
    categories: [
      { slug: 'social', name: 'Social', judgment: 'waste', minutes: 240, share: 0.6, apps: [] },
      {
        slug: 'learning',
        name: 'Learning',
        judgment: 'useful',
        minutes: 160,
        share: 0.4,
        apps: [],
      },
    ],
    devices: [{ slug: 'iphone', name: 'iPhone', minutes: 400, share: 1 }],
    daily: [],
    comparison: [],
    hours: [],
    trend: [],
    insights: [],
    budgets: [],
    ...overrides,
  } as ScreenDashboard
}

function task(overrides: Partial<TaskItem> & Pick<TaskItem, 'id'>): TaskItem {
  return {
    title: `Task ${overrides.id}`,
    bucket: 'today',
    due_on: null,
    due_at: null,
    priority: 'normal',
    goal: null,
    done_at: null,
    created_at: '2026-08-10T12:00:00',
    ...overrides,
  }
}

function habit(overrides: Partial<WeekHabit> = {}): WeekHabit {
  return {
    slug: 'meditate',
    name: 'Meditate',
    metric_slug: 'meditated',
    period: 'day',
    target_value: 1,
    comparator: 'at_least',
    current_value: null,
    satisfied: false,
    current_streak: 2,
    days: [
      { day: '2026-08-10', scheduled: true, value: 1, satisfied: true },
      { day: '2026-08-11', scheduled: true, value: null, satisfied: false },
      { day: '2026-08-12', scheduled: false, value: null, satisfied: null },
      { day: '2026-08-13', scheduled: true, value: null, satisfied: false },
      { day: '2026-08-14', scheduled: true, value: null, satisfied: null },
    ],
    ...overrides,
  }
}

describe('screenRows', () => {
  it('divides week minutes by the elapsed days for a daily average', () => {
    const rows = screenRows(dashboard(), 'category', 'week')
    expect(rows).toEqual([
      { slug: 'social', name: 'Social', minutes: 60 },
      { slug: 'learning', name: 'Learning', minutes: 40 },
    ])
  })

  it('reads the chosen split as-is for a day', () => {
    expect(screenRows(dashboard(), 'device', 'day')).toEqual([
      { slug: 'iphone', name: 'iPhone', minutes: 400 },
    ])
    expect(screenRows(dashboard(), 'app', 'day')).toEqual([])
    expect(screenRows(null, 'app', 'day')).toEqual([])
  })

  it('headlines the total for a day and the daily average for a week', () => {
    expect(screenHeadline(dashboard(), 'day')).toBe(400)
    expect(screenHeadline(dashboard(), 'week')).toBe(100)
  })
})

describe('visibleTasks', () => {
  it('hides tasks finished before today and lists open tasks first', () => {
    const rows = visibleTasks(
      [
        task({ id: 1, done_at: '2026-08-13T09:00:00' }),
        task({ id: 2 }),
        task({ id: 3, done_at: '2026-08-01T09:00:00' }),
      ],
      '2026-08-13',
    )
    expect(rows.map((row) => row.id)).toEqual([2, 1])
  })
})

describe('habitCellState', () => {
  it('maps a daily habit week onto confirm states', () => {
    const item = habit()
    expect(item.days.map((cell) => habitCellState(item, cell, '2026-08-13'))).toEqual([
      'done',
      'missed',
      'off',
      'open',
      'future',
    ])
  })

  it('marks any logged day as done for a weekly habit', () => {
    const item = habit({
      period: 'week',
      days: [
        { day: '2026-08-10', scheduled: true, value: 1, satisfied: null },
        { day: '2026-08-11', scheduled: true, value: null, satisfied: null },
      ],
    })
    expect(item.days.map((cell) => habitCellState(item, cell, '2026-08-13'))).toEqual([
      'done',
      'open',
    ])
  })
})

describe('habitWeekSummary', () => {
  it('counts confirmed scheduled days so far for daily habits', () => {
    expect(habitWeekSummary(habit(), '2026-08-13')).toBe('1/3 this week · streak 2')
  })

  it('shows bucket progress for weekly habits', () => {
    expect(
      habitWeekSummary(habit({ period: 'week', current_value: 2, target_value: 3 }), '2026-08-13'),
    ).toBe('2/3 this week')
  })
})
