// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest'

import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import type { ReactNode } from 'react'
import { MemoryRouter, Outlet, Route, Routes } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { QuestTask, ScheduledBlock, TimeBlock, TodayQuests } from '@/lib/api'
import * as api from '@/lib/api'
import { localToUtc, OUTCOME_LEARNED_KEY, utcToLocal } from '@/lib/timeBlocks'
import { TodayPage } from '@/pages/quests/TodayPage'

import { TaskTimeBlocks } from './TaskTimeBlocks'
import { TimeBlockDialog } from './TimeBlockDialog'
import { HOUR_PX, WeekCalendar } from './WeekCalendar'

vi.mock('@/lib/api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@/lib/api')>()
  return {
    ...actual,
    getTodayQuests: vi.fn(),
    completeTimeBlock: vi.fn(async () => ({})),
    cancelTimeBlock: vi.fn(async () => ({})),
    createTimeBlock: vi.fn(async () => ({})),
    updateTimeBlock: vi.fn(async () => ({})),
    deleteTimeBlock: vi.fn(async () => undefined),
    updateQuestTask: vi.fn(async () => ({})),
    getQuestTask: vi.fn(),
    listQuestTasks: vi.fn(async () => []),
  }
})

const TODAY = '2026-11-09'

function task(overrides: Partial<QuestTask> = {}): QuestTask {
  return {
    id: 7,
    title: 'Write a CLI that parses CSV files',
    description: null,
    status: 'todo',
    priority: 'normal',
    estimate_minutes: 180,
    due_on: null,
    weight: null,
    weight_share: null,
    position: 0,
    parent: { kind: 'chapter', id: 3, title: 'Rust fundamentals' },
    path: [
      { kind: 'goal', id: 1, title: 'Become a capable engineer' },
      { kind: 'milestone', id: 2, title: 'Backend skills' },
      { kind: 'chapter', id: 3, title: 'Rust fundamentals' },
    ],
    inbox: false,
    standalone: false,
    organized_at: '2026-11-01T09:00:00Z',
    started_at: null,
    completed_at: null,
    archived_at: null,
    created_at: '2026-11-01T09:00:00Z',
    updated_at: '2026-11-01T09:00:00Z',
    planned_minutes: 90,
    block_count: 1,
    ...overrides,
  }
}

function block(overrides: Partial<TimeBlock> = {}): TimeBlock {
  return {
    id: 11,
    task_id: 7,
    start_at: localToUtc(TODAY, '09:00'),
    end_at: localToUtc(TODAY, '10:30'),
    status: 'scheduled',
    provider: 'internal',
    external_event_id: null,
    created_at: '2026-11-01T09:00:00Z',
    updated_at: '2026-11-01T09:00:00Z',
    minutes: 90,
    unconfirmed: false,
    overlaps: false,
    ...overrides,
  }
}

function today(blocks: ScheduledBlock[], extra: Partial<TodayQuests> = {}): TodayQuests {
  return { date: TODAY, blocks, unconfirmed: [], due_today: [], up_next: [], ...extra }
}

function renderInShell(node: ReactNode) {
  return render(
    <MemoryRouter initialEntries={['/today']}>
      <Routes>
        <Route
          element={<Outlet context={{ asOf: TODAY, displayName: 'Test', openLog: () => {} }} />}
        >
          <Route path="*" element={node} />
        </Route>
      </Routes>
    </MemoryRouter>,
  )
}

beforeEach(() => {
  vi.clearAllMocks()
  window.localStorage.clear()
})
afterEach(cleanup)

