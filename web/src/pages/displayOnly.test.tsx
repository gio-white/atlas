// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest'

import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import type { ReactNode } from 'react'
import { MemoryRouter, Outlet, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { SleepCard } from '@/components/home/SleepCard'
import type { ScreenDashboard, SleepNight, SleepView } from '@/lib/api'
import * as api from '@/lib/api'
import { EntriesPage } from '@/pages/EntriesPage'
import { SCORE_EXPLANATION, ScreenPage } from '@/pages/ScreenPage'
import { SleepPage } from '@/pages/SleepPage'

vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>()
  return {
    ...actual,
    getSleepView: vi.fn(),
    getScreenDashboard: vi.fn(),
    listScreenCategories: vi.fn(async () => []),
    listScreenApps: vi.fn(async () => []),
    listScreenDevices: vi.fn(async () => []),
    listScreenBudgets: vi.fn(async () => []),
    listEntries: vi.fn(async () => []),
    listMetrics: vi.fn(async () => []),
  }
})

const AS_OF = '2026-08-13'

function renderPage(page: ReactNode, path = '/') {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route
          element={<Outlet context={{ asOf: AS_OF, displayName: 'Test', openLog: () => {} }} />}
        >
          <Route path="*" element={page} />
        </Route>
      </Routes>
    </MemoryRouter>,
  )
}

function night(date: string): SleepNight {
  return {
    date,
    session_id: 1,
    started_at: `${date}T00:00:00Z`,
    ended_at: `${date}T07:00:00Z`,
    bed_offset: -60,
    wake_offset: 420,
    in_bed_minutes: 480,
    asleep_minutes: 450,
    stages: { awake: 30, rem: 90, light: 240, deep: 120 },
    segments: [
      { stage: 'light', start_offset: -60, end_offset: 180 },
      { stage: 'deep', start_offset: 180, end_offset: 300 },
    ],
  }
}

function sleepView(nights: (SleepNight | null)[], recorded: string | null): SleepView {
  const days = nights.map((item, index) => ({
    date: `2026-08-${String(13 - nights.length + 1 + index).padStart(2, '0')}`,
    night: item,
  }))
  const logged = nights.filter((item) => item !== null).length
  return {
    as_of: AS_OF,
    range_start: days[0]?.date ?? AS_OF,
    range_end: AS_OF,
    night: nights.at(-1) ?? null,
    days,
    nights_logged: logged,
    average_asleep: logged > 0 ? 450 : null,
    average_bed_offset: logged > 0 ? -60 : null,
    average_wake_offset: logged > 0 ? 420 : null,
    average_stages: logged > 0 ? { awake: 30, rem: 90, light: 240, deep: 120 } : null,
    bed_spread: logged > 1 ? 20 : null,
    wake_spread: logged > 1 ? 10 : null,
    last_recorded_at: recorded,
  }
}

function dashboard(overrides: Partial<ScreenDashboard> = {}): ScreenDashboard {
  return {
    period: 'week',
    as_of: AS_OF,
    range_start: '2026-08-10',
    range_end: AS_OF,
    previous_start: '2026-08-03',
    previous_end: '2026-08-09',
    total: 120,
    daily_average: 30,
    longest_day: { date: AS_OF, minutes: 60 },
    delta_minutes: null,
    delta_fraction: null,
    score: 50,
    score_band: 'ok',
    judgments: { useful: 30, waste: 60, neutral: 30, total: 120 },
    apps: [],
    categories: [
      { slug: 'social', name: 'Social', judgment: 'waste', minutes: 60, share: 0.5, apps: [] },
      { slug: 'video', name: 'Video', judgment: 'waste', minutes: 60, share: 0.5, apps: [] },
    ],
    devices: [],
    daily: [{ date: AS_OF, useful: 30, waste: 60, neutral: 30, total: 120 }],
    comparison: [],
    hours: [],
    trend: [],
    insights: [],
    budgets: [],
    last_recorded_at: '2026-08-13T08:00:00Z',
    ...overrides,
  }
}

const CAPTURE = /log|delete|edit|save night|add stage/i

beforeEach(() => {
  vi.mocked(api.getSleepView).mockReset()
  vi.mocked(api.getScreenDashboard).mockReset()
  vi.mocked(api.listEntries).mockClear()
})

afterEach(cleanup)

