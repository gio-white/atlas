import { describe, expect, it } from 'vitest'

import type { Habit, HabitDayResult, HabitDayRow, HabitFreeze, HabitPeriod, HabitRule } from './api'
import {
  cellAction,
  checkLabel,
  dateRangeLabel,
  dayCountLabel,
  dayGroups,
  dayHeading,
  dayLine,
  dueOn,
  frequencyLabel,
  historyWeeks,
  keptFigure,
  mondayOf,
  ownDayFreeze,
  periodLabel,
  progressLabel,
  progressShare,
  reasonLine,
  rowActions,
  ruleSummary,
  shortDay,
  sourceLine,
  splitFreezes,
  streakFigure,
  streakLabel,
  stripSteps,
  timeGroups,
  weekdaysLabel,
  weekOfLabel,
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

  it('groups habits Morning to Any time and drops empty groups', () => {
    const groups = timeGroups([
      habit('read', { time_of_day: 'evening' }),
      habit('run'),
      habit('wake', { time_of_day: 'morning' }),
    ])
    expect(groups.map((group) => group.id)).toEqual(['morning', 'evening', 'anytime'])
  })
})

function result(overrides: Partial<HabitDayResult> = {}): HabitDayResult {
  return { day: '2026-11-14', status: 'open', reason: null, value: null, ...overrides }
}

function dayRow(h: Habit, r: Partial<HabitDayResult> = {}): HabitDayRow {
  return { habit: h, result: result(r), streak: { count: 0, period: 'day' }, progress: null }
}

const WAKE = rule({ check: 'data', source: 'wake_time', threshold: 'before', value: 420 })
const BAD_APPS = rule({
  check: 'data',
  source: 'screen_bad_apps',
  threshold: 'at_most',
  value: 90,
})

describe('Day tab words', () => {
  it('words streaks with the period, singular for one, and nothing for none', () => {
    expect(streakLabel({ count: 12, period: 'day' })).toBe('12 days')
    expect(streakLabel({ count: 1, period: 'day' })).toBe('1 day')
    expect(streakLabel({ count: 3, period: 'week' })).toBe('3 weeks')
    expect(streakLabel({ count: 1, period: 'month' })).toBe('1 month')
    expect(streakLabel({ count: 0, period: 'week' })).toBeNull()
  })

  it('words a weekly or monthly habit’s progress', () => {
    expect(progressLabel({ period: 'week', done: 2, target: 4 })).toBe('2 of 4 this week')
    expect(progressLabel({ period: 'month', done: 1, target: 2 })).toBe('1 of 2 this month')
    expect(progressLabel(null)).toBeNull()
  })

  it('heads the day and counts it', () => {
    expect(dayHeading('2026-11-14')).toBe('Saturday 14 Nov 2026')
    expect(dayCountLabel(3, 6)).toBe('3 of 6 done')
  })

  it('words every reason exactly', () => {
    const h = habit('wake', { rule: WAKE })
    expect(reasonLine(dayRow(h, { status: 'not_done', reason: 'no_data' }))).toBe(
      'No data received',
    )
    expect(reasonLine(dayRow(h, { status: 'not_done', reason: 'data_incomplete' }))).toBe(
      'Data incomplete',
    )
    expect(reasonLine(dayRow(h, { status: 'waiting', reason: 'waiting_for_data' }))).toBe(
      'Waiting for data',
    )
    expect(reasonLine(dayRow(h, { status: 'done', reason: 'set_by_you', value: 400 }))).toBe(
      'Set by you',
    )
    expect(reasonLine(dayRow(h, { status: 'frozen', reason: 'frozen' }))).toBe('Frozen')
    const bad = habit('bad', { rule: BAD_APPS })
    expect(reasonLine(dayRow(bad, { status: 'not_done', reason: 'over_limit' }))).toBe(
      'Over the limit',
    )
  })

  it('shows the reading behind a judged day and today’s screen time so far', () => {
    expect(reasonLine(dayRow(habit('wake', { rule: WAKE }), { status: 'done', value: 408 }))).toBe(
      '06:48 · from sleep',
    )
    const plan = habit('plan', {
      rule: rule({ check: 'data', source: 'sessions_planned', threshold: 'before', value: 720 }),
    })
    expect(reasonLine(dayRow(plan, { status: 'done', value: 490 }))).toBe(
      'Session planned at 08:10',
    )
    const bad = habit('bad', { rule: BAD_APPS })
    expect(reasonLine(dayRow(bad, { status: 'in_progress', value: 40 }))).toBe(
      'On track · 40m of 1h 30m',
    )
    expect(reasonLine(dayRow(bad, { status: 'done', value: 75 }))).toBe('1h 15m · from screen time')
    const atLeast = habit('learn', {
      rule: rule({ check: 'data', source: 'screen_category', threshold: 'at_least', value: 30 }),
    })
    expect(reasonLine(dayRow(atLeast, { status: 'in_progress', value: 20 }))).toBe('20 of 30m')
    expect(progressShare(dayRow(atLeast, { status: 'in_progress', value: 20 }))).toBeCloseTo(2 / 3)
    expect(
      reasonLine(dayRow(habit('wake', { rule: WAKE }), { status: 'not_done', value: 421 })),
    ).toBe('07:01 · from sleep')
    expect(reasonLine(dayRow(habit('read'), { status: 'open' }))).toBeNull()
    expect(reasonLine(dayRow(habit('wake', { rule: WAKE }), { status: 'open' }))).toBeNull()
  })
})

