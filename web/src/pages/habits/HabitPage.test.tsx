// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest'

import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError, type HabitDetail } from '@/lib/api'

import { dayResult, READ, WAKE } from './testFixtures'

const api = vi.hoisted(() => ({
  getHabitDetail: vi.fn(),
  archiveHabit: vi.fn(),
  restoreHabit: vi.fn(),
  deleteHabit: vi.fn(),
  deleteFreeze: vi.fn(),
  setHabitDay: vi.fn(),
  clearHabitDay: vi.fn(),
  createFreeze: vi.fn(),
}))

vi.mock('@/lib/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/api')>()),
  ...api,
}))
vi.mock('@/lib/asOf', () => ({ useAsOf: () => '2026-11-14' }))

import { HabitPage } from './HabitPage'

const DETAIL: HabitDetail = {
  habit: WAKE,
  as_of: '2026-11-14',
  current_streak: { count: 12, period: 'day' },
  best_streak: 21,
  kept_last_4_weeks: { done: 24, target: 28, share: 24 / 28 },
  history: [
    { period: 'day', start: '2026-11-13', end: '2026-11-13', target: 1, done: 1, state: 'kept' },
    { period: 'day', start: '2026-11-14', end: '2026-11-14', target: 1, done: 0, state: 'running' },
  ],
  recent: [
    dayResult('2026-11-14', 'open'),
    dayResult('2026-11-13', 'done', { value: 408 }),
    dayResult('2026-11-12', 'not_done', { reason: 'set_by_you', value: 400 }),
  ],
  freezes: [
    {
      id: 4,
      habit: 'wake',
      start_on: '2026-11-04',
      end_on: '2026-11-04',
      reason: 'Travel day',
      created_at: '2026-11-03T08:00:00Z',
    },
    {
      id: 5,
      habit: null,
      start_on: '2026-11-20',
      end_on: '2026-11-22',
      reason: 'Holiday',
      created_at: '2026-11-03T08:00:00Z',
    },
  ],
}

function renderPage(slug = 'wake') {
  return render(
    <MemoryRouter initialEntries={[`/habit/${slug}`]}>
      <Routes>
        <Route path="/habit/:slug" element={<HabitPage />} />
        <Route path="/habits/week" element={<p>Week tab</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  api.getHabitDetail.mockResolvedValue(DETAIL)
  api.archiveHabit.mockResolvedValue({})
  api.restoreHabit.mockResolvedValue({})
  api.deleteHabit.mockResolvedValue(undefined)
  api.deleteFreeze.mockResolvedValue(undefined)
  api.clearHabitDay.mockResolvedValue(undefined)
})

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('HabitPage', () => {
  it('shows the rule, the three figures, history, recent days, and freezes', async () => {
    renderPage()
    expect(await screen.findByRole('heading', { name: 'Wake up early' })).toBeVisible()
    expect(
      screen.getByText('Every day · From your data: wake time before 07:00 · Morning'),
    ).toBeVisible()
    expect(screen.getByText('Current streak').nextSibling).toHaveTextContent('12 days')
    expect(screen.getByText('Best streak').nextSibling).toHaveTextContent('21 days')
    expect(screen.getByText('Kept, last 4 weeks').nextSibling).toHaveTextContent('86%')
    expect(screen.getByText('24 of 28 days')).toBeVisible()
    expect(screen.getByText('1 of 1 days kept in the last 12 weeks.')).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Fri 13 Nov: Done · 06:48 · from sleep' }),
    ).toBeVisible()
    expect(screen.getByRole('button', { name: 'Thu 12 Nov: Not done · Set by you' })).toBeVisible()
    const freezes = screen.getByRole('region', { name: 'Freezes' })
    expect(within(freezes).getByText('20–22 Nov 2026')).toBeVisible()
    expect(within(freezes).getByText('All habits')).toBeVisible()
    expect(within(freezes).getByText('4 Nov 2026')).toBeVisible()
  })

  it('answers a recent day from its row menu', async () => {
    renderPage()
    const row = await screen.findByRole('button', { name: 'Thu 12 Nov: Not done · Set by you' })
    fireEvent.pointerDown(row, { button: 0, ctrlKey: false, pointerType: 'mouse' })
    const menu = await screen.findByRole('menu')
    expect(
      within(menu)
        .getAllByRole('menuitem')
        .map((item) => item.textContent),
    ).toEqual(['Mark done', 'Use data again', 'Freeze this day'])
    fireEvent.click(within(menu).getByRole('menuitem', { name: 'Use data again' }))
    await waitFor(() => expect(api.clearHabitDay).toHaveBeenCalledWith('wake', '2026-11-12'))
  })

  it('removes a freeze', async () => {
    renderPage()
    fireEvent.click(await screen.findByRole('button', { name: 'Remove the freeze 4 Nov 2026' }))
    await waitFor(() => expect(api.deleteFreeze).toHaveBeenCalledWith(4))
  })

  it('archives, and restores an archived habit', async () => {
    renderPage()
    fireEvent.click(await screen.findByRole('button', { name: 'Archive' }))
    await waitFor(() => expect(api.archiveHabit).toHaveBeenCalledWith('wake'))
    cleanup()
    api.getHabitDetail.mockResolvedValue({
      ...DETAIL,
      habit: { ...READ, archived_at: '2026-11-14T09:00:00' },
    })
    renderPage('read')
    expect(await screen.findByText('Archived')).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Restore' }))
    await waitFor(() => expect(api.restoreHabit).toHaveBeenCalledWith('read'))
  })

  it('asks before deleting, saying the history goes with it', async () => {
    renderPage()
    fireEvent.click(await screen.findByRole('button', { name: 'Delete' }))
    const dialog = await screen.findByRole('dialog', { name: 'Delete Wake up early?' })
    expect(dialog).toHaveTextContent('Its history goes with it')
    expect(api.deleteHabit).not.toHaveBeenCalled()
    fireEvent.click(within(dialog).getByRole('button', { name: 'Delete' }))
    await waitFor(() => expect(api.deleteHabit).toHaveBeenCalledWith('wake'))
    expect(await screen.findByText('Week tab')).toBeVisible()
  })

  it('says when there is no such habit', async () => {
    api.getHabitDetail.mockRejectedValue(new ApiError(404, 'habit not found'))
    renderPage('nope')
    expect(await screen.findByText('There is no habit at this address.')).toBeVisible()
  })
})
