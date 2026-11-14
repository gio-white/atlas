// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest'

import { cleanup, render, screen, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { Habit, HabitRule } from '@/lib/api'

const api = vi.hoisted(() => ({ listHabits: vi.fn() }))

vi.mock('@/lib/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/api')>()),
  ...api,
}))

import { HabitsPage } from './HabitsPage'

const MANUAL: HabitRule = {
  starts_on: '2026-11-01',
  frequency: 'every_day',
  check: 'manual',
  weekdays: null,
  times: null,
  source: null,
  source_ref: null,
  source_ref_name: null,
  threshold: null,
  value: null,
}

function habit(slug: string, name: string, overrides: Partial<Habit> = {}): Habit {
  return {
    id: 1,
    slug,
    name,
    time_of_day: 'anytime',
    first_day: '2026-11-01',
    archived_at: null,
    rule: MANUAL,
    ...overrides,
  }
}

afterEach(cleanup)

describe('HabitsPage (read-only while the rebuild lands)', () => {
  it('lists habits by time of day with their rule, then the archived ones', async () => {
    api.listHabits.mockResolvedValue([
      habit('run', 'Run', { rule: { ...MANUAL, frequency: 'times_a_week', times: 3 } }),
      habit('wake', 'Wake up early', {
        time_of_day: 'morning',
        rule: { ...MANUAL, check: 'data', source: 'wake_time', threshold: 'before', value: 420 },
      }),
      habit('read', 'Read before bed', { archived_at: '2026-11-09T20:00:00' }),
    ])
    render(<HabitsPage />)

    const morning = await screen.findByRole('region', { name: 'Morning' })
    expect(within(morning).getByText('Wake up early')).toBeInTheDocument()
    expect(
      within(morning).getByText('Every day · From your data: wake time before 07:00 · Morning'),
    ).toBeInTheDocument()
    const anytime = screen.getByRole('region', { name: 'Anytime' })
    expect(within(anytime).getByText('3× a week · You tick it')).toBeInTheDocument()
    const archived = screen.getByRole('region', { name: 'Archived' })
    expect(within(archived).getByText('Read before bed')).toBeInTheDocument()
  })

  it('says when there are no habits', async () => {
    api.listHabits.mockResolvedValue([])
    render(<HabitsPage />)
    expect(await screen.findByText('No habits yet')).toBeInTheDocument()
  })
})
