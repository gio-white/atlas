// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

const api = vi.hoisted(() => ({
  updateQuestTask: vi.fn(),
  getQuestTask: vi.fn(),
}))

vi.mock('@/lib/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/api')>()),
  ...api,
}))

import { QuestTree } from './QuestTree'
import { TaskDrawerProvider } from './TaskDrawer'
import { chapter, task } from './testFixtures'

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

function renderTree(onChanged = vi.fn()) {
  render(
    <MemoryRouter>
      <TaskDrawerProvider onChanged={onChanged}>
        <QuestTree
          parent={{ kind: 'milestone', id: 1, title: 'Learn Rust' }}
          chapters={[
            {
              chapter: chapter(10, 'Fundamentals', {
                state: 'in_progress',
                progress: 0.5,
                done_tasks: 1,
                total_tasks: 2,
                weight_share: 0.4,
              }),
              tasks: [
                task(1, 'Ownership', { status: 'completed', weight_share: 0.5 }),
                task(2, 'Write a CLI', { status: 'in_progress', weight_share: 0.5 }),
              ],
            },
            {
              chapter: chapter(11, 'Async Rust', {
                state: 'empty',
                progress: null,
                weight_share: 0.4,
              }),
              tasks: [],
            },
          ]}
          tasks={[task(3, 'Pick a Rust book', { weight_share: 0.2 })]}
          onChanged={onChanged}
        />
      </TaskDrawerProvider>
    </MemoryRouter>,
  )
  return onChanged
}

describe('QuestTree', () => {
  it('renders chapters with their state and tasks, and direct tasks beside them', () => {
    renderTree()

    const chapters = screen.getAllByTestId('chapter')
    expect(chapters).toHaveLength(2)

    const fundamentals = within(chapters[0])
    expect(fundamentals.getByText('Fundamentals')).toBeTruthy()
    expect(
      within(chapters[0].querySelector('header') as HTMLElement).getByText('In progress'),
    ).toBeTruthy()
    expect(fundamentals.getByText('1 of 2 tasks done')).toBeTruthy()
    expect(fundamentals.getAllByTestId('task-row')).toHaveLength(2)
    expect(fundamentals.getByRole('button', { name: 'Reopen Ownership' })).toBeTruthy()

    const empty = within(chapters[1])
    expect(empty.getByText('Empty')).toBeTruthy()
    expect(empty.queryAllByTestId('task-row')).toHaveLength(0)
    expect(empty.getByText(/An empty chapter never counts as done/)).toBeTruthy()

    expect(screen.getByText('Tasks directly on this milestone')).toBeTruthy()
    expect(screen.getByText('Pick a Rust book')).toBeTruthy()
    // Shares come from the API and are shown as percentages, never recomputed.
    expect(screen.getByText('20%')).toBeTruthy()
    expect(screen.getAllByRole('button', { name: /Add a task/ })).toHaveLength(3)
    expect(screen.getByRole('button', { name: /Add a chapter/ })).toBeTruthy()
  })

  it('completes a task only through its explicit checkbox', async () => {
    api.updateQuestTask.mockResolvedValue(task(3, 'Pick a Rust book', { status: 'completed' }))
    const onChanged = renderTree()

    fireEvent.click(screen.getByRole('button', { name: 'Mark Pick a Rust book done' }))

    await waitFor(() => expect(onChanged).toHaveBeenCalled())
    expect(api.updateQuestTask).toHaveBeenCalledWith(3, { status: 'completed' })
  })
})
