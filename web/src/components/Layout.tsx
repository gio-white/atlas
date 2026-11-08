import {
  BookOpen,
  CalendarDays,
  Clapperboard,
  Compass,
  Flag,
  Flame,
  HeartPulse,
  History,
  Home,
  Inbox,
  Menu,
  Monitor,
  Moon,
  Mountain,
  Plus,
  Scroll,
  Settings,
  Sun,
  X,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { NavLink, Outlet, useLocation, useSearchParams } from 'react-router-dom'

import { LogDialog } from '@/components/LogDialog'
import { ProfileDialog } from '@/components/ProfileDialog'
import { Button } from '@/components/ui/button'
import { getInbox } from '@/lib/api'
import type { ShellContext } from '@/lib/asOf'
import { longDateLabel } from '@/lib/dates'
import { initials, readDisplayName } from '@/lib/profile'
import { LIFE_SECTIONS } from '@/lib/sections'
import { cn, todayIso } from '@/lib/utils'

const SECTION_ICONS = {
  sleep: Moon,
  health: HeartPulse,
  adventure: Mountain,
  entertainment: Clapperboard,
} as const

const NAV = [
  { to: '/', label: 'Home', icon: Home, end: true },
  ...LIFE_SECTIONS.map((section) => ({
    to: section.path,
    label: section.label,
    icon: SECTION_ICONS[section.slug],
  })),
  { to: '/screen', label: 'Screen Time', icon: Monitor },
  { to: '/habit', label: 'Habits', icon: Flame },
  { to: '/journal', label: 'Journal', icon: BookOpen },
  { to: '/history', label: 'History', icon: History },
] as const

const QUEST_NAV = [
  { to: '/today', label: 'Today', icon: Sun },
  { to: '/inbox', label: 'Inbox', icon: Inbox },
  { to: '/quests', label: 'Main quests', icon: Flag },
  { to: '/side-quests', label: 'Side quests', icon: Scroll },
  { to: '/calendar', label: 'Calendar', icon: CalendarDays },
] as const

/** Number of Inbox items for the sidebar badge; refreshed on every navigation. */
function useInboxCount(): number {
  const { pathname } = useLocation()
  const [count, setCount] = useState(0)
  useEffect(() => {
    let cancelled = false
    void pathname
    getInbox()
      .then((inbox) => {
        if (!cancelled) setCount(inbox.count)
      })
      .catch(() => {
        if (!cancelled) setCount(0)
      })
    return () => {
      cancelled = true
    }
  }, [pathname])
  return count
}

function navClass({ isActive }: { isActive: boolean }) {
  return cn(
    'inline-flex min-h-11 w-full items-center gap-3 rounded-xl px-3 text-sm font-medium motion-safe:transition-colors motion-safe:duration-200',
    isActive ? 'bg-raised text-ink' : 'text-muted hover:bg-raised/70 hover:text-ink',
  )
}

export function Layout() {
  const [searchParams, setSearchParams] = useSearchParams()
  const asOf = searchParams.get('on') ?? todayIso()
  const search = searchParams.toString()
  const [displayName, setDisplayName] = useState(readDisplayName)
  const [logOpen, setLogOpen] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const inboxCount = useInboxCount()

  function onDateChange(value: string) {
    const next = new URLSearchParams(searchParams)
    if (!value || value === todayIso()) next.delete('on')
    else next.set('on', value)
    setSearchParams(next, { replace: true })
  }

  const sidebar = (
    <div className="flex h-full flex-col gap-6 p-4">
      <NavLink
        to={{ pathname: '/', search }}
        className="inline-flex items-center gap-2 text-lg font-semibold tracking-tight text-ink"
        onClick={() => setSidebarOpen(false)}
      >
        <Compass className="size-6 text-quick" aria-hidden />
        Atlas
      </NavLink>
      <nav className="flex flex-col gap-1" aria-label="Primary">
        {NAV.map((item) => (
          <NavLink
            key={item.to}
            to={{ pathname: item.to, search }}
            end={'end' in item ? item.end : false}
            className={navClass}
            onClick={() => setSidebarOpen(false)}
          >
            <item.icon className="size-4 shrink-0" aria-hidden />
            {item.label}
          </NavLink>
        ))}
      </nav>
      <nav className="flex flex-col gap-1" aria-labelledby="quests-nav-heading">
        <h2 id="quests-nav-heading" className="px-3 pb-1 text-xs font-medium text-muted">
          Quests
        </h2>
        {QUEST_NAV.map((item) => (
          <NavLink
            key={item.to}
            to={{ pathname: item.to, search }}
            className={navClass}
            onClick={() => setSidebarOpen(false)}
          >
            <item.icon className="size-4 shrink-0" aria-hidden />
            {item.label}
            {item.to === '/inbox' && inboxCount > 0 && (
              <span className="ml-auto rounded-full bg-raised px-2 text-xs tabular-nums text-muted">
                <span className="sr-only">, </span>
                {inboxCount}
                <span className="sr-only"> to sort</span>
              </span>
            )}
          </NavLink>
        ))}
      </nav>
      <div className="mt-auto flex flex-col gap-4">
        <Button
          type="button"
          className="min-h-11 w-full rounded-full bg-quick text-on-primary hover:bg-quick/90"
          onClick={() => {
            setSidebarOpen(false)
            setLogOpen(true)
          }}
        >
          <Plus className="size-4" aria-hidden />
          New Entry
        </Button>
        <button
          type="button"
          className="flex min-h-11 items-center gap-3 rounded-xl px-1 text-left hover:bg-raised/70"
          onClick={() => {
            setSidebarOpen(false)
            setProfileOpen(true)
          }}
        >
          <span
            className="inline-flex size-9 items-center justify-center rounded-full bg-raised text-sm font-semibold"
            aria-hidden
          >
            {initials(displayName)}
          </span>
          <span className="min-w-0 flex-1">
            <span className="block truncate text-sm font-medium text-ink">{displayName}</span>
            <span className="block text-xs text-muted">View profile</span>
          </span>
        </button>
      </div>
    </div>
  )

  return (
    <div className="min-h-svh bg-canvas">
      {sidebarOpen && (
        <button
          type="button"
          className="fixed inset-0 z-30 bg-black/50 lg:hidden"
          aria-label="Close menu"
          onClick={() => setSidebarOpen(false)}
        />
      )}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-40 w-64 overflow-y-auto border-r border-line bg-sidebar motion-safe:transition-transform motion-safe:duration-200 lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        {sidebar}
      </aside>
      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex items-center gap-3 border-b border-line bg-canvas/90 px-4 py-3 backdrop-blur-md">
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="lg:hidden"
            aria-label={sidebarOpen ? 'Close menu' : 'Open menu'}
            onClick={() => setSidebarOpen((open) => !open)}
          >
            {sidebarOpen ? (
              <X className="size-4" aria-hidden />
            ) : (
              <Menu className="size-4" aria-hidden />
            )}
          </Button>
          <p className="text-sm font-medium text-muted">{longDateLabel(asOf)}</p>
          <div className="ml-auto flex items-center gap-1">
            <Button
              type="button"
              variant="ghost"
              size="icon"
              aria-label="Settings"
              onClick={() => setProfileOpen(true)}
            >
              <Settings className="size-4" aria-hidden />
            </Button>
          </div>
        </header>
        <main className="px-4 py-5 lg:px-6">
          <Outlet
            context={
              {
                asOf,
                displayName,
                openLog: () => setLogOpen(true),
              } satisfies ShellContext
            }
          />
        </main>
      </div>
      <LogDialog open={logOpen} onOpenChange={setLogOpen} occurredOn={asOf} />
      <ProfileDialog
        open={profileOpen}
        onOpenChange={setProfileOpen}
        displayName={displayName}
        onDisplayName={setDisplayName}
        asOf={asOf}
        onAsOf={onDateChange}
      />
    </div>
  )
}
