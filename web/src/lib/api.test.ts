import { describe, expect, it, vi } from 'vitest'

import { type ApiError, getToday, logEntry, queryString } from './api'

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
})
