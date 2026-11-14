// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest'

import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import type { ReactNode } from 'react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type {
  EntertainmentTitle,
  HabitStatus,
  JournalDay,
  MainQuests,
  QuestGoal,
  ScreenBudgetStatus,
  ScreenDashboard,
  WeekSoFar,
} from '@/lib/api'

const api = vi.hoisted(() => ({ logJournal: vi.fn(), amendEntry: vi.fn(), checkInHabit: vi.fn() }))
vi.mock('@/lib/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/api')>()),
  ...api,
}))

import { HabitsTodayBlock } from './HabitsTodayBlock'
import { NoteBlock } from './NoteBlock'
import {
  activeGoals,
  dailyTotalCap,
  InProgressBlock,
  MainQuestsBlock,
  ScreenTodayBlock,
  WeekSoFarBlock,
} from './StatusBlocks'

function renderBlock(node: ReactNode) {
  return render(<MemoryRouter>{node}</MemoryRouter>)
}

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

const WEEK: WeekSoFar = {
  as_of: '2026-11-12',
  week_start: '2026-11-09',
  sessions_kept: 5,
  sessions_total: 7,
  habits_kept: 9,
  habits_judged: 11,
  habits_kept_share: 0.82,
  sleep_average_minutes: 410,
  sleep_nights: 3,
  screen_score: 61,
}

describe('This week so far', () => {
  it('shows the four numbers with the brief’s labels', () => {
    renderBlock(<WeekSoFarBlock week={WEEK} search="" />)

    const block = screen.getByRole('region', { name: 'This week so far' })
    const text = block.textContent ?? ''
    expect(text).toContain('Sessions kept5 of 7')
    expect(text).toContain('Habits kept82%')
    expect(text).toContain('Sleep, average6h 50m')
    expect(text).toContain('Screen score61')
  })

  it('shows a dash for numbers it cannot compute yet', () => {
    renderBlock(
      <WeekSoFarBlock
        week={{
          ...WEEK,
          sessions_total: 0,
          sessions_kept: 0,
          habits_kept_share: null,
          sleep_average_minutes: null,
          screen_score: null,
        }}
        search=""
      />,
    )
    expect(screen.getAllByText('—')).toHaveLength(4)
  })

  it('says so when it could not load, without hiding the rest of Home', () => {
    renderBlock(<WeekSoFarBlock week={null} search="" />)
    expect(screen.getByRole('status')).toHaveTextContent('Couldn’t load this right now.')
  })
})

function goal(id: number, extra: Partial<QuestGoal> = {}): QuestGoal {
  return {
    id,
    title: `Goal ${id}`,
    status: 'active',
    archived_at: null,
    progress: 0.4,
    next_action: null,
    ...extra,
  } as QuestGoal
}

describe('Main quests', () => {
  it('lists active goals in Main quests order, at most five', () => {
    const quests: MainQuests = {
      ambitions: [
        {
          ambition: {} as MainQuests['ambitions'][number]['ambition'],
          goals: [goal(1), goal(2, { status: 'completed' }), goal(3)],
          tasks: [],
        },
      ],
      independent_goals: [goal(4), goal(5), goal(6), goal(7)],
    }
    expect(activeGoals(quests).map((item) => item.id)).toEqual([1, 3, 4, 5, 6])
  })

  it('shows each goal’s next action and links to its quest map', () => {
    const quests: MainQuests = {
      ambitions: [],
      independent_goals: [
        goal(4, {
          title: 'Move to Copenhagen',
          next_action: { title: 'Book a viewing trip' } as QuestGoal['next_action'],
        }),
      ],
    }
    renderBlock(<MainQuestsBlock quests={quests} search="on=2026-11-12" />)

    expect(screen.getByRole('link', { name: 'Move to Copenhagen' })).toHaveAttribute(
      'href',
      '/quests/goals/4?on=2026-11-12',
    )
    expect(screen.getByText('Next: Book a viewing trip')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'All quests' })).toHaveAttribute(
      'href',
      '/quests?on=2026-11-12',
    )
  })

  it('offers to add a goal when there are none', () => {
    renderBlock(<MainQuestsBlock quests={{ ambitions: [], independent_goals: [] }} search="" />)
    expect(screen.getByText('No goals yet.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Add a goal' })).toHaveAttribute('href', '/quests')
  })
})

