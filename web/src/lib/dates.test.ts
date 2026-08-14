import { describe, expect, it } from 'vitest'

import { longDateLabel, weekdayLabel } from './dates'

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