describe('Today', () => {
  beforeEach(() => {
    vi.mocked(api.getTodayQuests).mockResolvedValue(today([{ block: block(), task: task() }]))
  })

  it('shows the session with its time range and parent path', async () => {
    renderInShell(<TodayPage />)
    const row = await screen.findByTestId('session-11')
    expect(within(row).getByText('Write a CLI that parses CSV files')).toBeInTheDocument()
    expect(
      within(row).getByText('Become a capable engineer › Backend skills › Rust fundamentals'),
    ).toBeInTheDocument()
    expect(within(row).getByText('09:00')).toBeInTheDocument()
    expect(within(row).getByText('10:30')).toBeInTheDocument()
  })

  it('Session done completes the block and never the task', async () => {
    renderInShell(<TodayPage />)
    fireEvent.click(
      await screen.findByRole('button', {
        name: 'Session done: Write a CLI that parses CSV files',
      }),
    )
    await waitFor(() => expect(api.completeTimeBlock).toHaveBeenCalledWith(11))
    expect(api.updateQuestTask).not.toHaveBeenCalled()
    expect(await screen.findByText(/stays open until you mark the outcome/)).toBeInTheDocument()
  })

  it('Outcome achieved asks the first time, then completes the task only', async () => {
    renderInShell(<TodayPage />)
    fireEvent.click(
      await screen.findByRole('button', {
        name: 'Outcome achieved: Write a CLI that parses CSV files',
      }),
    )
    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByText('Complete the task?')).toBeInTheDocument()
    expect(api.updateQuestTask).not.toHaveBeenCalled()
    fireEvent.click(within(dialog).getByRole('button', { name: 'Complete task' }))
    await waitFor(() =>
      expect(api.updateQuestTask).toHaveBeenCalledWith(7, { status: 'completed' }),
    )
    expect(api.completeTimeBlock).not.toHaveBeenCalled()
    expect(window.localStorage.getItem(OUTCOME_LEARNED_KEY)).toBe('1')
  })

  it('Outcome achieved skips the confirmation once learned', async () => {
    window.localStorage.setItem(OUTCOME_LEARNED_KEY, '1')
    renderInShell(<TodayPage />)
    fireEvent.click(
      await screen.findByRole('button', {
        name: 'Outcome achieved: Write a CLI that parses CSV files',
      }),
    )
    await waitFor(() =>
      expect(api.updateQuestTask).toHaveBeenCalledWith(7, { status: 'completed' }),
    )
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('lets you resolve an unconfirmed session as done or cancelled', async () => {
    const past = block({
      id: 3,
      start_at: localToUtc('2026-11-07', '18:00'),
      end_at: localToUtc('2026-11-07', '19:00'),
      unconfirmed: true,
    })
    vi.mocked(api.getTodayQuests).mockResolvedValue(
      today([], { unconfirmed: [{ block: past, task: task() }] }),
    )
    renderInShell(<TodayPage />)
    const section = (await screen.findByRole('heading', { name: /Unconfirmed/ })).closest(
      'section',
    ) as HTMLElement
    expect(
      within(section).queryByRole('button', { name: /Outcome achieved/ }),
    ).not.toBeInTheDocument()
    fireEvent.click(within(section).getByRole('button', { name: /Didn’t happen/ }))
    await waitFor(() => expect(api.cancelTimeBlock).toHaveBeenCalledWith(3))
    fireEvent.click(within(section).getByRole('button', { name: /Session done/ }))
    await waitFor(() => expect(api.completeTimeBlock).toHaveBeenCalledWith(3))
    expect(api.updateQuestTask).not.toHaveBeenCalled()
  })
})

describe('WeekCalendar', () => {
  it('draws a block in its day column at its hour', () => {
    const item = {
      block: block({
        start_at: localToUtc('2026-11-11', '14:00'),
        end_at: localToUtc('2026-11-11', '15:30'),
      }),
      task: task(),
    }
    render(
      <WeekCalendar
        monday="2026-11-09"
        blocks={[item]}
        today={TODAY}
        showCancelled={false}
        onSlot={() => {}}
        onBlock={() => {}}
      />,
    )
    const wednesday = screen.getByTestId('day-2026-11-11')
    const drawn = within(wednesday).getByTestId('cal-block-11')
    expect(drawn.style.top).toBe(`${14 * HOUR_PX}px`)
    expect(drawn.style.height).toBe(`${1.5 * HOUR_PX}px`)
    expect(within(screen.getByTestId('day-2026-11-10')).queryByTestId('cal-block-11')).toBeNull()
  })

  it('hides cancelled blocks unless asked, and marks overlaps', () => {
    const cancelled = { block: block({ id: 1, status: 'cancelled' }), task: task() }
    const overlapping = { block: block({ id: 2, overlaps: true }), task: task() }
    const { rerender } = render(
      <WeekCalendar
        monday="2026-11-09"
        blocks={[cancelled, overlapping]}
        today={TODAY}
        showCancelled={false}
        onSlot={() => {}}
        onBlock={() => {}}
      />,
    )
    expect(screen.queryByTestId('cal-block-1')).toBeNull()
    expect(screen.getByTestId('cal-block-2')).toHaveAccessibleName(/overlaps another session/)
    rerender(
      <WeekCalendar
        monday="2026-11-09"
        blocks={[cancelled, overlapping]}
        today={TODAY}
        showCancelled
        onSlot={() => {}}
        onBlock={() => {}}
      />,
    )
    expect(screen.getByTestId('cal-block-1')).toHaveAttribute('data-status', 'cancelled')
  })

  it('opens an empty slot with its date and hour', () => {
    const onSlot = vi.fn()
    render(
      <WeekCalendar
        monday="2026-11-09"
        blocks={[]}
        today={TODAY}
        showCancelled={false}
        onSlot={onSlot}
        onBlock={() => {}}
      />,
    )
    fireEvent.click(
      screen.getByRole('button', { name: 'Plan a session on Tuesday 10 November at 16:00' }),
    )
    expect(onSlot).toHaveBeenCalledWith('2026-11-10', '16:00')
  })
})

describe('TimeBlockDialog', () => {
  const fixed = task()

  it('refuses an end before the start', async () => {
    render(
      <TimeBlockDialog
        open
        onOpenChange={() => {}}
        task={fixed}
        initial={{ date: TODAY, start: '10:00', end: '11:00' }}
        onSaved={() => {}}
      />,
    )
    expect(screen.getByText('Duration: 1h')).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText('To'), { target: { value: '09:30' } })
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'The end time must be after the start time.',
    )
    fireEvent.click(screen.getByRole('button', { name: 'Plan session' }))
    expect(api.createTimeBlock).not.toHaveBeenCalled()
  })

  it('creates the block in UTC from the local inputs', async () => {
    const onSaved = vi.fn()
    render(
      <TimeBlockDialog
        open
        onOpenChange={() => {}}
        task={fixed}
        initial={{ date: TODAY, start: '10:00', end: '11:15' }}
        onSaved={onSaved}
      />,
    )
    fireEvent.click(screen.getByRole('button', { name: 'Plan session' }))
    await waitFor(() =>
      expect(api.createTimeBlock).toHaveBeenCalledWith({
        task_id: 7,
        start_at: localToUtc(TODAY, '10:00'),
        end_at: localToUtc(TODAY, '11:15'),
      }),
    )
    expect(onSaved).toHaveBeenCalled()
  })

  it('edits an existing block from its local time', async () => {
    const existing = block()
    render(
      <TimeBlockDialog
        open
        onOpenChange={() => {}}
        block={existing}
        task={fixed}
        onSaved={() => {}}
      />,
    )
    expect(screen.getByLabelText('From')).toHaveValue(utcToLocal(existing.start_at).time)
    fireEvent.change(screen.getByLabelText('To'), { target: { value: '11:00' } })
    fireEvent.click(screen.getByRole('button', { name: 'Save time' }))
    await waitFor(() =>
      expect(api.updateTimeBlock).toHaveBeenCalledWith(11, {
        start_at: localToUtc(TODAY, '09:00'),
        end_at: localToUtc(TODAY, '11:00'),
      }),
    )
  })

  it('picks a task from organized open tasks', async () => {
    vi.mocked(api.listQuestTasks).mockResolvedValue([
      task({ id: 1, title: 'Open task' }),
      task({ id: 2, title: 'Inbox task', inbox: true, path: [] }),
      task({ id: 3, title: 'Done task', status: 'completed' }),
    ])
    render(
      <TimeBlockDialog
        open
        onOpenChange={() => {}}
        initial={{ date: TODAY, start: '10:00' }}
        onSaved={() => {}}
      />,
    )
    const list = await screen.findByRole('listbox', { name: 'Tasks' })
    await within(list).findByText('Open task')
    expect(within(list).queryByText('Inbox task')).toBeNull()
    expect(within(list).queryByText('Done task')).toBeNull()
    fireEvent.click(within(list).getByText('Open task'))
    fireEvent.click(screen.getByRole('button', { name: 'Plan session' }))
    await waitFor(() =>
      expect(api.createTimeBlock).toHaveBeenCalledWith(expect.objectContaining({ task_id: 1 })),
    )
  })
})

describe('TaskTimeBlocks', () => {
  it('lists sessions with planned time against the estimate', async () => {
    vi.mocked(api.getQuestTask).mockResolvedValue({ ...task(), blocks: [block()] })
    const onChanged = vi.fn()
    render(<TaskTimeBlocks taskId={7} onChanged={onChanged} />)
    expect(await screen.findByTestId('planned-effort')).toHaveTextContent(
      '1h 30m planned · estimate 3h',
    )
    fireEvent.click(screen.getByRole('button', { name: /^Session done/ }))
    await waitFor(() => expect(api.completeTimeBlock).toHaveBeenCalledWith(11))
    await waitFor(() => expect(onChanged).toHaveBeenCalled())
    expect(api.updateQuestTask).not.toHaveBeenCalled()
  })

  it('does not schedule a completed task', async () => {
    vi.mocked(api.getQuestTask).mockResolvedValue({
      ...task({ status: 'completed', completed_at: '2026-11-08T10:00:00Z' }),
      blocks: [],
    })
    render(<TaskTimeBlocks taskId={7} />)
    expect(await screen.findByRole('button', { name: /Schedule/ })).toBeDisabled()
    expect(screen.getByText('Reopen the task to plan more sessions.')).toBeInTheDocument()
  })
})
