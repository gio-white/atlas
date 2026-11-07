import { describe, expect, it } from 'vitest'

import type { ScreenCategoryShare } from '@/lib/api'

import { CATEGORY_PALETTE, categorySlices, minuteTicks } from './Charts'

function share(slug: string, minutes: number): ScreenCategoryShare {
  return { slug, name: slug, judgment: 'waste', minutes, share: 0, apps: [] }
}

describe('categorySlices', () => {
  it('gives categories with the same judgment different colours', () => {
    const [social, video] = categorySlices([share('social', 60), share('video', 30)])
    expect(social.swatch).not.toBe(video.swatch)
    expect(social.detail).toBe('Bad')
  })

  it('keeps a colour when the ranking changes', () => {
    const known = ['news', 'social', 'video']
    const first = categorySlices([share('social', 60), share('video', 30)], known)
    const second = categorySlices([share('video', 90), share('social', 10)], known)
    expect(first.find((slice) => slice.slug === 'video')?.swatch).toBe(
      second.find((slice) => slice.slug === 'video')?.swatch,
    )
  })

  it('never uses the judgment colours', () => {
    const swatches = CATEGORY_PALETTE.map((item) => item.swatch)
    expect(swatches).not.toContain('bg-good')
    expect(swatches).not.toContain('bg-bad')
    expect(swatches).not.toContain('bg-warn')
  })
})

describe('minuteTicks', () => {
  it('picks a readable step that covers the tallest bar', () => {
    expect(minuteTicks(50)).toEqual([0, 15, 30, 45, 60])
    expect(minuteTicks(200)).toEqual([0, 60, 120, 180, 240])
    expect(minuteTicks(1)).toEqual([0, 15])
  })
})
