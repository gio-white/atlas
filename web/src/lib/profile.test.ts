import { describe, expect, it } from 'vitest'

import { initials, normalizeDisplayName } from './profile'

describe('profile', () => {
  it('falls back to Alex when the name is blank', () => {
    expect(normalizeDisplayName('')).toBe('Alex')
    expect(normalizeDisplayName('  ')).toBe('Alex')
    expect(normalizeDisplayName(' Sam ')).toBe('Sam')
  })

  it('builds initials from the first letters', () => {
    expect(initials('Alex')).toBe('A')
    expect(initials('Ada Lovelace')).toBe('AL')
  })
})
