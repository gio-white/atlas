import {
  ChartColumn,
  House,
  Library,
  type LucideIcon,
  Map as MapIcon,
  Repeat,
  Settings,
} from 'lucide-react'
import { Link } from 'react-router-dom'

import { DESTINATIONS, type Destination, type DestinationId, SETTINGS } from '@/lib/nav'
import { cn } from '@/lib/utils'

// None of these is a quest level icon (compass, flag, diamond, bookmark, scroll).
const ICONS: Record<DestinationId, LucideIcon> = {
  home: House,
  quests: MapIcon,
  habits: Repeat,
  stats: ChartColumn,
  library: Library,
  settings: Settings,
}

type NavProps = {
  active: DestinationId
  /** The query string to carry (the "As of" date), without the leading `?`. */
  search: string
  inboxCount: number
}

function DestinationLink({
  destination,
  active,
  search,
  inboxCount,
  className,
}: NavProps & { destination: Destination; className?: string }) {
  const Icon = ICONS[destination.id]
  const current = active === destination.id
  const badge = destination.id === 'quests' && inboxCount > 0 ? inboxCount : null
  return (
    <Link
      to={{ pathname: destination.to, search }}
      aria-current={current ? 'page' : undefined}
      className={cn(
        'flex flex-col items-center justify-center gap-1 rounded-xl text-[11px] leading-none font-medium motion-safe:transition-colors motion-safe:duration-200 focus-visible:ring-2 focus-visible:ring-accent focus-visible:outline-none',
        current ? 'text-accent' : 'text-muted hover:text-ink',
        className,
      )}
    >
      <span className="relative">
        <Icon className="size-5" aria-hidden />
        {badge !== null && (
          <span className="absolute -top-1.5 left-3.5 min-w-4 rounded-full bg-accent px-1 py-0.5 text-center text-[10px] leading-none font-semibold text-on-accent tabular-nums">
            {badge}
          </span>
        )}
      </span>
      <span>
        {destination.label}
        {badge !== null && <span className="sr-only">, {badge} in your Inbox to sort</span>}
      </span>
    </Link>
  )
}

/** The fixed left rail on wide screens: five destinations, with Settings at the bottom. */
export function Rail(props: NavProps) {
  const item = (destination: Destination) => (
    <DestinationLink
      key={destination.id}
      destination={destination}
      className={cn(
        'min-h-14 w-full px-1',
        props.active === destination.id
          ? 'bg-raised shadow-[var(--shadow-card)]'
          : 'hover:bg-raised/70',
      )}
      {...props}
    />
  )
  return (
    <aside className="fixed inset-y-0 left-0 z-30 hidden w-[76px] flex-col border-r border-line bg-sidebar px-2 py-3 md:flex">
      <nav aria-label="Primary" className="flex flex-1 flex-col gap-1">
        {DESTINATIONS.map(item)}
        <div className="mt-auto">{item(SETTINGS)}</div>
      </nav>
    </aside>
  )
}

/** The same five destinations as a bottom tab bar on narrow screens. */
export function BottomBar(props: NavProps) {
  return (
    <nav
      aria-label="Primary"
      className="fixed inset-x-0 bottom-0 z-30 grid grid-cols-5 border-t border-line bg-sidebar pb-[env(safe-area-inset-bottom)] md:hidden"
    >
      {DESTINATIONS.map((destination) => (
        <DestinationLink
          key={destination.id}
          destination={destination}
          className="min-h-14 rounded-none"
          {...props}
        />
      ))}
    </nav>
  )
}
