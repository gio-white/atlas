import { describe, expect, it } from 'vitest'

import { parseLogValue, rawFromEntry } from './value'

describe('parseLogValue', () => {
  it('uses the bool flag and parses numbers', () => {
    expect(parseLogValue('bool', '', false)).toBe(false)
    expect(parseLogValue('count', '40')).toBe(40)
    expect(parseLogValue('text', 'ok')).toBe('ok')
    expect(parseLogValue('quantity', '')).toBeNull()
  })

  it('rejects non-numeric input for numeric types', () => {
    expect(() => parseLogValue('count', 'nope')).toThrow('value must be a number')
  })
})

describe('rawFromEntry', () => {
  it('prefers bool, then text, then number', () => {
    expect(rawFromEntry(null, true, null)).toBe('true')
    expect(rawFromEntry(null, null, 'ok')).toBe('ok')
    expect(rawFromEntry(12, null, null)).toBe('12')
  })
})
