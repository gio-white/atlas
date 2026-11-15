// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest'

import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError, type Habit } from '@/lib/api'

const api = vi.hoisted(() => ({
  createHabit: vi.fn(),
  updateHabit: vi.fn(),
  createFreeze: vi.fn(),
  listScreenCategories: vi.fn(),
  listScreenApps: vi.fn(),
}))

vi.mock('@/lib/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/api')>()),
  ...api,
}))

import { FreezeSheet } from './FreezeSheet'
import { HabitSheet } from './HabitSheet'

const RUN: Habit = {
  id: 3,
  slug: 'run',
  name: 'Run',
  time_of_day: 'anytime',
  first_day: '2026-10-18',
  archived_at: null,
  rule: {
    starts_on: '2026-11-03',
    frequency: 'times_a_week',
    check: 'manual',
    weekdays: null,
    times: 3,
    source: null,
    source_ref: null,
    source_ref_name: null,
    threshold: null,
    value: null,
  },
}

beforeEach(() => {
  api.createHabit.mockImplementation(async (body: { name: string }) => ({ ...RUN, ...body }))
  api.updateHabit.mockResolvedValue(RUN)
  api.createFreeze.mockResolvedValue({})
  api.listScreenCategories.mockResolvedValue([
    { id: 1, slug: 'social', name: 'Social', judgment: 'waste', archived_at: null },
  ])
  api.listScreenApps.mockResolvedValue([])
})

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

function newSheet() {
  const onSaved = vi.fn()
  const onOpenChange = vi.fn()
  render(<HabitSheet open onOpenChange={onOpenChange} onSaved={onSaved} />)
  return { onSaved, onOpenChange }
}

