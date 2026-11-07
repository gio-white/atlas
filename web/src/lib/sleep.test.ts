import { describe, expect, it } from 'vitest'

import type { SleepNight, SleepView } from './api'
import {
  asleepAxis,
  consistencyLabel,
  daysNewestFirst,
  formatClock,
  formatSpread,
  parseSleepRange,
  rangeDays,
  stageShares,
  weekAxis,
} from './sleep'

function night(bed: number, wake: number): SleepNight {
  return {
    date: '2026-08-13',
    session_id: 1,
    started_at: '2026-08-12T23:00:00Z',
    ended_at: '2026-08-13T07:00:00Z',
    bed_offset: bed,
    wake_offset: wake,
    in_bed_minutes: wake - bed,
    asleep_minutes: wake - bed,
    stages: { awake: 0, rem: 0, light: 0, deep: 0 },
    segments: [],
  }
}

function view(nights: (SleepNight | null)[]): SleepView {
  return {
    as_of: '2026-08-13',
    range_start: '2026-08-07',
    range_end: '2026-08-13',
    night: nights.at(-1) ?? null,
    days: nights.map((item, index) => ({ date: `2026-08-${7 + index}`, night: item })),
    nights_logged: nights.filter(Boolean).length,
    average_asleep: null,
    average_bed_offset: null,
    average_wake_offset: null,
    average_stages: null,
    bed_spread: null,
    wake_spread: null,
    last_recorded_at: null,
  }
}

describe('formatClock', () => {
  it('wraps offsets before midnight onto the previous evening', () => {
    expect(formatClock(-50)).toBe('23:10')
    expect(formatClock(425)).toBe('07:05')
    expect(formatClock(0)).toBe('00:00')
    expect(formatClock(null)).toBe('—')
  })
})

describe('stageShares', () => {
  it('returns every stage in display order with its share', () => {
    const shares = stageShares({ awake: 30, rem: 90, light: 240, deep: 120 })
    expect(shares.map((item) => item.stage)).toEqual(['deep', 'light', 'rem', 'awake'])
    expect(shares[0].share).toBeCloseTo(0.25)
  })

  it('keeps shares at zero when nothing was recorded', () => {
    expect(stageShares({ awake: 0, rem: 0, light: 0, deep: 0 })[0].share).toBe(0)
  })
})

describe('weekAxis', () => {
  it('spans the earliest bedtime to the latest wake on whole hours', () => {
    const axis = weekAxis(view([night(-90, 400), null, night(30, 545)]))
    expect(axis.start).toBe(-120)
    expect(axis.end).toBe(600)
    expect(axis.ticks).toEqual([-120, 0, 120, 240, 360, 480, 600])
  })

  it('falls back to a default window with no nights', () => {
    const axis = weekAxis(view([null, null]))
    expect(axis.start).toBe(-120)
    expect(axis.end).toBe(480)
  })
})

describe('ranges', () => {
  it('parses known ranges and falls back to a week', () => {
    expect(parseSleepRange('quarter')).toBe('quarter')
    expect(parseSleepRange('year')).toBe('week')
    expect(parseSleepRange(null)).toBe('week')
    expect(rangeDays('month')).toBe(30)
    expect(rangeDays('quarter')).toBe(90)
  })
})

describe('consistency', () => {
  it('formats a spread in minutes or hours', () => {
    expect(formatSpread(null)).toBe('—')
    expect(formatSpread(24.6)).toBe('±25m')
    expect(formatSpread(60)).toBe('±1h')
    expect(formatSpread(95)).toBe('±1h 35m')
  })

  it('names the spread in plain words', () => {
    expect(consistencyLabel(null)).toBe('Needs two nights')
    expect(consistencyLabel(20)).toBe('Steady')
    expect(consistencyLabel(45)).toBe('Varies a little')
    expect(consistencyLabel(90)).toBe('Irregular')
  })
})

describe('asleepAxis', () => {
  it('reaches at least eight hours and rounds up to two-hour ticks', () => {
    expect(asleepAxis(view([null])).ticks).toEqual([0, 120, 240, 360, 480])
    expect(asleepAxis(view([night(-60, 570)])).max).toBe(720)
  })
})

describe('daysNewestFirst', () => {
  it('keeps the days without a night', () => {
    const days = daysNewestFirst(view([night(-60, 420), null]))
    expect(days.map((day) => day.night === null)).toEqual([true, false])
  })
})
