import { describe, expect, it } from 'vitest'

import { lastUpdatedLabel } from './freshness'

const NOW = new Date(2026, 10, 7, 15, 0)

function at(day: number, hour: number, minute = 0): string {
  return new Date(2026, 10, day, hour, minute).toISOString()
}

describe('lastUpdatedLabel', () => {
  it('is null without a record', () => {
    expect(lastUpdatedLabel(null, NOW)).toBeNull()
    expect(lastUpdatedLabel('not a date', NOW)).toBeNull()
  })

  it('reads recent records in minutes', () => {
    expect(lastUpdatedLabel(at(7, 14, 59), NOW)).toBe('Last updated 1 min ago')
    expect(lastUpdatedLabel(new Date(NOW.getTime() - 10_000).toISOString(), NOW)).toBe(
      'Last updated just now',
    )
  })

  it('names today, yesterday, and older days', () => {
    expect(lastUpdatedLabel(at(7, 9, 5), NOW)).toBe('Last updated today at 09:05')
    expect(lastUpdatedLabel(at(6, 22, 30), NOW)).toBe('Last updated yesterday at 22:30')
    expect(lastUpdatedLabel(at(2, 8, 0), NOW)).toBe('Last updated 2 Nov 2026 at 08:00')
  })
})