describe('Day tab row menu and strip', () => {
  it('offers only the actions that apply', () => {
    expect(rowActions(result({ status: 'open' }), false)).toEqual([
      'mark_done',
      'mark_not_done',
      'freeze',
      'open',
    ])
    expect(rowActions(result({ status: 'done', reason: 'set_by_you' }), false)).toEqual([
      'mark_not_done',
      'use_data',
      'freeze',
      'open',
    ])
    expect(rowActions(result({ status: 'not_done', reason: 'no_data' }), false)).toEqual([
      'mark_done',
      'freeze',
      'open',
    ])
    expect(rowActions(result({ status: 'frozen', reason: 'frozen' }), true)).toEqual([
      'unfreeze',
      'open',
    ])
    expect(rowActions(result({ status: 'frozen', reason: 'frozen' }), false)).toEqual(['open'])
  })

  it('unfreezes only the habit’s own one-day freeze', () => {
    const freeze = (id: number, h: string | null, start: string, end: string): HabitFreeze => ({
      id,
      habit: h,
      start_on: start,
      end_on: end,
      reason: null,
      created_at: '2026-11-01T00:00:00Z',
    })
    const freezes = [
      freeze(1, null, '2026-11-14', '2026-11-14'),
      freeze(2, 'run', '2026-11-13', '2026-11-15'),
      freeze(3, 'read', '2026-11-14', '2026-11-14'),
    ]
    expect(ownDayFreeze(freezes, 'read', '2026-11-14')?.id).toBe(3)
    expect(ownDayFreeze(freezes, 'run', '2026-11-14')).toBeUndefined()
    expect(ownDayFreeze(freezes, 'meditate', '2026-11-14')).toBeUndefined()
  })

  it('steps a week back, and forward no further than today', () => {
    expect(stripSteps('2026-11-14', '2026-11-09', '2026-11-14')).toEqual({
      previous: '2026-11-07',
      next: undefined,
    })
    expect(stripSteps('2026-11-05', '2026-11-02', '2026-11-14')).toEqual({
      previous: '2026-10-29',
      next: '2026-11-12',
    })
    expect(stripSteps('2026-11-07', '2026-11-02', '2026-11-12').next).toBe('2026-11-12')
  })

  it('groups by time of day, without headings when no habit has one', () => {
    const rows = [
      dayRow(habit('read', { time_of_day: 'evening' })),
      dayRow(habit('run')),
      dayRow(habit('wake', { time_of_day: 'morning' })),
    ]
    expect(dayGroups(rows).map((group) => group.label)).toEqual(['Morning', 'Evening', 'Any time'])
    const plain = dayGroups([dayRow(habit('run')), dayRow(habit('read'))])
    expect(plain).toHaveLength(1)
    expect(plain[0].label).toBeNull()
    expect(dayGroups([])).toEqual([])
  })
})

