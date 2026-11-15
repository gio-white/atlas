// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest'

import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useLocation } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { HabitDayRow, HabitsDay } from '@/lib/api'
import { habit, MANUAL, READ, WAKE } from '@/pages/habits/testFixtures'

const api = vi.hoisted(() => ({
  getHabitsDay: vi.fn(),
  listFreezes: vi.fn(),
  listHabits: vi.fn(),
  setHabitDay: vi.fn(),
  clearHabitDay: vi.fn(),
  createFreeze: vi.fn(),
  deleteFreeze: vi.fn(),
}))

vi.mock('@/lib/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/api')>()),
  ...api,
}))

import { type HabitsToday, HabitsTodayBlock, loadHabitsToday } from './HabitsTodayBlock'

const RUN = habit('run', 'Physical activity', {
  rule: { ...MANUAL, frequency: 'times_a_week', times: 4 },
})

function row(h: typeof READ, result: Partial<HabitDayRow['result']>, rest: Partial<HabitDayRow>) {
  return {
    habit: h,
    result: { day: '2026-11-14', status: 'open', reason: null, value: null, ...result },
    streak: { count: 0, period: 'day' },
    progress: null,
    ...rest,
  } as HabitDayRow
}

const DAY: HabitsDay = {
  day: '2026-11-14',
  done: 2,
  total: 3,
  week: [],
  rows: [
    row(READ, { status: 'open' }, { streak: { count: 1, period: 'day' } }),
    row(WAKE, { status: 'done', value: 408 }, { streak: { count: 12, period: 'day' } }),
    row(
      RUN,
      { status: 'done' },
      {
        streak: { count: 3, period: 'week' },
        progress: { period: 'week', done: 2, target: 4 },
      },
    ),
  ],
}

function Where() {
  const location = useLocation()
  return <p data-testid="where">{location.pathname + location.search}</p>
}

function renderBlock(habits: HabitsToday | null, onChanged = vi.fn(async () => {})) {
  render(
    <MemoryRouter initialEntries={['/?on=2026-11-14']}>
      <Routes>
        <Route
          path="*"
          element={
            <>
              <HabitsTodayBlock habits={habits} search="on=2026-11-14" onChanged={onChanged} />
              <Where />
            </>
          }
        />
      </Routes>
    </MemoryRouter>,
  )
  return onChanged
}

const LOADED: HabitsToday = { view: DAY, freezes: [], hasHabits: true }

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['Date'] })
  vi.setSystemTime(new Date(2026, 10, 14, 9, 0))
  api.getHabitsDay.mockResolvedValue(DAY)
  api.listFreezes.mockResolvedValue([])
  api.listHabits.mockResolvedValue([WAKE, READ, RUN])
  api.setHabitDay.mockResolvedValue({ day: '2026-11-14', result: 'done' })
  api.clearHabitDay.mockResolvedValue(undefined)
})

afterEach(() => {
  cleanup()
  vi.useRealTimers()
  vi.clearAllMocks()
})

describe('HabitsTodayBlock', () => {
  it('loads the Day tab’s view of the day, the freezes, and whether any habit exists', async () => {
    api.listHabits.mockResolvedValue([{ ...READ, archived_at: '2026-11-10T20:00:00' }])
    expect(await loadHabitsToday('2026-11-14')).toEqual({
      view: DAY,
      freezes: [],
      hasHabits: false,
    })
    expect(api.getHabitsDay).toHaveBeenCalledWith('2026-11-14')
  })

  it('shows the count beside a heading that opens the Day tab, and the Day tab’s groups', () => {
    renderBlock(LOADED)
    const block = screen.getByRole('region', { name: 'Habits' })
    expect(within(block).getByRole('link', { name: 'Habits' })).toHaveAttribute(
      'href',
      '/habits?on=2026-11-14',
    )
    expect(within(block).getByText('2 of 3 done')).toBeVisible()
    expect(
      within(block)
        .getAllByRole('region')
        .map((group) => group.getAttribute('aria-label')),
    ).toEqual(['Morning', 'Any time'])
    const morning = within(block).getByRole('region', { name: 'Morning' })
    expect(within(morning).getByText('Wake up early')).toBeVisible()
    expect(within(morning).getByText('06:48 · from sleep')).toBeVisible()
    expect(within(morning).getByText('12 days')).toBeVisible()
    const anyTime = within(block).getByRole('region', { name: 'Any time' })
    expect(within(anyTime).getByText('2 of 4 this week')).toBeVisible()
    expect(within(anyTime).getByText('3 weeks')).toBeVisible()
  })

  it('ticks and unticks a habit you tick, then reloads Home', async () => {
    const onChanged = renderBlock(LOADED)
    fireEvent.click(screen.getByRole('button', { name: 'Done: Read 30 minutes' }))
    await waitFor(() => expect(api.setHabitDay).toHaveBeenCalledWith('read', '2026-11-14', 'done'))
    await waitFor(() => expect(onChanged).toHaveBeenCalledTimes(1))
    fireEvent.click(screen.getByRole('button', { name: 'Done: Physical activity' }))
    await waitFor(() => expect(api.clearHabitDay).toHaveBeenCalledWith('run', '2026-11-14'))
    await waitFor(() => expect(onChanged).toHaveBeenCalledTimes(2))
  })

  it('opens the row menu from the name, with Open habit keeping the As of date', async () => {
    renderBlock(LOADED)
    const name = screen.getByRole('button', { name: 'Read 30 minutes, Not done yet' })
    fireEvent.pointerDown(name, { button: 0, ctrlKey: false, pointerType: 'mouse' })
    const menu = await screen.findByRole('menu')
    expect(
      within(menu)
        .getAllByRole('menuitem')
        .map((item) => item.textContent),
    ).toEqual(['Mark done', 'Mark not done', 'Freeze this day', 'Open habit'])
    fireEvent.click(within(menu).getByRole('menuitem', { name: 'Open habit' }))
    expect(screen.getByTestId('where')).toHaveTextContent('/habit/read?on=2026-11-14')
  })

  it('shows the API’s message when a tick fails', async () => {
    api.setHabitDay.mockRejectedValue(new Error('offline'))
    renderBlock(LOADED)
    fireEvent.click(screen.getByRole('button', { name: 'Done: Read 30 minutes' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Couldn’t save that. Try again.')
  })

  it('offers New habit when there are no habits, and says when none is scheduled', () => {
    renderBlock({ view: { ...DAY, done: 0, total: 0, rows: [] }, freezes: [], hasHabits: false })
    expect(screen.getByText('No habits yet')).toBeVisible()
    expect(screen.getByRole('button', { name: 'New habit' })).toBeVisible()
    expect(screen.queryByText('0 of 0 done')).not.toBeInTheDocument()
    cleanup()
    renderBlock({ view: { ...DAY, done: 0, total: 0, rows: [] }, freezes: [], hasHabits: true })
    expect(screen.getByText('No habits scheduled today.')).toBeVisible()
    cleanup()
    renderBlock({
      view: { ...DAY, day: '2026-11-12', done: 0, total: 0, rows: [] },
      freezes: [],
      hasHabits: true,
    })
    expect(screen.getByText('No habits scheduled on this day.')).toBeVisible()
  })

  it('says so when the habits could not load', () => {
    renderBlock(null)
    expect(screen.getByRole('status')).toHaveTextContent('Couldn’t load this right now.')
  })
})
