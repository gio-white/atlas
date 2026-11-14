// @vitest-environment jsdom
import { cleanup, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { Metric } from '@/lib/api'

const api = vi.hoisted(() => ({ listMetrics: vi.fn() }))
vi.mock('@/lib/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/api')>()),
  ...api,
}))

import { LogDialog } from './LogDialog'

function metric(slug: string, origin: Metric['origin']): Metric {
  return {
    id: slug.length,
    slug,
    name: slug,
    origin,
    value_type: 'count',
    unit: null,
    aggregation: 'sum',
    direction: 'higher_is_better',
    archived_at: null,
  }
}

afterEach(cleanup)

describe('LogDialog', () => {
  it('offers only the metrics you manage, not screen apps or the journal', async () => {
    api.listMetrics.mockResolvedValue([
      metric('books', 'manual'),
      metric('pushups', 'habit'),
      metric('youtube', 'screen'),
      metric('journal', 'journal'),
    ])
    render(<LogDialog open onOpenChange={() => {}} occurredOn="2026-11-12" />)
    const select = await waitFor(() => screen.getByLabelText('Metric') as HTMLSelectElement)
    const options = Array.from(select.options).map((option) => option.value)
    expect(options).toEqual(['', 'books', 'pushups'])
  })
})
