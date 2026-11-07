// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { Area } from '@/lib/api'

const api = vi.hoisted(() => ({
  listAreas: vi.fn(),
  createHabit: vi.fn(),
  updateHabit: vi.fn(),
}))

vi.mock('@/lib/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/api')>()),
  ...api,
}))

import { HabitFormDialog } from './HabitFormDialog'

function area(slug: string, name: string): Area {
  return { id: slug.length, slug, name, description: null, archived_at: null }
}

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('HabitFormDialog area picker', () => {
  it('lists user areas only and sends the chosen area with the typed name', async () => {
    api.listAreas.mockResolvedValue([
      area('health', 'Health'),
      area('habits', 'Habits'),
      area('screen', 'Screen'),
      area('life', 'Life'),
    ])
    api.createHabit.mockResolvedValue({ slug: 'meditate' })
    const onSaved = vi.fn()
    render(<HabitFormDialog open onOpenChange={() => {}} onSaved={onSaved} />)

    const select = (await screen.findByLabelText('Area (optional)')) as HTMLSelectElement
    expect([...select.options].map((option) => option.textContent)).toEqual(['None', 'Health'])

    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Meditate' } })
    fireEvent.change(select, { target: { value: 'health' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create habit' }))

    await waitFor(() => expect(onSaved).toHaveBeenCalled())
    expect(api.createHabit).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'Meditate', area: 'health' }),
    )
  })

  it('sends no area when none is picked', async () => {
    api.listAreas.mockResolvedValue([area('health', 'Health')])
    api.createHabit.mockResolvedValue({ slug: 'stretch' })
    const onSaved = vi.fn()
    render(<HabitFormDialog open onOpenChange={() => {}} onSaved={onSaved} />)

    await screen.findByLabelText('Area (optional)')
    fireEvent.change(screen.getByLabelText('Name'), { target: { value: 'Stretch' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create habit' }))

    await waitFor(() => expect(onSaved).toHaveBeenCalled())
    expect(api.createHabit).toHaveBeenCalledWith(expect.objectContaining({ area: null }))
  })
})
