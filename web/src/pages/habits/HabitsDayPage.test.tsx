// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest'

import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { Habit, HabitDayRow, HabitRule, HabitsDay } from '@/lib/api'

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
vi.mock('@/lib/asOf', () => ({ useAsOf: () => '2026-11-14' }))

import { HabitsDayPage } from './HabitsDayPage'

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

function row(h: Habit, result: Partial<HabitDayRow['result']>, rest: Partial<HabitDayRow> = {}) {
  return {
    habit: h,
    result: { day: '2026-11-14', status: 'open', reason: null, value: null, ...result },
    streak: { count: 0, period: 'day' },
    progress: null,
    ...rest,
  } as HabitDayRow
}

const WAKE = habit('wake', 'Wake up before 07:00', {
  time_of_day: 'morning',
  rule: { ...MANUAL, check: 'data', source: 'wake_time', threshold: 'before', value: 420 },
})
const READ = habit('read', 'Read 30 minutes')
const RUN = habit('run', 'Physical activity', {
  rule: { ...MANUAL, frequency: 'times_a_week', times: 4 },
})

const WEEK = ['09', '10', '11', '12', '13', '14', '15'].map((d, i) => ({
  day: `2026-11-${d}`,
  done: i < 5 ? 2 : i === 5 ? 3 : 0,
  total: i < 6 ? 4 : 0,
}))

const DAY: HabitsDay = {
  day: '2026-11-14',
  done: 2,
  total: 3,
  week: WEEK,
  rows: [
    row(WAKE, { status: 'done', value: 408 }, { streak: { count: 12, period: 'day' } }),
    row(READ, { status: 'open' }, { streak: { count: 1, period: 'day' } }),
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

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/habits']}>
      <HabitsDayPage />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.useFakeTimers({ toFake: ['Date'] })
  vi.setSystemTime(new Date(2026, 10, 14, 9, 0))
  api.getHabitsDay.mockResolvedValue(DAY)
  api.listFreezes.mockResolvedValue([])
  api.listHabits.mockResolvedValue([WAKE, READ, RUN])
  api.setHabitDay.mockResolvedValue({ day: '2026-11-14', result: 'done' })
  api.clearHabitDay.mockResolvedValue(undefined)
  api.createFreeze.mockResolvedValue({})
})

afterEach(() => {
  cleanup()
  vi.useRealTimers()
  vi.clearAllMocks()
})

describe('HabitsDayPage', () => {
  it('shows the day, its count, the groups, reasons, progress, and streaks', async () => {
    renderPage()
    expect(await screen.findByRole('heading', { name: 'Saturday 14 Nov 2026' })).toBeVisible()
    expect(screen.getByText('2 of 3 done')).toBeVisible()
    const morning = screen.getByRole('region', { name: 'Morning' })
    expect(within(morning).getByText('Wake up before 07:00')).toBeVisible()
    expect(within(morning).getByText('06:48 · from sleep')).toBeVisible()
    expect(within(morning).getByText('12 days')).toBeVisible()
    const anyTime = screen.getByRole('region', { name: 'Any time' })
    expect(within(anyTime).getByText('2 of 4 this week')).toBeVisible()
    expect(within(anyTime).getByText('3 weeks')).toBeVisible()
    expect(within(anyTime).getByText('1 day')).toBeVisible()
  })

  it('dims the days after today and keeps today selected', async () => {
    renderPage()
    const week = await screen.findByRole('list', { name: 'Week' })
    const days = within(week).getAllByRole('button')
    expect(days[5]).toHaveAttribute('aria-current', 'date')
    expect(days[6]).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Next week' })).toBeDisabled()
    expect(screen.getByRole('button', { name: 'Previous week' })).toBeEnabled()
  })

  it('ticks and unticks a habit you tick from its icon', async () => {
    renderPage()
    fireEvent.click(await screen.findByRole('button', { name: 'Done: Read 30 minutes' }))
    await waitFor(() => expect(api.setHabitDay).toHaveBeenCalledWith('read', '2026-11-14', 'done'))
    fireEvent.click(screen.getByRole('button', { name: 'Done: Physical activity' }))
    await waitFor(() => expect(api.clearHabitDay).toHaveBeenCalledWith('run', '2026-11-14'))
    expect(api.getHabitsDay).toHaveBeenCalledTimes(3)
  })

  it('opens the row menu from a data habit’s icon instead of ticking it', async () => {
    renderPage()
    fireEvent.click(await screen.findByRole('button', { name: 'Done: Wake up before 07:00' }))
    const menu = await screen.findByRole('menu')
    expect(
      within(menu)
        .getAllByRole('menuitem')
        .map((item) => item.textContent),
    ).toEqual(['Mark not done', 'Freeze this day', 'Open habit'])
    expect(api.setHabitDay).not.toHaveBeenCalled()
    fireEvent.click(within(menu).getByRole('menuitem', { name: 'Freeze this day' }))
    await waitFor(() =>
      expect(api.createFreeze).toHaveBeenCalledWith({
        habit: 'wake',
        start_on: '2026-11-14',
        end_on: '2026-11-14',
      }),
    )
  })

  it('uses the data again for a day you set', async () => {
    api.getHabitsDay.mockResolvedValue({
      ...DAY,
      rows: [row(WAKE, { status: 'not_done', reason: 'set_by_you', value: 400 })],
    })
    renderPage()
    expect(await screen.findByText('Set by you')).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Not done: Wake up before 07:00' }))
    fireEvent.click(await screen.findByRole('menuitem', { name: 'Use data again' }))
    await waitFor(() => expect(api.clearHabitDay).toHaveBeenCalledWith('wake', '2026-11-14'))
  })

  it('unfreezes the habit’s own one-day freeze', async () => {
    api.getHabitsDay.mockResolvedValue({
      ...DAY,
      rows: [row(READ, { status: 'frozen', reason: 'frozen' })],
    })
    api.listFreezes.mockResolvedValue([
      {
        id: 7,
        habit: 'read',
        start_on: '2026-11-14',
        end_on: '2026-11-14',
        reason: null,
        created_at: '2026-11-14T08:00:00Z',
      },
    ])
    api.deleteFreeze.mockResolvedValue(undefined)
    renderPage()
    expect(await screen.findByText('Frozen')).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Frozen: Read 30 minutes' }))
    fireEvent.click(await screen.findByRole('menuitem', { name: 'Unfreeze' }))
    await waitFor(() => expect(api.deleteFreeze).toHaveBeenCalledWith(7))
  })

  it('shows no headings when no habit has a time of day', async () => {
    api.getHabitsDay.mockResolvedValue({ ...DAY, rows: [row(READ, {})] })
    renderPage()
    expect(await screen.findByText('Read 30 minutes')).toBeVisible()
    expect(screen.queryByRole('heading', { name: 'Any time' })).toBeNull()
  })

  it('says when there are no habits yet', async () => {
    api.getHabitsDay.mockResolvedValue({ ...DAY, done: 0, total: 0, rows: [] })
    api.listHabits.mockResolvedValue([])
    renderPage()
    expect(await screen.findByText('No habits yet')).toBeVisible()
  })
})