function cap(extra: Partial<ScreenBudgetStatus>): ScreenBudgetStatus {
  return {
    slug: 'cap',
    name: 'Cap',
    target_kind: 'total',
    target_slug: 'all',
    period: 'day',
    target_value: 180,
    comparator: 'at_most',
    current_value: 125,
    satisfied: true,
    scheduled: true,
    current_streak: 0,
    longest_streak: 0,
    adherence: null,
    as_of: '2026-11-12',
    ...extra,
  }
}

describe('Screen time today', () => {
  it('names the cap only when a daily cap on all screen time is active', () => {
    const base = { total: 125, budgets: [] } as unknown as ScreenDashboard
    expect(dailyTotalCap({ ...base, budgets: [cap({})] })).toBe(180)
    expect(dailyTotalCap({ ...base, budgets: [cap({ target_kind: 'judgment' })] })).toBeNull()
    expect(dailyTotalCap({ ...base, budgets: [cap({ period: 'week' })] })).toBeNull()
    expect(dailyTotalCap({ ...base, budgets: [cap({ scheduled: false })] })).toBeNull()
  })

  it('reads "2h 5m of 3h cap", and just the total without a cap', () => {
    const screenToday = { total: 125, budgets: [cap({})] } as unknown as ScreenDashboard
    const { rerender } = renderBlock(<ScreenTodayBlock screen={screenToday} search="" />)
    expect(screen.getByRole('region', { name: 'Screen time today' })).toHaveTextContent(
      '2h 5m of 3h cap',
    )

    rerender(
      <MemoryRouter>
        <ScreenTodayBlock screen={{ ...screenToday, budgets: [] }} search="" />
      </MemoryRouter>,
    )
    expect(screen.queryByText(/cap/)).not.toBeInTheDocument()
  })

  it('has its own empty state and a way into Stats', () => {
    renderBlock(
      <ScreenTodayBlock
        screen={{ total: null, budgets: [] } as unknown as ScreenDashboard}
        search=""
      />,
    )
    expect(screen.getByText('No screen time data yet today.')).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Screen time today' })).toHaveAttribute(
      'href',
      '/stats/screen-time',
    )
  })
})

describe('In progress', () => {
  it('counts titles in progress and names up to three', () => {
    const titles = ['Dune', 'Severance', 'Atomic Habits', 'Lex Fridman'].map(
      (name) => ({ slug: name.toLowerCase(), name }) as EntertainmentTitle,
    )
    renderBlock(<InProgressBlock titles={titles} search="" />)

    const block = screen.getByRole('region', { name: 'In progress' })
    expect(within(block).getByText('4 titles')).toBeInTheDocument()
    expect(within(block).getAllByRole('listitem')).toHaveLength(3)
  })

  it('says when nothing is in progress', () => {
    renderBlock(<InProgressBlock titles={[]} search="" />)
    expect(screen.getByText('Nothing in progress.')).toBeInTheDocument()
  })
})

