export const LIFE_SECTIONS = [
  {
    slug: 'sleep',
    path: '/sleep',
    label: 'Sleep',
    description: 'Rest and recovery.',
  },
  {
    slug: 'health',
    path: '/health',
    label: 'Health',
    description: 'Body, energy, and daily practice.',
  },
  {
    slug: 'adventure',
    path: '/adventure',
    label: 'Adventure',
    description: 'Trips, outdoors, and exploration.',
  },
  {
    slug: 'entertainment',
    path: '/entertainment',
    label: 'Entertainment',
    description: 'Shows, games, and leisure.',
  },
] as const

export type LifeSection = (typeof LIFE_SECTIONS)[number]
export type LifeSectionSlug = LifeSection['slug']
