import { describe, expect, it, vi } from 'vitest'

import {
  API_UNREACHABLE,
  type ApiError,
  completeQuestGoal,
  createQuestTask,
  getEntertainmentDashboard,
  getHabitsBoard,
  getHabitsCalendar,
  getQuestCalendar,
  getScreenDashboard,
  listQuestTasks,
  logEntry,
  organizeTask,
  queryString,
} from './api'

describe('queryString', () => {
  it('omits empty values and names as_of for the API', () => {
    expect(queryString({ as_of: '2026-08-13', metric: '', include_archived: undefined })).toBe(
      '?as_of=2026-08-13',
    )
  })
})

describe('request helpers', () => {
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

  it('getHabitsCalendar sends period and as_of', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({
        as_of: '2026-08-13',
        period: 'month',
        range_start: '2026-08-01',
        range_end: '2026-08-31',
        habits: [],
      }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await getHabitsCalendar('month', '2026-08-13')

    expect(fetchMock).toHaveBeenCalledWith(
      '/views/habits/calendar?period=month&as_of=2026-08-13',
      expect.any(Object),
    )
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

    await expect(getHabitsBoard('2026-08-15')).rejects.toMatchObject({
      name: 'ApiError',
      status: 502,
      message: API_UNREACHABLE,
    } satisfies Partial<ApiError>)
    vi.unstubAllGlobals()
  })

  it('maps a network failure to a reachable API message', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('Failed to fetch')))

    await expect(getHabitsBoard('2026-08-15')).rejects.toMatchObject({
      name: 'ApiError',
      status: 0,
      message: API_UNREACHABLE,
    } satisfies Partial<ApiError>)
    vi.unstubAllGlobals()
  })
})

describe('quest client', () => {
  function stubFetch() {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({}) })
    vi.stubGlobal('fetch', fetchMock)
    return fetchMock
  }

  function call(fetchMock: ReturnType<typeof vi.fn>) {
    const [path, init] = fetchMock.mock.calls[0] as [string, RequestInit]
    return { path, method: init.method ?? 'GET', body: init.body as string | undefined }
  }

  it('creates an Inbox task with only a title', async () => {
    const fetchMock = stubFetch()
    await createQuestTask({ title: 'Look into climbing gyms' })
    expect(call(fetchMock)).toEqual({
      path: '/tasks',
      method: 'POST',
      body: JSON.stringify({ title: 'Look into climbing gyms' }),
    })
    vi.unstubAllGlobals()
  })

  it('lists tasks with parent and inbox filters', async () => {
    const fetchMock = stubFetch()
    await listQuestTasks({ parent_kind: 'chapter', parent_id: 4, inbox: false })
    expect(call(fetchMock).path).toBe('/tasks?parent_kind=chapter&parent_id=4&inbox=false')
    vi.unstubAllGlobals()
  })

  it('organizes by integer id and completes with override', async () => {
    const fetchMock = stubFetch()
    await organizeTask(7, { standalone: true })
    expect(call(fetchMock)).toEqual({
      path: '/tasks/7/organize',
      method: 'POST',
      body: JSON.stringify({ standalone: true }),
    })
    fetchMock.mockClear()
    await completeQuestGoal(3, true)
    expect(call(fetchMock)).toEqual({
      path: '/goals/3/complete',
      method: 'POST',
      body: JSON.stringify({ override: true }),
    })
    vi.unstubAllGlobals()
  })

  it('asks the calendar for a UTC range', async () => {
    const fetchMock = stubFetch()
    await getQuestCalendar('2026-11-09T00:00:00Z', '2026-11-16T00:00:00Z')
    expect(call(fetchMock).path).toBe(
      '/views/calendar?start=2026-11-09T00%3A00%3A00Z&end=2026-11-16T00%3A00%3A00Z',
    )
    vi.unstubAllGlobals()
  })
})
