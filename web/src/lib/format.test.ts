import { describe, expect, it } from 'vitest'

import {
  formatComparator,
  formatDeltaFraction,
  formatEntryValue,
  formatMinutes,
  formatPace,
  formatPercent,
} from './format'
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

  it('formats duration minutes as hours and minutes', () => {
    expect(formatMinutes(275)).toBe('4h 35m')
    expect(formatMinutes(60)).toBe('1h')
    expect(formatMinutes(12)).toBe('12m')
    expect(formatMinutes(null)).toBe('—')
  })

  it('formats a signed percent delta', () => {
    expect(formatDeltaFraction(-1 / 3)).toBe('↓ 33%')
    expect(formatDeltaFraction(0.12)).toBe('↑ 12%')
    expect(formatDeltaFraction(null)).toBeNull()
  })
})

describe('todayIso', () => {
  it('formats a local date as YYYY-MM-DD', () => {
    expect(todayIso(new Date(2026, 7, 13))).toBe('2026-08-13')
  })
})
