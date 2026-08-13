import { describe, expect, it } from 'vitest'

import { formatComparator, formatEntryValue, formatPace, formatPercent } from './format'
import { todayIso } from './utils'

describe('format helpers', () => {
  it('maps comparators and pace labels', () => {
    expect(formatComparator('at_least')).toBe('≥')
    expect(formatPace('on_track')).toBe('on track')
    expect(formatPercent(0.42)).toBe('42%')
    expect(formatPercent(null)).toBe('—')
  })

  it('formats entry values by stored field', () => {
    expect(formatEntryValue(null, true, null)).toBe('yes')
    expect(formatEntryValue(40, null, null)).toBe('40')
    expect(formatEntryValue(null, null, 'ok')).toBe('ok')
  })
})

describe('todayIso', () => {
  it('formats a local date as YYYY-MM-DD', () => {
    expect(todayIso(new Date(2026, 7, 13))).toBe('2026-08-13')
  })
})
