import { describe, expect, it } from 'vitest'

import { weekdayLabel } from './dates'

describe('weekdayLabel', () => {
  it('labels an ISO local date without UTC shifting', () => {
    expect(weekdayLabel('2026-08-13')).toBe('Thu')
  })
})
