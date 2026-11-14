import { describe, expect, it } from 'vitest'

import {
  clockChange,
  countChange,
  minutesChange,
  shareChange,
  weekRangeLine,
  weekSteps,
  weekTitle,
} from './thisWeek'

// Thursday 12 Nov 2026; its week runs Monday 9 to Sunday 15 Nov.
const TODAY = '2026-11-12'

describe('weekTitle and weekRangeLine', () => {
  it('names the week holding today "This week" and others by their Monday', () => {
    expect(weekTitle('2026-11-09', TODAY)).toBe('This week')
    expect(weekTitle('2026-11-02', TODAY)).toBe('Week of 2 Nov 2026')
  })

  it('says how far a week in progress is counted', () => {
    expect(weekRangeLine('2026-11-09', TODAY, false)).toBe('9–15 Nov 2026 · up to Thu 12 Nov')
    expect(weekRangeLine('2026-11-02', '2026-11-08', true)).toBe('2–8 Nov 2026')
  })
})

describe('weekSteps', () => {
  it('steps to whole weeks by their Sunday, and back to no date for this week', () => {
    expect(weekSteps('2026-11-09', TODAY)).toEqual({ previous: '2026-11-08', next: undefined })
    expect(weekSteps('2026-11-02', TODAY)).toEqual({ previous: '2026-11-01', next: null })
    expect(weekSteps('2026-10-26', TODAY)).toEqual({ previous: '2026-10-25', next: '2026-11-08' })
  })
})

describe('changes from last week', () => {
  it('words minutes, counts, shares, and times of day', () => {
    expect(minutesChange(410, 375)).toBe('+35m vs last week')
    expect(minutesChange(300, 380)).toBe('−1h 20m vs last week')
    expect(minutesChange(300, null)).toBeNull()
    expect(countChange(6, 4)).toBe('+2 vs last week')
    expect(countChange(3, 3)).toBe('Same as last week')
    expect(shareChange(0.82, 0.77)).toBe('+5 points vs last week')
    expect(shareChange(0.5, 0.51)).toBe('−1 point vs last week')
    expect(clockChange(-20, -40)).toBe('20m later than last week')
    expect(clockChange(400, 430)).toBe('30m earlier than last week')
  })
})