describe('Note for today', () => {
  const empty: JournalDay = { as_of: '2026-11-12', text: null, entry_id: null }

  it('writes today’s note the first time, then amends it', async () => {
    api.logJournal.mockResolvedValue({})
    api.amendEntry.mockResolvedValue({})
    const onSaved = vi.fn(async () => {})
    const { rerender } = renderBlock(
      <NoteBlock journal={empty} asOf="2026-11-12" search="" onSaved={onSaved} />,
    )

    const field = screen.getByRole('textbox', { name: 'Note for today' })
    expect(field).toHaveAttribute('rows', '1')
    expect(screen.queryByRole('button', { name: 'Save note' })).not.toBeInTheDocument()
    fireEvent.focus(field)
    expect(field).toHaveAttribute('rows', '4')
    fireEvent.change(field, { target: { value: '  A quiet day. ' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save note' }))

    await waitFor(() =>
      expect(api.logJournal).toHaveBeenCalledWith({
        text: 'A quiet day.',
        occurred_on: '2026-11-12',
      }),
    )
    expect(onSaved).toHaveBeenCalled()

    rerender(
      <MemoryRouter>
        <NoteBlock
          journal={{ ...empty, text: 'A quiet day.', entry_id: 31 }}
          asOf="2026-11-12"
          search=""
          onSaved={onSaved}
        />
      </MemoryRouter>,
    )
    const again = screen.getByRole('textbox', { name: 'Note for today' })
    fireEvent.change(again, { target: { value: 'A quiet day. Long walk.' } })
    fireEvent.keyDown(again, { key: 'Enter', ctrlKey: true })
    await waitFor(() =>
      expect(api.amendEntry).toHaveBeenCalledWith(31, { value: 'A quiet day. Long walk.' }),
    )
  })

  it('links to the earlier notes', () => {
    renderBlock(<NoteBlock journal={empty} asOf="2026-11-12" search="" onSaved={async () => {}} />)
    expect(screen.getByRole('link', { name: 'Earlier notes' })).toHaveAttribute('href', '/journal')
  })
})

function habit(overrides: Partial<HabitStatus> & Pick<HabitStatus, 'slug'>): HabitStatus {
  return {
    name: overrides.slug,
    metric_slug: overrides.slug,
    period: 'day',
    target_value: 1,
    comparator: 'at_least',
    current_streak: 0,
    longest_streak: 0,
    adherence: null,
    current_value: null,
    satisfied: false,
    scheduled: true,
    as_of: '2026-11-12',
    kind: 'check',
    time_of_day: 'anytime',
    unit: null,
    archived: false,
    bucket_start: '2026-11-12',
    bucket_end: '2026-11-12',
    days_left: 0,
    effective_target: 1,
    excused: false,
    skipped_today: false,
    today_value: null,
    last_entry_on: null,
    weekdays: null,
    ...overrides,
  }
}

describe('HabitsTodayBlock', () => {
  function renderHabits(statuses: HabitStatus[]) {
    const board = {
      as_of: '2026-11-12',
      scheduled: statuses.length,
      satisfied: 0,
      fraction: null,
      completion_7d: null,
      completion_30d: null,
      day: statuses.filter((row) => row.period === 'day'),
      week: statuses.filter((row) => row.period === 'week'),
      month: statuses.filter((row) => row.period === 'month'),
    }
    return renderBlock(
      <HabitsTodayBlock board={board} asOf="2026-11-12" search="" onChanged={async () => {}} />,
    )
  }

  it('reads a quit habit as slips today and logs a slip in one tap', async () => {
    api.checkInHabit.mockResolvedValue({})
    renderHabits([
      habit({
        slug: 'no-doomscrolling',
        name: 'No doomscrolling',
        kind: 'quit',
        comparator: 'at_most',
        target_value: 0,
        effective_target: 0,
        unit: 'slips',
        satisfied: true,
      }),
    ])
    expect(screen.getByText('No slips today')).toBeInTheDocument()
    expect(screen.queryByText(/of 0 slips/)).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Log a slip' }))
    await waitFor(() =>
      expect(api.checkInHabit).toHaveBeenCalledWith(
        'no-doomscrolling',
        { amount: undefined, on: '2026-11-12', note: null },
        '2026-11-12',
      ),
    )
  })

  it('reads a daily amount as today’s progress, and a weekly one as the week’s', () => {
    renderHabits([
      habit({
        slug: 'pushups',
        kind: 'count',
        target_value: 40,
        effective_target: 40,
        today_value: 10,
        current_value: 10,
      }),
      habit({
        slug: 'runs',
        period: 'week',
        target_value: 3,
        effective_target: 3,
        current_value: 1,
        days_left: 4,
      }),
    ])
    expect(screen.getByText('10 of 40 today')).toBeInTheDocument()
    expect(screen.getByText('1 of 3')).toBeInTheDocument()
    expect(screen.getByText('4 days left')).toBeInTheDocument()
  })
})
