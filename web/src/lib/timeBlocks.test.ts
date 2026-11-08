import { afterAll, beforeAll, describe, expect, it } from 'vitest'

import {
  addMinutesToTime,
  assignLanes,
  dayPlacement,
  END_BEFORE_START,
  formatTimeRange,
  inputMinutes,
  localToUtc,
  markOutcomeLearned,
  nextHalfHour,
  outcomeLearned,
  pathLabel,
  utcToLocal,
  WINDOW_INCOMPLETE,
  weekDays,
  weekLabel,
  weekRangeUtc,
  weekStart,
  windowError,
} from './timeBlocks'

// Node reads TZ when a Date is formatted, so pinning it here makes the local ↔ UTC
// conversions deterministic (Copenhagen: UTC+1 in winter, UTC+2 in summer).
const env = (globalThis as unknown as { process: { env: Record<string, string | undefined> } })
  .process.env
const previousTz = env.TZ
beforeAll(() => {
  env.TZ = 'Europe/Copenhagen'
})
afterAll(() => {
  env.TZ = previousTz
})

describe('local ↔ UTC', () => {
  it('converts local inputs to the UTC instant the API stores', () => {
    expect(localToUtc('2026-11-09', '09:30')).toBe('2026-11-09T08:30:00.000Z')
    expect(localToUtc('2026-07-01', '09:30')).toBe('2026-07-01T07:30:00.000Z')
  })

  it('reads API instants back as local date and time', () => {
    expect(utcToLocal('2026-11-08T23:30:00Z')).toEqual({ date: '2026-11-09', time: '00:30' })
    expect(utcToLocal('2026-07-01T07:30:00Z')).toEqual({ date: '2026-07-01', time: '09:30' })
  })

  it('round-trips', () => {
    const { date, time } = utcToLocal(localToUtc('2026-03-29', '04:15'))
    expect({ date, time }).toEqual({ date: '2026-03-29', time: '04:15' })
  })

  it('formats a local time range', () => {
    expect(formatTimeRange('2026-11-08T09:00:00Z', '2026-11-08T10:30:00Z')).toBe('10:00–11:30')
  })
})

describe('window validation', () => {
  it('needs every field', () => {
    expect(windowError('', '09:00', '10:00')).toBe(WINDOW_INCOMPLETE)
    expect(windowError('2026-11-09', '09:00', '')).toBe(WINDOW_INCOMPLETE)
  })

  it('refuses an end at or before the start', () => {
    expect(windowError('2026-11-09', '10:00', '10:00')).toBe(END_BEFORE_START)
    expect(windowError('2026-11-09', '10:00', '09:00')).toBe(END_BEFORE_START)
    expect(windowError('2026-11-09', '09:00', '09:45')).toBeNull()
  })

  it('measures the duration', () => {
    expect(inputMinutes('2026-11-09', '09:00', '10:30')).toBe(90)
  })
})

describe('weeks', () => {
  it('starts on Monday', () => {
    expect(weekStart('2026-11-08')).toBe('2026-11-02') // Sunday → previous Monday
    expect(weekStart('2026-11-09')).toBe('2026-11-09')
    expect(weekDays('2026-11-09')).toEqual([
      '2026-11-09',
      '2026-11-10',
      '2026-11-11',
      '2026-11-12',
      '2026-11-13',
      '2026-11-14',
      '2026-11-15',
    ])
  })

  it('asks the API for the local week in UTC', () => {
    expect(weekRangeUtc('2026-11-09')).toEqual({
      start: '2026-11-08T23:00:00.000Z',
      end: '2026-11-15T23:00:00.000Z',
    })
  })

  it('labels a week', () => {
    expect(weekLabel('2026-11-09')).toBe('9–15 Nov 2026')
    expect(weekLabel('2026-11-30')).toBe('30 Nov – 6 Dec 2026')
  })
})

describe('day placement', () => {
  it('places a block by local minutes from midnight', () => {
    // 09:00–10:30 UTC is 10:00–11:30 in Copenhagen.
    expect(dayPlacement('2026-11-09T09:00:00Z', '2026-11-09T10:30:00Z', '2026-11-09')).toEqual({
      top: 600,
      height: 90,
    })
    expect(dayPlacement('2026-11-09T09:00:00Z', '2026-11-09T10:30:00Z', '2026-11-10')).toBeNull()
  })

  it('clips a block across midnight into both days', () => {
    const start = '2026-11-09T22:00:00Z' // 23:00 local
    const end = '2026-11-10T00:00:00Z' // 01:00 local
    expect(dayPlacement(start, end, '2026-11-09')).toEqual({ top: 1380, height: 60 })
    expect(dayPlacement(start, end, '2026-11-10')).toEqual({ top: 0, height: 60 })
  })

  it('puts intersecting blocks in side-by-side lanes', () => {
    const lanes = assignLanes([
      { id: 1, top: 540, height: 60 },
      { id: 2, top: 570, height: 60 },
      { id: 3, top: 720, height: 30 },
    ])
    expect(lanes.get(1)).toEqual({ lane: 0, lanes: 2 })
    expect(lanes.get(2)).toEqual({ lane: 1, lanes: 2 })
    expect(lanes.get(3)).toEqual({ lane: 0, lanes: 1 })
  })
})

describe('defaults and labels', () => {
  it('suggests the next half hour', () => {
    expect(nextHalfHour(new Date(2026, 10, 9, 9, 10))).toEqual({
      date: '2026-11-09',
      time: '09:30',
    })
    expect(nextHalfHour(new Date(2026, 10, 9, 23, 40))).toEqual({
      date: '2026-11-10',
      time: '00:00',
    })
  })

  it('adds minutes without spilling past midnight', () => {
    expect(addMinutesToTime('09:30', 60)).toBe('10:30')
    expect(addMinutesToTime('23:30', 60)).toBe('23:59')
  })

  it('joins the parent path', () => {
    expect(
      pathLabel([
        { kind: 'goal', id: 1, title: 'Become a capable engineer' },
        { kind: 'milestone', id: 2, title: 'Backend skills' },
        { kind: 'chapter', id: 3, title: 'Rust fundamentals' },
      ]),
    ).toBe('Become a capable engineer › Backend skills › Rust fundamentals')
  })

  it('remembers the Outcome achieved confirmation', () => {
    const store = new Map<string, string>()
    const storage = {
      getItem: (key: string) => store.get(key) ?? null,
      setItem: (key: string, value: string) => void store.set(key, value),
    }
    expect(outcomeLearned(storage)).toBe(false)
    markOutcomeLearned(storage)
    expect(outcomeLearned(storage)).toBe(true)
  })
})
