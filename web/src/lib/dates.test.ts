import { describe, expect, it } from 'vitest'

import { longDateLabel, shiftPeriodDate, weekdayLabel } from './dates'

describe('weekdayLabel', () => {
  it('labels an ISO local date without UTC shifting', () => {
    expect(weekdayLabel('2026-08-13')).toBe('Thu')
  })
})

describe('longDateLabel', () => {
  it('formats the mockup-style weekday date', () => {
    expect(longDateLabel('2026-08-14')).toBe('Friday, 14 August 2026')
  })
})

describe('shiftPeriodDate', () => {
  it('moves by day, week, and month', () => {
    expect(shiftPeriodDate('2026-08-14', 'day', -1)).toBe('2026-08-13')
    expect(shiftPeriodDate('2026-08-14', 'week', -1)).toBe('2026-08-07')
    expect(shiftPeriodDate('2026-03-31', 'month', -1)).toBe('2026-02-28')
  })
})
