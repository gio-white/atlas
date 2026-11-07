import { describe, expect, it } from 'vitest'
import { LIFE_SECTIONS } from '@/lib/sections'
import NAVIGATION from '../../docs/product/navigation.md?raw'
import APP from './App.tsx?raw'

function appRoutes(source: string): string[] {
  const routes = new Set<string>()
  if (/<Route\s+index\b/.test(source)) routes.add('/')
  for (const match of source.matchAll(/<Route[^>]*\spath="([^"]+)"/g)) {
    if (match[1] !== '*') routes.add(`/${match[1].replace(/^\//, '')}`)
  }
  // Section pages are generated from LIFE_SECTIONS, so their paths are not literals in App.tsx.
  if (source.includes('LIFE_SECTIONS')) {
    for (const section of LIFE_SECTIONS) routes.add(section.path)
  }
  return [...routes].sort()
}

function documentedRoutes(markdown: string): Set<string> {
  const routes = new Set<string>()
  for (const match of markdown.matchAll(/^\|\s*`(\/[^`]*)`\s*\|/gm)) routes.add(match[1])
  return routes
}

describe('docs drift: SPA routes', () => {
  it('lists every App.tsx route in docs/product/navigation.md', () => {
    const documented = documentedRoutes(NAVIGATION)
    const missing = appRoutes(APP).filter((route) => !documented.has(route))
    expect(missing, 'add these routes to the table in docs/product/navigation.md').toEqual([])
  })

  it('catches a route added without docs', () => {
    const withProbe = APP.replace(
      '<Route path="history"',
      '<Route path="undocumented-probe" element={null} />\n<Route path="history"',
    )
    const documented = documentedRoutes(NAVIGATION)
    expect(appRoutes(withProbe).filter((route) => !documented.has(route))).toEqual([
      '/undocumented-probe',
    ])
  })
})
