// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/lib/api'

const api = vi.hoisted(() => ({ promoteTask: vi.fn() }))

vi.mock('@/lib/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/api')>()),
  ...api,
}))

import { HAS_SESSIONS_MESSAGE, PromoteDialog } from './PromoteDialog'
import { task } from './testFixtures'

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

function renderDialog(blockCount: number, onPromoted = vi.fn()) {
  render(
    <MemoryRouter>
      <PromoteDialog
        task={task(42, 'Plan the move', {
          inbox: true,
          organized_at: null,
          block_count: blockCount,
        })}
        open
        onOpenChange={() => {}}
        onPromoted={onPromoted}
      />
    </MemoryRouter>,
  )
  return onPromoted
}

describe('PromoteDialog', () => {
  it('explains and blocks turning a task with sessions into something else', () => {
    renderDialog(2)

    expect(screen.getByRole('alert').textContent).toBe(HAS_SESSIONS_MESSAGE)
    const submit = screen.getByRole('button', { name: /Turn into/ }) as HTMLButtonElement
    expect(submit.disabled).toBe(true)
    fireEvent.click(submit)
    expect(api.promoteTask).not.toHaveBeenCalled()
  })

  it('shows the same plain explanation when the server refuses because of sessions', async () => {
    api.promoteTask.mockRejectedValue(
      new ApiError(400, 'this task already has time blocks, so it cannot become something else'),
    )
    const onPromoted = renderDialog(0)

    fireEvent.click(screen.getByRole('button', { name: 'Turn into goal' }))

    await waitFor(() => expect(screen.getByRole('alert').textContent).toBe(HAS_SESSIONS_MESSAGE))
    expect(onPromoted).not.toHaveBeenCalled()
  })

  it('turns a task into a side quest', async () => {
    api.promoteTask.mockResolvedValue({ kind: 'side_quest', id: 3, title: 'Plan the move' })
    const onPromoted = renderDialog(0)

    fireEvent.click(screen.getByLabelText(/Side quest/))
    fireEvent.click(screen.getByRole('button', { name: 'Turn into side quest' }))

    await waitFor(() => expect(onPromoted).toHaveBeenCalled())
    expect(api.promoteTask).toHaveBeenCalledWith(42, {
      kind: 'side_quest',
      parent_kind: null,
      parent_id: null,
    })
  })

  it('needs a goal before a task becomes a milestone', () => {
    renderDialog(0)

    fireEvent.click(screen.getByLabelText(/Milestone/))

    const submit = screen.getByRole('button', { name: 'Turn into milestone' }) as HTMLButtonElement
    expect(submit.disabled).toBe(true)
    expect(screen.getByText('Choose a goal')).toBeTruthy()
  })
})
