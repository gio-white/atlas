// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest'

import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { HabitsWeek } from '@/lib/api'

import { dayResult, habit, MANUAL, READ, WAKE, WEEK_DAYS } from './testFixtures'

const api = vi.hoisted(() => ({
  getHabitsWeek: vi.fn(),
  listFreezes: vi.fn(),
  listHabits: vi.fn(),
  setHabitDay: vi.fn(),
  clearHabitDay: vi.fn(),
  createFreeze: vi.fn(),
}))

vi.mock('@/lib/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/api')>()),
  ...api,
}))
vi.mock('@/lib/asOf', () => ({ useAsOf: () => '2026-11-14' }))

import { HabitsWeekPage } from './HabitsWeekPage'

const RUN = habit('run', 'Physical activity', {
  rule: { ...MANUAL, frequency: 'times_a_week', times: 4 },
})
const OLD = habit('old', 'Read before bed', { archived_at: '2026-11-09T20:00:00' })

const WEEK: HabitsWeek = {
  as_of: '2026-11-14',
  week_start: '2026-11-09',
  week_end: '2026-11-15',
  rows: [
    {
      habit: WAKE,
      days: WEEK_DAYS.map((day, i) =>
        i < 2
          ? dayResult(day, 'done', { value: 400 })
          : i === 2
            ? dayResult(day, 'not_done', { reason: 'no_data' })
            : i < 6
              ? dayResult(day, 'done', { value: 410 })
              : dayResult(day, 'upcoming'),
      ),
      streak: { count: 12, period: 'day' },
      progress: null,
    },
    {
      habit: READ,
      days: WEEK_DAYS.map((day, i) =>
        i < 5
          ? dayResult(day, 'done')
          : i === 5
            ? dayResult(day, 'open')
            : dayResult(day, 'upcoming'),
      ),
      streak: { count: 2, period: 'day' },
      progress: null,
    },
    {
      habit: RUN,
      days: WEEK_DAYS.map((day, i) =>
        i === 0 || i === 2
          ? dayResult(day, 'done')
          : i < 6
            ? dayResult(day, 'blank')
            : dayResult(day, 'upcoming'),
      ),
      streak: { count: 3, period: 'week' },
      progress: { period: 'week', done: 2, target: 4 },
    },
  ],
  kept: { done: 13, target: 16, share: 0.8125 },
  kept_last_week: { done: 14, target: 19, share: 0.7368 },
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/habits/week']}>
      <HabitsWeekPage />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['Date'] })
  vi.setSystemTime(new Date(2026, 10, 14, 9, 0))
  api.getHabitsWeek.mockResolvedValue(WEEK)
  api.listFreezes.mockResolvedValue([])
  api.listHabits.mockResolvedValue([WAKE, READ, RUN, OLD])
  api.setHabitDay.mockResolvedValue({ day: '2026-11-14', result: 'done' })
  api.clearHabitDay.mockResolvedValue(undefined)
  api.createFreeze.mockResolvedValue({})
})

afterEach(() => {
  cleanup()
  vi.useRealTimers()
  vi.clearAllMocks()
})

describe('HabitsWeekPage', () => {
  it('shows the week, each habit by group with its days, progress, streak, and Habits kept', async () => {
    renderPage()
    expect(await screen.findByRole('heading', { name: 'Week of 9 Nov 2026' })).toBeVisible()
    const morning = screen.getByRole('region', { name: 'Morning' })
    expect(within(morning).getByRole('link', { name: 'Wake up early' })).toHaveAttribute(
      'href',
      '/habit/wake',
    )
    expect(
      within(morning).getByRole('button', {
        name: 'Wake up early, Wed 11 Nov: Not done, No data received',
      }),
    ).toBeVisible()
    const anyTime = screen.getByRole('region', { name: 'Any time' })
    expect(within(anyTime).getAllByText('2 of 4')[0]).toBeInTheDocument()
    expect(within(anyTime).getAllByText('3 weeks')[0]).toBeInTheDocument()
    expect(screen.getByText(/Habits kept this week/)).toHaveTextContent('81%')
    expect(screen.getByText(/last week/)).toHaveTextContent('74%')
    expect(screen.getByRole('button', { name: 'Next week' })).toBeDisabled()
  })

  it('leaves future days alone and toggles a habit you tick from its cell', async () => {
    renderPage()
    await screen.findByRole('heading', { name: 'Week of 9 Nov 2026' })
    expect(
      screen.queryByRole('button', { name: 'Read 30 minutes, Sun 15 Nov: Upcoming' }),
    ).toBeNull()
    fireEvent.click(
      screen.getByRole('button', { name: 'Read 30 minutes, Sat 14 Nov: Not done yet' }),
    )
    await waitFor(() => expect(api.setHabitDay).toHaveBeenCalledWith('read', '2026-11-14', 'done'))
    fireEvent.click(screen.getByRole('button', { name: 'Physical activity, Mon 9 Nov: Done' }))
    await waitFor(() => expect(api.clearHabitDay).toHaveBeenCalledWith('run', '2026-11-09'))
    fireEvent.click(screen.getByRole('button', { name: 'Physical activity, Tue 10 Nov: No tick' }))
    await waitFor(() => expect(api.setHabitDay).toHaveBeenCalledWith('run', '2026-11-10', 'done'))
  })

  it('opens the row menu for a data habit’s day', async () => {
    renderPage()
    const cell = await screen.findByRole('button', {
      name: 'Wake up early, Wed 11 Nov: Not done, No data received',
    })
    fireEvent.pointerDown(cell, { button: 0, ctrlKey: false, pointerType: 'mouse' })
    const menu = await screen.findByRole('menu')
    expect(
      within(menu)
        .getAllByRole('menuitem')
        .map((item) => item.textContent),
    ).toEqual(['Mark done', 'Freeze this day', 'Open habit'])
    fireEvent.click(within(menu).getByRole('menuitem', { name: 'Mark done' }))
    await waitFor(() => expect(api.setHabitDay).toHaveBeenCalledWith('wake', '2026-11-11', 'done'))
  })

  it('lists archived habits at the bottom', async () => {
    renderPage()
    const archived = await screen.findByRole('region', { name: 'Archived' })
    expect(within(archived).getByRole('link', { name: /Read before bed/ })).toHaveAttribute(
      'href',
      '/habit/old',
    )
  })
})
