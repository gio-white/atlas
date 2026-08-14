import { describe, expect, it } from 'vitest'

import { summarizeGoals } from './goalsSummary'

describe('summarizeGoals', () => {
  it('averages fractions and counts pace buckets', () => {
    const summary = summarizeGoals([
      { pace: 'on_track', fraction: 0.5 },
      { pace: 'on_track', fraction: 0.5 },
      { pace: 'behind', fraction: 0.8 },
      { pace: 'ahead', fraction: 0.8 },
      { pace: 'no_data', fraction: null },
    ])
    expect(summary.overall).toBeCloseTo(0.65)
    expect(summary.onTrack).toBe(2)
    expect(summary.behind).toBe(1)
    expect(summary.ahead).toBe(1)
  })

  it('returns null overall when no fractions exist', () => {
    expect(summarizeGoals([]).overall).toBeNull()
  })
})
