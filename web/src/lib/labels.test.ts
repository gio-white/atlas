import { describe, expect, it } from 'vitest'

import {
  AGGREGATION_LABEL,
  DIRECTION_LABEL,
  isManagedMetric,
  metricSummary,
  VALUE_TYPE_LABEL,
} from './labels'

describe('labels', () => {
  it('never shows a raw value', () => {
    const labels = [
      ...Object.values(VALUE_TYPE_LABEL),
      ...Object.values(AGGREGATION_LABEL),
      ...Object.values(DIRECTION_LABEL),
    ]
    for (const label of labels) {
      expect(label).not.toMatch(/_/)
      expect(label[0]).toBe(label[0].toUpperCase())
    }
    expect(DIRECTION_LABEL.higher_is_better).toBe('More is better')
    expect(AGGREGATION_LABEL.sum).toBe('Add up the day')
    expect(AGGREGATION_LABEL.last).toBe('Keep the latest')
  })

  it('summarises a metric in plain words, with its unit when it has one', () => {
    expect(
      metricSummary({
        value_type: 'count',
        aggregation: 'sum',
        direction: 'higher_is_better',
        unit: 'reps',
      }),
    ).toBe('Count · Add up the day · More is better · reps')
    expect(
      metricSummary({
        value_type: 'rating',
        aggregation: 'mean',
        direction: 'neutral',
        unit: null,
      }),
    ).toBe('Rating, 1 to 10 · Average the day · Neither')
  })

  it('counts hand-made and habit-made metrics as yours to manage, not app or journal ones', () => {
    expect(isManagedMetric({ origin: 'manual' })).toBe(true)
    expect(isManagedMetric({ origin: 'habit' })).toBe(true)
    expect(isManagedMetric({ origin: 'screen' })).toBe(false)
    expect(isManagedMetric({ origin: 'journal' })).toBe(false)
  })
})
