// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest'

import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { Plan, QuestTask } from '@/lib/api'

const api = vi.hoisted(() => ({ getPlan: vi.fn(), listQuestTasks: vi.fn(async () => []) }))
vi.mock('@/lib/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/api')>()),
  ...api,
}))
vi.mock('@/lib/asOf', () => ({ useShell: () => ({ asOf: '2026-11-12' }) }))

import { PlanPage } from './PlanPage'

function task(overrides: Partial<QuestTask>): QuestTask {
  return {
    id: 7,
    title: 'Write the parser',
    description: null,
    status: 'todo',
    priority: 'normal',
    estimate_minutes: null,
    due_on: null,
    weight: null,
    weight_share: null,
    position: 0,
    parent: { kind: 'chapter', id: 3, title: 'Rust fundamentals' },
    path: [
      { kind: 'goal', id: 1, title: 'Become a capable engineer' },
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
    planned_minutes: 0,
    block_count: 0,
    ...overrides,
  }
}

function plan(notScheduled: QuestTask[]): Plan {
  return {
    start: '2026-11-09T00:00:00Z',
    end: '2026-11-16T00:00:00Z',
    blocks: [],
    not_scheduled: notScheduled,
  }
}

function renderPage() {
  return render(
    <MemoryRouter>
      <PlanPage />
    </MemoryRouter>,
  )
}

beforeEach(() => vi.clearAllMocks())
afterEach(cleanup)

describe('Plan: Not scheduled yet', () => {
  it('lists next actions without a session and plans one for the chosen task', async () => {
    api.getPlan.mockResolvedValue(
      plan([task({}), task({ id: 8, title: 'Book the flights', standalone: true, path: [] })]),
    )
    renderPage()

    const list = await screen.findByRole('region', { name: 'Not scheduled yet' })
    expect(within(list).getByText('Write the parser')).toBeInTheDocument()
    expect(within(list).getByText('Book the flights')).toBeInTheDocument()

    fireEvent.click(within(list).getByRole('button', { name: 'Schedule: Book the flights' }))
    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByText('Book the flights')).toBeInTheDocument()
    expect(within(dialog).queryByPlaceholderText('Search your tasks')).not.toBeInTheDocument()
    expect(api.listQuestTasks).not.toHaveBeenCalled()
  })

  it('says so when every next action has a session', async () => {
    api.getPlan.mockResolvedValue(plan([]))
    renderPage()

    const list = await screen.findByRole('region', { name: 'Not scheduled yet' })
    expect(within(list).getByText('Everything next has a session.')).toBeInTheDocument()
  })
})
