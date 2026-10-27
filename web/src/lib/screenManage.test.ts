import { describe, expect, it } from 'vitest'

import type { ScreenSessionRecord } from './api'
import {
  budgetIsActive,
  budgetSlug,
  budgetSummary,
  draftFromSession,
  sessionTimeLabel,
  sessionUpdateBody,
  toLocalInput,
} from './screenManage'

function record(overrides: Partial<ScreenSessionRecord> = {}): ScreenSessionRecord {
  const started = new Date(2026, 7, 14, 20, 0).toISOString()
  const ended = new Date(2026, 7, 14, 20, 30).toISOString()
  return {
    id: 1,
    app: 'instagram',
    device: 'iphone',
    started_at: started,
    ended_at: ended,
    minutes: 30,
    occurred_on: '2026-08-14',
    note: null,
    source: 'api',
    created_at: ended,
    entry_id: 7,
    ...overrides,
  }
}

describe('budgets', () => {
  it('derives a slug and a readable summary', () => {
    expect(budgetSlug('waste', 'day')).toBe('waste-day-cap')
    expect(budgetSummary({ comparator: 'at_most', target_value: 90, period: 'day' })).toBe(
      '≤ 1h 30m a day',
    )
  })

  it('is active inside its window only', () => {
    const budget = { active_from: '2026-08-01', active_to: '2026-08-10' }
    expect(budgetIsActive(budget, '2026-08-10')).toBe(true)
    expect(budgetIsActive(budget, '2026-08-11')).toBe(false)
    expect(budgetIsActive({ active_from: '2026-08-01', active_to: null }, '2027-01-01')).toBe(true)
  })
})

describe('sessions', () => {
  it('shows local times for intervals and a label for duration-only rows', () => {
    expect(sessionTimeLabel(record())).toBe('20:00–20:30')
    expect(sessionTimeLabel(record({ started_at: null, ended_at: null }))).toBe('duration only')
    expect(toLocalInput(new Date(2026, 0, 2, 3, 4).toISOString())).toBe('2026-01-02T03:04')
  })

  it('sends both interval ends when either changes', () => {
    const row = record()
    const draft = { ...draftFromSession(row), ended: '2026-08-14T21:00' }
    expect(sessionUpdateBody(row, draft)).toEqual({
      started_at: new Date(2026, 7, 14, 20, 0).toISOString(),
      ended_at: new Date(2026, 7, 14, 21, 0).toISOString(),
    })
    expect(sessionUpdateBody(row, draftFromSession(row))).toEqual({})
  })

  it('edits minutes, device, and note on a duration-only row', () => {
    const row = record({ started_at: null, ended_at: null, note: 'x' })
    const draft = { ...draftFromSession(row), minutes: '45', device: '', note: '' }
    expect(sessionUpdateBody(row, draft)).toEqual({ minutes: 45, device: null, note: null })
    expect(() => sessionUpdateBody(row, { ...draft, minutes: '0' })).toThrow('minutes')
  })
})
