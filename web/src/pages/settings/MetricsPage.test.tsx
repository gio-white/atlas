// @vitest-environment jsdom
import '@testing-library/jest-dom/vitest'

import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { Habit, Metric } from '@/lib/api'

const api = vi.hoisted(() => ({
  listMetrics: vi.fn(),
  listHabits: vi.fn(),
  createMetric: vi.fn(),
  updateMetric: vi.fn(),
  archiveMetric: vi.fn(),
}))

vi.mock('@/lib/api', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/lib/api')>()),
  ...api,
}))

import { ApiError } from '@/lib/api'
import { MetricsPage } from './MetricsPage'

function metric(slug: string, name: string, extra: Partial<Metric> = {}): Metric {
  return {
    id: slug.length,
    slug,
    origin: 'manual',
    name,
    value_type: 'count',
    unit: null,
    aggregation: 'sum',
    direction: 'higher_is_better',
    archived_at: null,
    ...extra,
  }
}

const METRICS = [
  metric('pushups', 'Pushups', { unit: 'reps' }),
  metric('meditate', 'Meditate', { origin: 'habit', value_type: 'bool' }),
  metric('instagram', 'Instagram', { origin: 'screen', value_type: 'duration' }),
  metric('journal', 'Journal', { origin: 'journal', value_type: 'text', aggregation: 'last' }),
]

beforeEach(() => {
  api.listMetrics.mockResolvedValue(METRICS)
  api.listHabits.mockResolvedValue([
    { slug: 'meditate', name: 'Meditate daily', metric: 'meditate', archived_at: null } as Habit,
  ])
})

afterEach(() => {
  cleanup()
  vi.clearAllMocks()
})

describe('Settings → Metrics', () => {
  it('lists the metrics you manage, in plain words, and leaves out app and journal ones', async () => {
    render(<MetricsPage />)

    expect(await screen.findByText('Pushups')).toBeInTheDocument()
    expect(screen.getByText('Count · Add up the day · More is better · reps')).toBeInTheDocument()
    expect(screen.getByText('Made for a habit')).toBeInTheDocument()
    expect(screen.queryByText('Instagram')).not.toBeInTheDocument()
    expect(screen.queryByText('Journal')).not.toBeInTheDocument()

    const text = document.body.textContent ?? ''
    for (const raw of ['pushups', 'higher_is_better', 'sum', 'manual', 'bool']) {
      expect(text).not.toContain(raw)
    }
  })

  it('creates a metric from a name, without a slug or an area', async () => {
    api.createMetric.mockResolvedValue(metric('glasses-of-water', 'Glasses of water'))
    render(<MetricsPage />)

    fireEvent.change(await screen.findByLabelText('Name'), {
      target: { value: '  Glasses of water ' },
    })
    fireEvent.change(screen.getByLabelText('Which way is better'), {
      target: { value: 'higher_is_better' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Add metric' }))

    await waitFor(() => expect(api.createMetric).toHaveBeenCalled())
    expect(api.createMetric).toHaveBeenCalledWith({
      name: 'Glasses of water',
      value_type: 'count',
      aggregation: 'sum',
      direction: 'higher_is_better',
      unit: undefined,
    })
    await waitFor(() => expect(api.listMetrics).toHaveBeenCalledTimes(2))
  })

  it('keeps the latest value for a note, since notes cannot be added up', async () => {
    api.createMetric.mockResolvedValue(metric('gratitude', 'Gratitude'))
    render(<MetricsPage />)

    fireEvent.change(await screen.findByLabelText('Name'), { target: { value: 'Gratitude' } })
    fireEvent.change(screen.getByLabelText('What you record'), { target: { value: 'text' } })
    expect(screen.getByLabelText('Several values in one day')).toBeDisabled()
    fireEvent.click(screen.getByRole('button', { name: 'Add metric' }))

    await waitFor(() =>
      expect(api.createMetric).toHaveBeenCalledWith(
        expect.objectContaining({ value_type: 'text', aggregation: 'last' }),
      ),
    )
  })

  it('says so in plain words when the name is taken', async () => {
    api.createMetric.mockRejectedValue(new ApiError(409, "metric 'pushups' already exists"))
    render(<MetricsPage />)

    fireEvent.change(await screen.findByLabelText('Name'), { target: { value: 'Pushups' } })
    fireEvent.click(screen.getByRole('button', { name: 'Add metric' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'A metric with that name already exists.',
    )
  })

  it('edits the name, unit and direction', async () => {
    api.updateMetric.mockResolvedValue(METRICS[0])
    render(<MetricsPage />)

    const row = (await screen.findByText('Pushups')).closest('li') as HTMLElement
    fireEvent.click(within(row).getByRole('button', { name: 'Edit' }))
    fireEvent.change(within(row).getByLabelText('Name'), { target: { value: 'Push-ups' } })
    fireEvent.change(within(row).getByLabelText('Unit (optional)'), { target: { value: '' } })
    fireEvent.click(within(row).getByRole('button', { name: 'Save' }))

    await waitFor(() =>
      expect(api.updateMetric).toHaveBeenCalledWith('pushups', {
        name: 'Push-ups',
        unit: null,
        direction: 'higher_is_better',
      }),
    )
  })

  it('asks before archiving and names the habit that depends on the metric', async () => {
    api.archiveMetric.mockResolvedValue(METRICS[1])
    render(<MetricsPage />)

    const row = (await screen.findByText('Meditate')).closest('li') as HTMLElement
    fireEvent.click(within(row).getByRole('button', { name: 'Archive' }))

    expect(api.archiveMetric).not.toHaveBeenCalled()
    expect(
      within(row).getByText(/Meditate daily uses it and will stop showing/),
    ).toBeInTheDocument()

    fireEvent.click(within(row).getByRole('button', { name: 'Archive metric' }))
    await waitFor(() => expect(api.archiveMetric).toHaveBeenCalledWith('meditate'))
  })
})
