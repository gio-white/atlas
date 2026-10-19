import { describe, expect, it } from 'vitest'

import type { EntertainmentTitle } from './api'
import {
  categoryFromPath,
  filterTitles,
  type LibraryFilter,
  parseCategory,
  parseSortKey,
  parseTags,
  sortTitles,
  statusCounts,
  tagsIn,
  uniqueTitleSlug,
} from './entertainment'

function title(
  overrides: Partial<EntertainmentTitle> & Pick<EntertainmentTitle, 'slug' | 'name'>,
): EntertainmentTitle {
  return {
    kind: 'film',
    creator: null,
    recommended_by: null,
    status: 'queued',
    started_on: null,
    finished_on: null,
    progress: null,
    note: null,
    rating: null,
    link: null,
    topics: [],
    image: null,
    created_at: '2026-08-01T12:00:00+00:00',
    ...overrides,
  }
}

const NO_FILTER: LibraryFilter = { status: null, tag: null, minRating: null, query: '' }

const LIBRARY = [
  title({
    slug: 'interstellar',
    name: 'Interstellar',
    status: 'done',
    rating: 5,
    finished_on: '2026-08-10',
    topics: [{ slug: 'physics', name: 'Physics' }],
  }),
  title({ slug: 'the-office', name: 'The Office', kind: 'series', status: 'in_progress' }),
  title({
    slug: 'dune',
    name: 'Dune',
    kind: 'book',
    creator: 'Frank Herbert',
    rating: 3,
    created_at: '2026-08-05T12:00:00+00:00',
  }),
  title({ slug: 'kind-of-blue', name: 'Kind of Blue', kind: 'music', status: 'done', rating: 4 }),
]

describe('filterTitles', () => {
  it('groups film, series, anime and video under videos', () => {
    const slugs = filterTitles(LIBRARY, 'videos', NO_FILTER).map((row) => row.slug)
    expect(slugs).toEqual(['interstellar', 'the-office'])
  })

  it('combines status, tag, rating and text filters', () => {
    expect(filterTitles(LIBRARY, 'all', { ...NO_FILTER, status: 'done' })).toHaveLength(2)
    expect(filterTitles(LIBRARY, 'all', { ...NO_FILTER, tag: 'physics' })[0].slug).toBe(
      'interstellar',
    )
    expect(filterTitles(LIBRARY, 'all', { ...NO_FILTER, minRating: 4 })).toHaveLength(2)
    expect(filterTitles(LIBRARY, 'all', { ...NO_FILTER, query: 'herbert' })[0].slug).toBe('dune')
  })
})

describe('sortTitles', () => {
  it('keeps unrated titles last in either direction', () => {
    const desc = sortTitles(LIBRARY, 'rating', 'desc').map((row) => row.slug)
    expect(desc).toEqual(['interstellar', 'kind-of-blue', 'dune', 'the-office'])
    const asc = sortTitles(LIBRARY, 'rating', 'asc').map((row) => row.slug)
    expect(asc).toEqual(['dune', 'kind-of-blue', 'interstellar', 'the-office'])
  })

  it('sorts by name and by newest added', () => {
    expect(sortTitles(LIBRARY, 'name', 'asc')[0].slug).toBe('dune')
    expect(sortTitles(LIBRARY, 'created_at', 'desc')[0].slug).toBe('dune')
  })
})

describe('helpers', () => {
  it('counts statuses and collects tags', () => {
    expect(statusCounts(LIBRARY)).toEqual({ queued: 1, in_progress: 1, done: 2, dropped: 0 })
    expect(tagsIn(LIBRARY)).toEqual([{ slug: 'physics', name: 'Physics' }])
  })

  it('parses URL params with safe fallbacks', () => {
    expect(parseCategory('books')).toBe('books')
    expect(parseCategory('nope')).toBe('all')
    expect(categoryFromPath('music')).toBe('music')
    expect(categoryFromPath('insights')).toBeNull()
    expect(parseSortKey('rating')).toBe('rating')
    expect(parseSortKey(null)).toBe('created_at')
  })

  it('derives a slug that avoids existing titles', () => {
    expect(uniqueTitleSlug('Dune', 'film', ['interstellar'])).toBe('dune')
    expect(uniqueTitleSlug('Dune', 'film', ['dune'])).toBe('dune-film')
    expect(uniqueTitleSlug('Dune', 'film', ['dune', 'dune-film'])).toBe('dune-film-2')
  })

  it('splits typed tags into unique slugs', () => {
    expect(parseTags('Sci-Fi, space opera,, sci-fi ')).toEqual(['sci-fi', 'space-opera'])
  })
})
