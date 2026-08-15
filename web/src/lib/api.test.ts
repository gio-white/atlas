import { describe, expect, it, vi } from 'vitest'

import {
  API_UNREACHABLE,
  type ApiError,
  getEntertainmentDashboard,
  getGoalsBoard,
  getHabitsBoard,
  getScreenDashboard,
  getToday,
  logEntry,
  queryString,
} from './api'

describe('queryString', () => {
  it('omits empty values and names as_of for the API', () => {
    expect(queryString({ as_of: '2026-08-13', area: '', include_archived: undefined })).toBe(
      '?as_of=2026-08-13',
    )
  })
})

describe('request helpers', () => {
  it('getToday appends as_of', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ as_of: '2026-08-13', habits: [], entries: [], goals: [] }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await getToday('2026-08-13')

    expect(fetchMock).toHaveBeenCalledWith('/views/today?as_of=2026-08-13', expect.any(Object))
    vi.unstubAllGlobals()
  })

  it('getGoalsBoard appends as_of', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        as_of: '2026-08-13',
        long: { horizon: 'long', on_track: 0, total: 0, fraction: null, goals: [] },
        medium: { horizon: 'medium', on_track: 0, total: 0, fraction: null, goals: [] },
        short: { horizon: 'short', on_track: 0, total: 0, fraction: null, goals: [] },
        week: { total: 0, done: 0, fraction: null, tasks: [] },
      }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await getGoalsBoard('2026-08-13')

    expect(fetchMock).toHaveBeenCalledWith('/views/goals?as_of=2026-08-13', expect.any(Object))
    vi.unstubAllGlobals()
  })

  it('getHabitsBoard appends as_of', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        as_of: '2026-08-13',
        scheduled: 0,
        satisfied: 0,
        fraction: null,
        day: [],
        week: [],
        month: [],
      }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await getHabitsBoard('2026-08-13')

    expect(fetchMock).toHaveBeenCalledWith('/views/habits?as_of=2026-08-13', expect.any(Object))
    vi.unstubAllGlobals()
  })

  it('getScreenDashboard sends period and as_of', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        period: 'week',
        as_of: '2026-08-14',
        range_start: '2026-08-10',
        range_end: '2026-08-14',
        previous_start: '2026-08-03',
        previous_end: '2026-08-07',
        total: null,
        daily_average: null,
        longest_day: null,
        delta_minutes: null,
        delta_fraction: null,
        score: null,
        score_band: null,
        judgments: { useful: null, waste: null, neutral: null, total: null },
        apps: [],
        categories: [],
        devices: [],
        daily: [],
        comparison: [],
        hours: [],
        trend: [],
        insights: [],
        budgets: [],
      }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await getScreenDashboard('week', '2026-08-14')

    expect(fetchMock).toHaveBeenCalledWith(
      '/screen/dashboard?period=week&as_of=2026-08-14',
      expect.any(Object),
    )
    vi.unstubAllGlobals()
  })

  it('getEntertainmentDashboard sends period and as_of', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        period: 'week',
        as_of: '2026-08-14',
        range_start: '2026-08-10',
        range_end: '2026-08-14',
        finished_in_range: 0,
        started_in_range: 0,
        queued: 0,
        in_progress: 0,
        done: 0,
        dropped: 0,
        by_kind: [],
        by_topic: [],
        recently_finished: [],
        library: { queued: [], in_progress: [], done: [], dropped: [] },
      }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await getEntertainmentDashboard('week', '2026-08-14')

    expect(fetchMock).toHaveBeenCalledWith(
      '/entertainment/dashboard?period=week&as_of=2026-08-14',
      expect.any(Object),
    )
    vi.unstubAllGlobals()
  })

  it('throws ApiError with the server detail', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 400,
        statusText: 'Bad Request',
        json: async () => ({ detail: 'unknown metric' }),
      }),
    )

    await expect(logEntry({ metric: 'missing', value: 1 })).rejects.toMatchObject({
      name: 'ApiError',
      status: 400,
      message: 'unknown metric',
    } satisfies Partial<ApiError>)
    vi.unstubAllGlobals()
  })

  it('maps a 502 proxy failure to a reachable API message', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 502,
        statusText: 'Bad Gateway',
        json: async () => null,
      }),
    )

    await expect(getToday('2026-08-15')).rejects.toMatchObject({
      name: 'ApiError',
      status: 502,
      message: API_UNREACHABLE,
    } satisfies Partial<ApiError>)
    vi.unstubAllGlobals()
  })

  it('maps a network failure to a reachable API message', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))

    await expect(getToday('2026-08-15')).rejects.toMatchObject({
      name: 'ApiError',
      status: 0,
      message: API_UNREACHABLE,
    } satisfies Partial<ApiError>)
    vi.unstubAllGlobals()
  })
})
