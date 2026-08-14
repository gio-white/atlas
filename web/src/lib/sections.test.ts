import { describe, expect, it } from 'vitest'

import { LIFE_SECTIONS } from './sections'

describe('LIFE_SECTIONS', () => {
  it('defines sleep, health, adventure, and entertainment', () => {
    expect(LIFE_SECTIONS.map((section) => section.slug)).toEqual([
      'sleep',
      'health',
      'adventure',
      'entertainment',
    ])
  })

  it('uses unique paths that match the slug', () => {
    const paths = LIFE_SECTIONS.map((section) => section.path)
    expect(new Set(paths).size).toBe(paths.length)
    for (const section of LIFE_SECTIONS) {
      expect(section.path).toBe(`/${section.slug}`)
    }
  })
})
