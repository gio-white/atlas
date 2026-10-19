import type { EntertainmentKind, EntertainmentStatus, EntertainmentTitle } from './api'

export const KINDS: EntertainmentKind[] = [
  'film',
  'series',
  'anime',
  'video',
  'book',
  'podcast',
  'music',
  'other',
]

export const KIND_LABEL: Record<EntertainmentKind, string> = {
  film: 'Film',
  series: 'Series',
  anime: 'Anime',
  video: 'Video',
  book: 'Book',
  podcast: 'Podcast',
  music: 'Music',
  other: 'Other',
}

export type CategoryId = 'all' | 'videos' | 'books' | 'podcasts' | 'music' | 'other'

export type Category = {
  id: CategoryId
  label: string
  kinds: EntertainmentKind[]
}

export const CATEGORIES: Category[] = [
  { id: 'all', label: 'All', kinds: KINDS },
  { id: 'videos', label: 'Videos', kinds: ['film', 'series', 'anime', 'video'] },
  { id: 'books', label: 'Books', kinds: ['book'] },
  { id: 'podcasts', label: 'Podcasts', kinds: ['podcast'] },
  { id: 'music', label: 'Music', kinds: ['music'] },
  { id: 'other', label: 'Other', kinds: ['other'] },
]

export const STATUSES: { id: EntertainmentStatus; label: string }[] = [
  { id: 'queued', label: 'Wishlist' },
  { id: 'in_progress', label: 'In progress' },
  { id: 'done', label: 'Done' },
  { id: 'dropped', label: 'Dropped' },
]

export const STATUS_LABEL: Record<EntertainmentStatus, string> = {
  queued: 'Wishlist',
  in_progress: 'In progress',
  done: 'Done',
  dropped: 'Dropped',
}

const STATUS_ORDER: Record<EntertainmentStatus, number> = {
  in_progress: 0,
  queued: 1,
  done: 2,
  dropped: 3,
}

export function parseCategory(raw: string | null): CategoryId {
  return CATEGORIES.some((category) => category.id === raw) ? (raw as CategoryId) : 'all'
}

export function categoryFor(id: CategoryId): Category {
  return CATEGORIES.find((category) => category.id === id) ?? CATEGORIES[0]
}

export function inCategory(title: EntertainmentTitle, id: CategoryId): boolean {
  return categoryFor(id).kinds.includes(title.kind)
}

export type LibraryFilter = {
  status: EntertainmentStatus | null
  tag: string | null
  minRating: number | null
  query: string
}

export function filterTitles(
  titles: EntertainmentTitle[],
  category: CategoryId,
  filter: LibraryFilter,
): EntertainmentTitle[] {
  const query = filter.query.trim().toLowerCase()
  return titles.filter((title) => {
    if (!inCategory(title, category)) return false
    if (filter.status !== null && title.status !== filter.status) return false
    if (filter.tag !== null && !title.topics.some((topic) => topic.slug === filter.tag)) {
      return false
    }
    if (filter.minRating !== null && (title.rating ?? 0) < filter.minRating) return false
    if (query === '') return true
    return [title.name, title.creator, title.recommended_by, title.note]
      .concat(title.topics.map((topic) => topic.name))
      .some((field) => field?.toLowerCase().includes(query))
  })
}

export type SortKey = 'name' | 'kind' | 'status' | 'rating' | 'finished_on' | 'created_at'
export type SortDir = 'asc' | 'desc'

export const SORT_KEYS: SortKey[] = [
  'name',
  'kind',
  'status',
  'rating',
  'finished_on',
  'created_at',
]

export function parseSortKey(raw: string | null): SortKey {
  return SORT_KEYS.includes(raw as SortKey) ? (raw as SortKey) : 'created_at'
}

export function defaultDir(key: SortKey): SortDir {
  return key === 'name' || key === 'kind' || key === 'status' ? 'asc' : 'desc'
}

function sortValue(title: EntertainmentTitle, key: SortKey): string | number | null {
  switch (key) {
    case 'name':
      return title.name.toLowerCase()
    case 'kind':
      return KIND_LABEL[title.kind]
    case 'status':
      return STATUS_ORDER[title.status]
    case 'rating':
      return title.rating
    case 'finished_on':
      return title.finished_on
    case 'created_at':
      return title.created_at
  }
}

/** Sorts by one column; empty values always sink to the bottom, ties fall back to name. */
export function sortTitles(
  titles: EntertainmentTitle[],
  key: SortKey,
  dir: SortDir,
): EntertainmentTitle[] {
  const sign = dir === 'asc' ? 1 : -1
  return [...titles].sort((a, b) => {
    const left = sortValue(a, key)
    const right = sortValue(b, key)
    if (left === null && right !== null) return 1
    if (right === null && left !== null) return -1
    if (left !== null && right !== null && left !== right) {
      return (left < right ? -1 : 1) * sign
    }
    return a.name.toLowerCase().localeCompare(b.name.toLowerCase())
  })
}

export function statusCounts(titles: EntertainmentTitle[]): Record<EntertainmentStatus, number> {
  const counts: Record<EntertainmentStatus, number> = {
    queued: 0,
    in_progress: 0,
    done: 0,
    dropped: 0,
  }
  for (const title of titles) counts[title.status] += 1
  return counts
}

export function tagsIn(titles: EntertainmentTitle[]): { slug: string; name: string }[] {
  const tags = new Map<string, string>()
  for (const title of titles) {
    for (const topic of title.topics) tags.set(topic.slug, topic.name)
  }
  return [...tags.entries()]
    .map(([slug, name]) => ({ slug, name }))
    .sort((a, b) => a.name.localeCompare(b.name))
}

export function slugify(text: string): string {
  return text
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

/** A slug for a new title that does not collide with one already in the library. */
export function uniqueTitleSlug(
  name: string,
  kind: EntertainmentKind,
  taken: Iterable<string>,
): string {
  const used = new Set(taken)
  const base = slugify(name)
  if (base === '' || !used.has(base)) return base
  const withKind = `${base}-${kind}`
  if (!used.has(withKind)) return withKind
  let index = 2
  while (used.has(`${withKind}-${index}`)) index += 1
  return `${withKind}-${index}`
}

/** Splits a free-typed tag field ("sci-fi, Space opera") into tag slugs. */
export function parseTags(text: string): string[] {
  const slugs = text
    .split(',')
    .map(slugify)
    .filter((slug) => slug !== '')
  return [...new Set(slugs)]
}
