import { describe, expect, it } from 'vitest'

import { budgetSlug, budgetState, budgetSummary } from './screenManage'

describe('budgets', () => {
  it('derives a slug and a readable summary', () => {
    expect(budgetSlug('waste', 'day')).toBe('waste-day-cap')
    expect(budgetSummary({ comparator: 'at_most', target_value: 90, period: 'day' })).toBe(
      '≤ 1h 30m a day',
    )
  })

  it('reads an inclusive end date as a last day, then as ended', () => {
    const budget = { active_from: '2026-08-01', active_to: '2026-08-10' }
    expect(budgetState(budget, '2026-08-10')).toEqual({
      label: 'last day 2026-08-10',
      open: false,
      counting: true,
    })
    expect(budgetState(budget, '2026-08-11')).toEqual({
      label: 'ended 2026-08-10',
      open: false,
      counting: false,
    })
    expect(budgetState({ active_from: '2026-08-01', active_to: null }, '2027-01-01')).toEqual({
      label: 'active',
      open: true,
      counting: true,
    })
    expect(budgetState({ active_from: '2026-09-01', active_to: null }, '2026-08-01').counting).toBe(
      false,
    )
  })
})
