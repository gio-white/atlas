// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

const api = vi.hoisted(() => ({
  createHabit: vi.fn(),
  updateHabit: vi.fn(),
}))

vi.mock('@/lib/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/api')>()),
  ...api,
}))

import { HabitFormDialog } from './HabitFormDialog'

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('HabitFormDialog', () => {
  it('creates a habit from the typed name, with no area to choose or send', async () => {
    api.createHabit.mockResolvedValue({ slug: 'meditate' })
    const onSaved = vi.fn()
    render(<HabitFormDialog open onOpenChange={() => {}} onSaved={onSaved} />)

    expect(screen.queryByLabelText(/Area/)).toBeNull()

    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Meditate' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create habit' }))

    await waitFor(() => expect(onSaved).toHaveBeenCalled())
    const body = api.createHabit.mock.calls[0][0]
    expect(body).toEqual(expect.objectContaining({ name: 'Meditate' }))
    expect(body).not.toHaveProperty('area')
  })
})