describe('Sleep page', () => {
  it('shows nights read-only, with missing nights as visible gaps', async () => {
    vi.mocked(api.getSleepView).mockResolvedValue(
      sleepView([night('2026-08-11'), null, night('2026-08-13')], '2026-08-13T08:00:00Z'),
    )
    renderPage(<SleepPage />)

    expect(await screen.findByRole('heading', { name: 'Nights' })).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: CAPTURE })).not.toBeInTheDocument()
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument()
    expect(document.querySelector('input')).toBeNull()
    expect(screen.getByText(/Last updated/)).toBeInTheDocument()
    expect(within(screen.getByRole('list', { name: 'Nights' })).getByText('No data')).toBeVisible()
    expect(screen.queryByText(/· \d+ stages?/)).not.toBeInTheDocument()
    expect(screen.getByRole('tab', { name: '90 days' })).toBeInTheDocument()
    expect(api.getSleepView).toHaveBeenCalledWith(AS_OF, 7)
  })

  it('asks the API for the picked range', async () => {
    vi.mocked(api.getSleepView).mockResolvedValue(
      sleepView([night('2026-08-13')], '2026-08-13T08:00:00Z'),
    )
    renderPage(<SleepPage />)

    fireEvent.click(await screen.findByRole('tab', { name: 'Month' }))

    await waitFor(() => expect(api.getSleepView).toHaveBeenLastCalledWith(AS_OF, 30))
  })

  it('explains the empty state when no device has sent data', async () => {
    vi.mocked(api.getSleepView).mockResolvedValue(sleepView([null, null], null))
    renderPage(<SleepPage />)

    expect(await screen.findByText('No sleep data yet')).toBeInTheDocument()
    expect(
      screen.getByText('It will appear here once a data source is connected.'),
    ).toBeInTheDocument()
  })
})

describe('Home sleep card', () => {
  it('has no way to log a night', () => {
    renderPage(<SleepCard view={sleepView([night('2026-08-13')], '2026-08-13T08:00:00Z')} />)

    expect(screen.queryByRole('button', { name: CAPTURE })).not.toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'View all' })).toHaveAttribute('href', '/sleep')
  })

  it('shows the empty message without data', () => {
    renderPage(<SleepCard view={sleepView([null], null)} />)

    expect(
      screen.getByText('No sleep data yet. It will appear here once a data source is connected.'),
    ).toBeInTheDocument()
  })
})

describe('Screen Time page', () => {
  it('shows data without capture controls and keeps configuration collapsed', async () => {
    vi.mocked(api.getScreenDashboard).mockResolvedValue(dashboard())
    renderPage(<ScreenPage />)

    expect(await screen.findByText(SCORE_EXPLANATION)).toBeInTheDocument()
    expect(screen.queryByText(/Log a session/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Zeros included/)).not.toBeInTheDocument()
    expect(screen.queryByText(/Good \+ half of Neutral/)).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: CAPTURE })).not.toBeInTheDocument()
    expect(document.querySelector('input')).toBeNull()

    const configure = screen.getByRole('button', { name: /Configure/ })
    expect(configure).toHaveAttribute('aria-expanded', 'false')
    fireEvent.click(configure)
    expect(configure).toHaveAttribute('aria-expanded', 'true')
    const panel = within(document.getElementById('screen-configure-panel') as HTMLElement)
    expect(await panel.findByRole('heading', { name: 'Categories' })).toBeVisible()
    expect(await panel.findByRole('heading', { name: 'Apps' })).toBeVisible()
    expect(await panel.findByRole('heading', { name: 'Caps' })).toBeVisible()
    expect(await panel.findByRole('heading', { name: 'Devices' })).toBeVisible()
  })

  it('colours categories apart even when they share a judgment', async () => {
    vi.mocked(api.getScreenDashboard).mockResolvedValue(dashboard())
    renderPage(<ScreenPage />)

    const social = (await screen.findByText('Social')).closest('li')?.querySelector('span')
    const video = screen.getByText('Video').closest('li')?.querySelector('span')
    expect(social?.className).not.toEqual(video?.className)
  })

  it('explains the empty state when no device has sent data', async () => {
    vi.mocked(api.getScreenDashboard).mockResolvedValue(
      dashboard({ total: null, last_recorded_at: null }),
    )
    renderPage(<ScreenPage />)

    expect(await screen.findByText('No screen time data yet')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /Configure/ })).toBeInTheDocument()
  })
})

describe('History page', () => {
  it('hides automatic screen data by default and shows it when switched off', async () => {
    renderPage(<EntriesPage />)

    const toggle = await screen.findByRole('switch', { name: 'Hide automatic data' })
    expect(toggle).toHaveAttribute('aria-checked', 'true')
    expect(api.listEntries).toHaveBeenLastCalledWith(
      expect.objectContaining({ exclude_area: 'screen' }),
    )

    fireEvent.click(toggle)

    await waitFor(() =>
      expect(api.listEntries).toHaveBeenLastCalledWith(
        expect.objectContaining({ exclude_area: undefined }),
      ),
    )
    expect(screen.getByRole('switch', { name: 'Hide automatic data' })).toHaveAttribute(
      'aria-checked',
      'false',
    )
  })
})
