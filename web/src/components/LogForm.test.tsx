// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import type { Metric } from '@/lib/api'

import { LogForm } from './LogForm'

function metric(slug: string, name: string, overrides: Partial<Metric> = {}): Metric {
  return {
    id: slug.length,
    slug,
    name,
    origin: 'manual',
    value_type: 'count',
    unit: null,
    aggregation: 'sum',
    direction: 'higher_is_better',
    archived_at: null,
    ...overrides,
  }
}

afterEach(cleanup)

describe('LogForm', () => {
  const metrics = [
    metric('books', 'Books'),
    metric('weight', 'Weight', { value_type: 'quantity', unit: 'kg' }),
  ]

  it('starts with no metric chosen and an empty value', () => {
    render(<LogForm metrics={metrics} occurredOn="2026-11-07" onLogged={() => {}} />)
    expect((screen.getByLabelText('Metric') as HTMLSelectElement).value).toBe('')
    expect((screen.getByLabelText('Value') as HTMLInputElement).value).toBe('')
  })

  it('shows the chosen metric’s unit and a placeholder instead of 0', () => {
    render(<LogForm metrics={metrics} occurredOn="2026-11-07" onLogged={() => {}} />)
    fireEvent.change(screen.getByLabelText('Metric'), { target: { value: 'weight' } })
    expect(screen.getByTestId('log-unit').textContent).toBe('kg')
    const value = screen.getByLabelText('Value') as HTMLInputElement
    expect(value.value).toBe('')
    expect(value.placeholder).toBe('Amount')
  })
})
