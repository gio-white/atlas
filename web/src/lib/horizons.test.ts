import { describe, expect, it } from 'vitest'

import { PARENT_HORIZON, slugFromName } from './horizons'

describe('PARENT_HORIZON', () => {
  it('maps each horizon to the previous one', () => {
    expect(PARENT_HORIZON.long).toBeNull()
    expect(PARENT_HORIZON.medium).toBe('long')
    expect(PARENT_HORIZON.short).toBe('medium')
  })
})

describe('slugFromName', () => {
  it('hyphenates a lowercase slug', () => {
    expect(slugFromName('Durable Health')).toBe('durable-health')
    expect(slugFromName('  Workout this week!  ')).toBe('workout-this-week')
  })
})