describe('Week tab and habit page words', () => {
  it('heads the week and words Habits kept', () => {
    expect(weekOfLabel('2026-11-09')).toBe('Week of 9 Nov 2026')
    expect(keptFigure({ done: 13, target: 16, share: 0.8125 })).toBe('81%')
    expect(keptFigure({ done: 0, target: 0, share: null })).toBe('—')
  })

  it('ticks a habit you tick from a cell, opens the menu otherwise, and leaves the rest alone', () => {
    expect(cellAction(result({ status: 'open' }), 'manual')).toBe('toggle')
    expect(cellAction(result({ status: 'blank' }), 'manual')).toBe('toggle')
    expect(cellAction(result({ status: 'frozen', reason: 'frozen' }), 'manual')).toBe('menu')
    expect(cellAction(result({ status: 'done' }), 'data')).toBe('menu')
    expect(cellAction(result({ status: 'not_scheduled' }), 'manual')).toBe('none')
    expect(cellAction(result({ status: 'upcoming' }), 'data')).toBe('none')
  })

  it('words days, streak figures, and date ranges', () => {
    expect(shortDay('2026-11-14')).toBe('Sat 14 Nov')
    expect(streakFigure(0, 'day')).toBe('0 days')
    expect(streakFigure(1, 'week')).toBe('1 week')
    expect(dateRangeLabel('2026-11-04', '2026-11-04')).toBe('4 Nov 2026')
    expect(dateRangeLabel('2026-11-13', '2026-11-15')).toBe('13–15 Nov 2026')
    expect(dateRangeLabel('2026-10-28', '2026-11-03')).toBe('28 Oct – 3 Nov 2026')
    expect(dateRangeLabel('2026-12-29', '2027-01-02')).toBe('29 Dec 2026 – 2 Jan 2027')
  })

  it('words a Recent days line, Blank days by their reason or "No tick"', () => {
    const wake = habit('wake', { rule: WAKE })
    expect(dayLine(dayRow(wake, { status: 'done', value: 408 }))).toBe('Done · 06:48 · from sleep')
    expect(dayLine(dayRow(wake, { status: 'not_done', reason: 'no_data' }))).toBe(
      'Not done · No data received',
    )
    expect(dayLine(dayRow(wake, { status: 'waiting', reason: 'waiting_for_data' }))).toBe(
      'Waiting for data',
    )
    expect(dayLine(dayRow(habit('read'), { status: 'frozen', reason: 'frozen' }))).toBe('Frozen')
    expect(dayLine(dayRow(habit('run'), { status: 'blank' }))).toBe('No tick')
    expect(dayLine(dayRow(wake, { status: 'blank', reason: 'no_data' }))).toBe('No data received')
  })

  it('labels history squares by their period', () => {
    const period = (overrides: Partial<HabitPeriod>): HabitPeriod => ({
      period: 'day',
      start: '2026-11-10',
      end: '2026-11-10',
      target: 1,
      done: 1,
      state: 'kept',
      ...overrides,
    })
    expect(periodLabel(period({}))).toBe('Tue 10 Nov: Done')
    expect(periodLabel(period({ state: 'missed', done: 0 }))).toBe('Tue 10 Nov: Not done')
    expect(
      periodLabel(
        period({ period: 'week', start: '2026-11-09', end: '2026-11-15', target: 3, done: 3 }),
      ),
    ).toBe('Week of 9 Nov 2026: Kept, 3 of 3')
    expect(
      periodLabel(
        period({
          period: 'month',
          start: '2026-11-01',
          end: '2026-11-30',
          target: 2,
          done: 1,
          state: 'running',
        }),
      ),
    ).toBe('November 2026: In progress, 1 of 2')
  })

  it('lays daily history out as Monday-first weeks', () => {
    expect(mondayOf('2026-11-14')).toBe('2026-11-09')
    expect(mondayOf('2026-11-09')).toBe('2026-11-09')
    const kept: HabitPeriod = {
      period: 'day',
      start: '2026-11-03',
      end: '2026-11-03',
      target: 1,
      done: 1,
      state: 'kept',
    }
    const weeks = historyWeeks([kept], '2026-11-02', '2026-11-14')
    expect(weeks).toHaveLength(2)
    expect(weeks[0].map((cell) => cell.day)).toEqual([
      '2026-11-02',
      '2026-11-03',
      '2026-11-04',
      '2026-11-05',
      '2026-11-06',
      '2026-11-07',
      '2026-11-08',
    ])
    expect(weeks[0][1].period).toBe(kept)
    expect(weeks[1][0].period).toBeNull()
  })

  it('splits freezes into upcoming (soonest first) and past (latest first)', () => {
    const freeze = (id: number, start: string, end: string): HabitFreeze => ({
      id,
      habit: 'run',
      start_on: start,
      end_on: end,
      reason: null,
      created_at: '2026-11-01T00:00:00Z',
    })
    const { upcoming, past } = splitFreezes(
      [
        freeze(1, '2026-10-01', '2026-10-03'),
        freeze(2, '2026-11-20', '2026-11-22'),
        freeze(3, '2026-11-13', '2026-11-15'),
        freeze(4, '2026-11-04', '2026-11-04'),
      ],
      '2026-11-14',
    )
    expect(upcoming.map((item) => item.id)).toEqual([3, 2])
    expect(past.map((item) => item.id)).toEqual([4, 1])
  })
})
