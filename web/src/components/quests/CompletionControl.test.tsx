// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

const api = vi.hoisted(() => ({
  completeQuestGoal: vi.fn(),
  reopenQuestGoal: vi.fn(),
}))

vi.mock('@/lib/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/api')>()),
  ...api,
}))

import { type CompletableItem, CompletionControl } from './CompletionControl'

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

const openGoal: CompletableItem = {
  id: 5,
  title: 'Move to Copenhagen',
  status: 'active',
  eligible: false,
  completed_with_open_items: false,
  open_children: [
    { kind: 'milestone', id: 7, title: 'Apply to five companies' },
    { kind: 'task', id: 12, title: 'Ask Sam about the job market' },
  ],
}

describe('CompletionControl', () => {
  it('asks before completing with open items, lists them, and sends override', async () => {
    api.completeQuestGoal.mockResolvedValue({})
    const onChanged = vi.fn()
    render(<CompletionControl kind="goal" item={openGoal} onChanged={onChanged} />)

    expect(screen.getByText('2 items still open.')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Complete anyway…' }))

    const dialog = await screen.findByRole('dialog')
    expect(within(dialog).getByText('Complete with open items?')).toBeTruthy()
    const open = within(dialog).getByRole('list', { name: 'Open items' })
    expect(within(open).getByText('Apply to five companies')).toBeTruthy()
    expect(within(open).getByText('Ask Sam about the job market')).toBeTruthy()
    expect(api.completeQuestGoal).not.toHaveBeenCalled()

    fireEvent.click(within(dialog).getByRole('button', { name: 'Complete anyway' }))

    await waitFor(() => expect(onChanged).toHaveBeenCalled())
    expect(api.completeQuestGoal).toHaveBeenCalledWith(5, true)
  })

  it('cancelling the confirmation completes nothing', async () => {
    render(<CompletionControl kind="goal" item={openGoal} onChanged={vi.fn()} />)

    fireEvent.click(screen.getByRole('button', { name: 'Complete anyway…' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Keep working' }))

    await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull())
    expect(api.completeQuestGoal).not.toHaveBeenCalled()
  })

  it('completes an eligible item directly, without override', async () => {
    api.completeQuestGoal.mockResolvedValue({})
    const onChanged = vi.fn()
    render(
      <CompletionControl
        kind="goal"
        item={{ ...openGoal, eligible: true, open_children: [] }}
        onChanged={onChanged}
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Complete goal' }))

    await waitFor(() => expect(onChanged).toHaveBeenCalled())
    expect(api.completeQuestGoal).toHaveBeenCalledWith(5, false)
  })

  it('shows the open-items note on an overridden item and can reopen it', async () => {
    api.reopenQuestGoal.mockResolvedValue({})
    const onChanged = vi.fn()
    render(
      <CompletionControl
        kind="goal"
        item={{ ...openGoal, status: 'completed', completed_with_open_items: true }}
        onChanged={onChanged}
      />,
    )

    expect(screen.getByText('Completed with open items')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Reopen' }))
    await waitFor(() => expect(api.reopenQuestGoal).toHaveBeenCalledWith(5))
  })
})
