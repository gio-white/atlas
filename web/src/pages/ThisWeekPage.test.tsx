// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest'

import { cleanup, render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { ThisWeek, WeekNumbers } from '@/lib/api'

const api = vi.hoisted(() => ({ getThisWeek: vi.fn() }))
vi.mock('@/lib/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/api')>()),
  ...api,
}))
vi.mock('@/lib/asOf', () => ({ useShell: () => ({ asOf: '2026-11-08' }) }))

import { ThisWeekPage } from './ThisWeekPage'

function numbers(overrides: Partial<WeekNumbers>): WeekNumbers {
  return {
    as_of: '2026-11-08',
    week_start: '2026-11-02',
    sessions_kept: 0,
    sessions_total: 0,
    tasks_completed: 0,
    milestones_completed: 0,
    habits_kept: 0,
    habits_judged: 0,
    habits_kept_share: null,
    sleep_average_minutes: null,
    sleep_average_bedtime: null,
    sleep_average_wake: null,
    sleep_nights: 0,
    sleep_missing_nights: 7,
    screen_total: null,
    screen_daily_average: null,
    screen_score: null,
    screen_good: null,
    screen_neutral: null,
    screen_bad: null,
    titles_finished: 0,
    ...overrides,
  }
}

const WEEK: ThisWeek = {
  as_of: '2026-11-08',
  week_start: '2026-11-02',
  week_end: '2026-11-08',
  complete: true,
  current: numbers({
    sessions_kept: 5,
    sessions_total: 7,
    tasks_completed: 6,
    habits_kept_share: 0.82,
    sleep_nights: 6,
    sleep_missing_nights: 1,
    sleep_average_minutes: 410,
    sleep_average_bedtime: -20,
    sleep_average_wake: 410,
    screen_total: 1100,
    screen_daily_average: 157,
    screen_score: 61,
    screen_good: 500,
    screen_neutral: 300,
    screen_bad: 300,
    titles_finished: 2,
  }),
  previous: numbers({
    as_of: '2026-11-01',
    week_start: '2026-10-26',
    sessions_kept: 4,
    sessions_total: 6,
    tasks_completed: 4,
    habits_kept_share: 0.77,
    sleep_nights: 7,
    sleep_average_minutes: 375,
    sleep_average_bedtime: -40,
    sleep_average_wake: 400,
    screen_total: 1220,
    screen_daily_average: 174,
    screen_score: 57,
    titles_finished: 1,
  }),
  habits: [
    { slug: 'read', name: 'Read' },
    { slug: 'run', name: 'Run' },
  ],
}

afterEach(cleanup)

describe('ThisWeekPage', () => {
  it('shows the five blocks with the change from last week', async () => {
    api.getThisWeek.mockResolvedValue(WEEK)
    render(
      <MemoryRouter initialEntries={['/stats/week?on=2026-11-08']}>
        <ThisWeekPage />
      </MemoryRouter>,
    )
    expect(await screen.findByRole('heading', { name: 'Week of 2 Nov 2026' })).toBeInTheDocument()
    expect(api.getThisWeek).toHaveBeenCalledWith('2026-11-08')
    for (const name of ['Quests', 'Habits', 'Sleep', 'Screen time', 'Library']) {
      expect(screen.getByRole('link', { name })).toBeInTheDocument()
    }
    const quests = screen.getByRole('region', { name: 'Quests' })
    expect(within(quests).getByText('5 of 7')).toBeInTheDocument()
    expect(within(quests).getByText('Last week 4 of 6')).toBeInTheDocument()
    expect(within(quests).getByText('+2 vs last week')).toBeInTheDocument()
    const habits = screen.getByRole('region', { name: 'Habits' })
    expect(within(habits).getByText('82%')).toBeInTheDocument()
    expect(within(habits).getByText('+5 points vs last week')).toBeInTheDocument()
    expect(within(habits).getByText('Read')).toBeInTheDocument()
    expect(within(habits).getByText('Run')).toBeInTheDocument()
    const sleep = screen.getByRole('region', { name: 'Sleep' })
    expect(within(sleep).getByText('+35m vs last week')).toBeInTheDocument()
    expect(within(sleep).getByText('23:40')).toBeInTheDocument()
    expect(within(sleep).getByText('20m later than last week')).toBeInTheDocument()
    const screenTime = screen.getByRole('region', { name: 'Screen time' })
    expect(within(screenTime).getByText('−2h vs last week')).toBeInTheDocument()
    expect(within(screenTime).getByText('Good 8h 20m')).toBeInTheDocument()
    const library = screen.getByRole('region', { name: 'Library' })
    expect(within(library).getByText('2')).toBeInTheDocument()
  })

  it('shows empty states for sleep and screen time without data', async () => {
    api.getThisWeek.mockResolvedValue({
      ...WEEK,
      current: numbers({}),
      habits: [],
    })
    render(
      <MemoryRouter>
        <ThisWeekPage />
      </MemoryRouter>,
    )
    expect(await screen.findByText('No sleep data this week.')).toBeInTheDocument()
    expect(screen.getByText('No screen time data this week.')).toBeInTheDocument()
    expect(screen.getByText('No habits yet.')).toBeInTheDocument()
  })
})
