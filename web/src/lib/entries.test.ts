import { describe, expect, it } from 'vitest'

import type { Entry, Metric } from './api'
import {
  amendBodyFromDraft,
  draftFromEntry,
  entryValueLabel,
  groupEntriesByDay,
  historyRange,
} from './entries'

function entry(overrides: Partial<Entry> & Pick<Entry, 'id' | 'occurred_on'>): Entry {
  return {
    metric: 'pushups',
    occurred_at: null,
    value_num: 40,
    value_bool: null,
    value_text: null,
    note: null,
    source: 'api',
    created_at: '2026-08-14T12:00:00+00:00',
    ...overrides,
  }
}

function metric(overrides: Partial<Metric> = {}): Metric {
  return {
    id: 1,
    slug: 'pushups',
    area: 'health',
    name: 'Pushups',
    value_type: 'count',
    unit: 'reps',
    aggregation: 'sum',
    direction: 'higher_is_better',
    archived_at: null,
    ...overrides,
  }
}

describe('historyRange', () => {
  it('spans the given number of days ending on as-of', () => {
    expect(historyRange('2026-08-14', 7)).toEqual({ start: '2026-08-08', end: '2026-08-14' })
    expect(historyRange('2026-03-01', 2)).toEqual({ start: '2026-02-28', end: '2026-03-01' })
  })
})

describe('groupEntriesByDay', () => {
  it('keeps newest-first order and starts a block per day', () => {
    const days = groupEntriesByDay([
      entry({ id: 3, occurred_on: '2026-08-14' }),
      entry({ id: 2, occurred_on: '2026-08-14' }),
      entry({ id: 1, occurred_on: '2026-08-12' }),
    ])
    expect(days.map((day) => [day.day, day.entries.map((item) => item.id)])).toEqual([
      ['2026-08-14', [3, 2]],
      ['2026-08-12', [1]],
    ])
  })
})

describe('entryValueLabel', () => {
  it('adds the unit to numbers only', () => {
    expect(entryValueLabel(entry({ id: 1, occurred_on: '2026-08-14' }), metric())).toBe('40 reps')
    expect(
      entryValueLabel(
        entry({ id: 1, occurred_on: '2026-08-14', value_num: null, value_bool: true }),
        metric({ value_type: 'bool', unit: null }),
      ),
    ).toBe('yes')
    expect(entryValueLabel(entry({ id: 1, occurred_on: '2026-08-14' }), undefined)).toBe('40')
  })
})

describe('amendBodyFromDraft', () => {
  const base = entry({ id: 1, occurred_on: '2026-08-14', note: 'old' })

  it('sends only what changed', () => {
    const draft = { ...draftFromEntry(base), raw: '45' }
    expect(amendBodyFromDraft(base, metric(), draft)).toEqual({ value: 45 })
    expect(amendBodyFromDraft(base, metric(), draftFromEntry(base))).toEqual({})
  })

  it('clears a blanked note and moves the date', () => {
    const draft = { ...draftFromEntry(base), note: '  ', occurredOn: '2026-08-13' }
    expect(amendBodyFromDraft(base, metric(), draft)).toEqual({
      occurred_on: '2026-08-13',
      note: null,
    })
  })

  it('flips a bool and skips value edits when the metric is unknown', () => {
    const done = entry({ id: 2, occurred_on: '2026-08-14', value_num: null, value_bool: true })
    const bool = metric({ value_type: 'bool', unit: null })
    expect(amendBodyFromDraft(done, bool, { ...draftFromEntry(done), boolValue: false })).toEqual({
      value: false,
    })
    expect(amendBodyFromDraft(base, undefined, { ...draftFromEntry(base), raw: '99' })).toEqual({})
  })

  it('rejects a non-numeric value for numeric metrics', () => {
    expect(() => amendBodyFromDraft(base, metric(), { ...draftFromEntry(base), raw: 'x' })).toThrow(
      'value must be a number',
    )
  })
})
