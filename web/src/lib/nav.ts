/**
 * The app's map: the destinations on the rail (and the phone tab bar) and the tabs inside
 * each one. Labels follow docs/product/navigation.md; a path here must have a route in
 * `App.tsx`.
 */

export type DestinationId = 'home' | 'quests' | 'habits' | 'stats' | 'library' | 'settings'

export type Destination = {
  id: DestinationId
  label: string
  to: string
  /** Path prefixes that light this destination up. Home is matched exactly, not by prefix. */
  owns: readonly string[]
}

/** The five destinations, in rail order. Settings is separate: it sits apart on the rail. */
export const DESTINATIONS: readonly Destination[] = [
  // `/today` and `/journal` are reached from Home until Home takes over their content.
  { id: 'home', label: 'Home', to: '/', owns: ['/today', '/journal'] },
  { id: 'quests', label: 'Quests', to: '/quests', owns: ['/quests'] },
  { id: 'habits', label: 'Habits', to: '/habit', owns: ['/habit'] },
  { id: 'stats', label: 'Stats', to: '/stats', owns: ['/stats'] },
  { id: 'library', label: 'Library', to: '/library', owns: ['/library'] },
]

export const SETTINGS: Destination = {
  id: 'settings',
  label: 'Settings',
  to: '/settings',
  owns: ['/settings'],
}

export type SectionId = 'quests' | 'stats' | 'settings'

export type Tab = { label: string; to: string }

export type Section = { title: string; tabs: readonly Tab[] }

export const SECTIONS: Record<SectionId, Section> = {
  quests: {
    title: 'Quests',
    tabs: [
      { label: 'Main quests', to: '/quests' },
      { label: 'Side quests', to: '/quests/side-quests' },
      { label: 'Inbox', to: '/quests/inbox' },
      { label: 'Plan', to: '/quests/plan' },
    ],
  },
  stats: {
    title: 'Stats',
    tabs: [
      { label: 'Sleep', to: '/stats/sleep' },
      { label: 'Screen time', to: '/stats/screen-time' },
      { label: 'Health', to: '/stats/health' },
    ],
  },
  settings: {
    title: 'Settings',
    tabs: [
      { label: 'Appearance', to: '/settings/appearance' },
      { label: 'Screen time setup', to: '/settings/screen-time' },
      { label: 'Devices', to: '/settings/devices' },
      { label: 'Metrics', to: '/settings/metrics' },
      { label: 'All entries', to: '/settings/entries' },
    ],
  },
}

export const INBOX_PATH = '/quests/inbox'

function owns(destination: Destination, pathname: string): boolean {
  return destination.owns.some((prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`))
}

/** The destination a page belongs to, so the rail can mark it. Unknown paths belong to Home. */
export function activeDestination(pathname: string): DestinationId {
  const path = pathname.length > 1 ? pathname.replace(/\/+$/, '') : pathname
  if (owns(SETTINGS, path)) return 'settings'
  return DESTINATIONS.find((destination) => owns(destination, path))?.id ?? 'home'
}