describe('New habit sheet', () => {
  it('asks the four questions and creates a habit you tick', async () => {
    const { onSaved, onOpenChange } = newSheet()
    expect(screen.getByRole('dialog', { name: 'New habit' })).toBeVisible()
    for (const legend of ['How often?', 'How is it checked?', 'When?']) {
      expect(screen.getByRole('group', { name: legend })).toBeVisible()
    }
    expect(screen.getByRole('radio', { name: 'Any time' })).toBeChecked()
    expect(screen.queryByRole('radio', { name: 'Times a month' })).toBeNull()

    fireEvent.change(screen.getByLabelText('What do you want to do?'), {
      target: { value: '  Read 20 pages ' },
    })
    fireEvent.click(screen.getByRole('radio', { name: 'Specific days' }))
    fireEvent.click(screen.getByRole('checkbox', { name: 'Friday' }))
    fireEvent.click(screen.getByRole('radio', { name: 'Evening' }))
    fireEvent.click(screen.getByRole('button', { name: 'Create habit' }))

    await waitFor(() =>
      expect(api.createHabit).toHaveBeenCalledWith({
        name: 'Read 20 pages',
        time_of_day: 'evening',
        rule: {
          frequency: 'specific_days',
          check: 'manual',
          weekdays: [1, 2, 3, 4],
          times: null,
          source: null,
          source_ref: null,
          threshold: null,
          value: null,
        },
      }),
    )
    expect(onSaved).toHaveBeenCalled()
    expect(onOpenChange).toHaveBeenCalledWith(false)
  })

  it('reveals times a month under More options, with a stepper', async () => {
    newSheet()
    fireEvent.click(screen.getByRole('button', { name: 'More options' }))
    fireEvent.click(screen.getByRole('radio', { name: 'Times a month' }))
    expect(screen.getByText('times a month')).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Fewer' }))
    expect(screen.getByText('1')).toBeVisible()
    expect(screen.getByText('time a month')).toBeVisible()
  })

  it('reads a data rule as one line and needs a category for one', async () => {
    newSheet()
    fireEvent.change(screen.getByLabelText('What do you want to do?'), {
      target: { value: 'Less social' },
    })
    fireEvent.click(screen.getByRole('radio', { name: 'From your data' }))
    expect(screen.getByLabelText('Source')).toHaveValue('wake_time')
    expect(screen.getByLabelText('Threshold')).toHaveValue('before')
    expect(screen.getByLabelText('Time')).toHaveValue('07:00')
    fireEvent.change(screen.getByLabelText('Source'), { target: { value: 'screen_category' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create habit' }))
    expect(await screen.findByText('Pick a category.')).toBeVisible()
    expect(api.createHabit).not.toHaveBeenCalled()

    fireEvent.change(await screen.findByLabelText('Category'), { target: { value: 'social' } })
    expect(screen.getByLabelText('Hours')).toHaveValue(1)
    fireEvent.change(screen.getByLabelText('Minutes'), { target: { value: '15' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create habit' }))
    await waitFor(() =>
      expect(api.createHabit).toHaveBeenCalledWith(
        expect.objectContaining({
          rule: expect.objectContaining({
            check: 'data',
            source: 'screen_category',
            source_ref: 'social',
            threshold: 'at_most',
            value: 75,
          }),
        }),
      ),
    )
  })

  it('needs a name and says so', async () => {
    newSheet()
    fireEvent.click(screen.getByRole('button', { name: 'Create habit' }))
    expect(await screen.findByText('Give the habit a name.')).toBeVisible()
  })

  it('words a name already in use', async () => {
    api.createHabit.mockRejectedValue(new ApiError(409, "habit 'run' already exists"))
    newSheet()
    fireEvent.change(screen.getByLabelText('What do you want to do?'), { target: { value: 'Run' } })
    fireEvent.click(screen.getByRole('button', { name: 'Create habit' }))
    expect(await screen.findByRole('alert')).toHaveTextContent(
      'You already have a habit with this name.',
    )
  })
})

describe('Edit sheet', () => {
  it('saves a rename without asking how to apply it', async () => {
    render(<HabitSheet open onOpenChange={vi.fn()} habit={RUN} onSaved={vi.fn()} />)
    expect(screen.getByRole('dialog', { name: 'Edit habit' })).toBeVisible()
    expect(screen.getByText('3')).toBeVisible()
    expect(screen.queryByRole('group', { name: 'Apply this change' })).toBeNull()
    fireEvent.change(screen.getByLabelText('What do you want to do?'), {
      target: { value: 'Go for a run' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    await waitFor(() =>
      expect(api.updateHabit).toHaveBeenCalledWith('run', {
        name: 'Go for a run',
        time_of_day: 'anytime',
      }),
    )
  })

  it('asks how to apply a schedule change, from today by default', async () => {
    render(<HabitSheet open onOpenChange={vi.fn()} habit={RUN} onSaved={vi.fn()} />)
    fireEvent.click(screen.getByRole('button', { name: 'More' }))
    expect(screen.getByRole('group', { name: 'Apply this change' })).toBeVisible()
    expect(screen.getByRole('radio', { name: 'From today' })).toBeChecked()
    fireEvent.click(screen.getByRole('radio', { name: 'To all past days too' }))
    fireEvent.click(screen.getByRole('button', { name: 'Save' }))
    await waitFor(() =>
      expect(api.updateHabit).toHaveBeenCalledWith(
        'run',
        expect.objectContaining({
          rule: expect.objectContaining({ frequency: 'times_a_week', times: 4 }),
          apply: 'all_days',
        }),
      ),
    )
  })
})

describe('Freeze sheet', () => {
  it('freezes this habit from the given day, with a reason', async () => {
    const onSaved = vi.fn()
    render(
      <FreezeSheet open onOpenChange={vi.fn()} habit={RUN} day="2026-11-14" onSaved={onSaved} />,
    )
    expect(screen.getByRole('dialog', { name: 'Freeze Run' })).toBeVisible()
    expect(screen.getByLabelText('From')).toHaveValue('2026-11-14')
    expect(screen.getByLabelText('To')).toHaveValue('2026-11-14')
    fireEvent.change(screen.getByLabelText('To'), { target: { value: '2026-11-20' } })
    fireEvent.change(screen.getByLabelText(/Reason/), { target: { value: ' Holiday ' } })
    fireEvent.click(screen.getByRole('button', { name: 'Freeze' }))
    await waitFor(() =>
      expect(api.createFreeze).toHaveBeenCalledWith({
        habit: 'run',
        start_on: '2026-11-14',
        end_on: '2026-11-20',
        reason: 'Holiday',
      }),
    )
    expect(onSaved).toHaveBeenCalled()
  })

  it('freezes every habit with the switch on', async () => {
    render(
      <FreezeSheet open onOpenChange={vi.fn()} habit={RUN} day="2026-11-14" onSaved={vi.fn()} />,
    )
    fireEvent.click(screen.getByRole('switch', { name: 'Freeze all habits' }))
    expect(screen.getByRole('dialog', { name: 'Freeze all habits' })).toBeVisible()
    fireEvent.click(screen.getByRole('button', { name: 'Freeze' }))
    await waitFor(() =>
      expect(api.createFreeze).toHaveBeenCalledWith({
        start_on: '2026-11-14',
        end_on: '2026-11-14',
      }),
    )
  })

  it('refuses a To before From', async () => {
    render(
      <FreezeSheet open onOpenChange={vi.fn()} habit={RUN} day="2026-11-14" onSaved={vi.fn()} />,
    )
    fireEvent.change(screen.getByLabelText('To'), { target: { value: '2026-11-10' } })
    fireEvent.click(screen.getByRole('button', { name: 'Freeze' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('To can’t be before From.')
    expect(api.createFreeze).not.toHaveBeenCalled()
  })
})
