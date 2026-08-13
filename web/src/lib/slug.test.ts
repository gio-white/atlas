import { describe, expect, it } from 'vitest'

import { isValidSlug } from './slug'

describe('isValidSlug', () => {
  it('accepts lowercase hyphenated slugs', () => {
    expect(isValidSlug('pushups-daily')).toBe(true)
    expect(isValidSlug('Health_1')).toBe(false)
    expect(isValidSlug('')).toBe(false)
  })
})
