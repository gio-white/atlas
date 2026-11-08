// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { MainQuests, QuestGoal } from '@/lib/api'
import { INBOX_CHANGED_EVENT } from '@/lib/quests'

const api = vi.hoisted(() => ({
  getInbox: vi.fn(),
  createQuestTask: vi.fn(),
  organizeTask: vi.fn(),
  updateQuestTask: vi.fn(),
  getMainQuests: vi.fn(),
  getSideQuestsView: vi.fn(),
  getGoalTree: vi.fn(),
  getSideQuestTree: vi.fn(),
}))

vi.mock('@/lib/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/api')>()),
  ...api,
}))

import { InboxPage } from '@/pages/quests/InboxPage'

import { chapter, milestone, task } from './testFixtures'

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

const inboxTask = task(42, 'Look into climbing gyms', { inbox: true, organized_at: null })
const goal = { id: 5, title: 'Get stronger' } as QuestGoal

function mockHierarchy() {
  const main: MainQuests = { ambitions: [], independent_goals: [goal] }
  api.getMainQuests.mockResolvedValue(main)
  api.getSideQuestsView.mockResolvedValue({ side_quests: [], standalone_tasks: [] })
  api.getGoalTree.mockResolvedValue({
    goal,
    milestones: [
      {
        milestone: milestone(7, 'Climb twice a week'),
        chapters: [{ chapter: chapter(9, 'Find a gym'), tasks: [] }],
        tasks: [],
      },
    ],
    tasks: [],
  })
}

describe('Inbox', () => {
  it('captures with Enter, sending only a title, and announces the new count', async () => {
    api.getInbox.mockResolvedValueOnce({ count: 0, tasks: [] })
    api.getInbox.mockResolvedValue({ count: 1, tasks: [inboxTask] })
    api.createQuestTask.mockResolvedValue({ ...inboxTask, blocks: [] })
    const changed = vi.fn()
    window.addEventListener(INBOX_CHANGED_EVENT, changed)
    render(
      <MemoryRouter>
        <InboxPage />
      </MemoryRouter>,
    )

    const capture = screen.getByLabelText('Capture a task')
    expect(document.activeElement).toBe(capture)
    fireEvent.change(capture, { target: { value: '  Look into climbing gyms ' } })
    fireEvent.submit(capture.closest('form') as HTMLFormElement)

    await screen.findByText('Look into climbing gyms')
    expect(api.createQuestTask).toHaveBeenCalledWith({ title: 'Look into climbing gyms' })
    expect(changed).toHaveBeenCalled()
    expect((capture as HTMLInputElement).value).toBe('')
    window.removeEventListener(INBOX_CHANGED_EVENT, changed)
  })

  it('organizes the same task into a chapter picked by search', async () => {
    api.getInbox.mockResolvedValueOnce({ count: 1, tasks: [inboxTask] })
    api.getInbox.mockResolvedValue({ count: 0, tasks: [] })
    api.organizeTask.mockResolvedValue({ ...inboxTask, blocks: [] })
    mockHierarchy()
    render(
      <MemoryRouter>
        <InboxPage />
      </MemoryRouter>,
    )

    fireEvent.click(await screen.findByRole('button', { name: /Organize/ }))
    const search = await screen.findByLabelText('Search quests')
    await screen.findByText('Find a gym')
    fireEvent.change(search, { target: { value: 'gym' } })
    expect(screen.queryByText('Climb twice a week')).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: /Find a gym/ }))

    await waitFor(() => expect(api.organizeTask).toHaveBeenCalledTimes(1))
    // Identity kept: the Inbox task's own id is organized, nothing is created or deleted.
    expect(api.organizeTask).toHaveBeenCalledWith(42, { parent_kind: 'chapter', parent_id: 9 })
    expect(api.createQuestTask).not.toHaveBeenCalled()
    expect(await screen.findByText('Sorted into Find a gym.')).toBeTruthy()
    expect(await screen.findByText('Inbox zero')).toBeTruthy()
  })

  it('makes a task standalone without a parent', async () => {
    api.getInbox.mockResolvedValue({ count: 1, tasks: [inboxTask] })
    api.organizeTask.mockResolvedValue({ ...inboxTask, blocks: [] })
    render(
      <MemoryRouter>
        <InboxPage />
      </MemoryRouter>,
    )

    fireEvent.click(await screen.findByRole('button', { name: 'Make standalone' }))

    await waitFor(() => expect(api.organizeTask).toHaveBeenCalledWith(42, { standalone: true }))
  })
})
