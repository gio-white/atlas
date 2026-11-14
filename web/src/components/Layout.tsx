import { Settings } from 'lucide-react'
import { Suspense, useEffect, useState } from 'react'
import { Link, Outlet, useLocation, useSearchParams } from 'react-router-dom'

import { LogDialog } from '@/components/LogDialog'
import { PageLoading } from '@/components/PageState'
import { AddMenu } from '@/components/shell/AddMenu'
import { AsOfControl } from '@/components/shell/AsOfControl'
import { BottomBar, Rail } from '@/components/shell/DestinationNav'
import { QuickTaskDialog } from '@/components/shell/QuickTaskDialog'
import { getInbox } from '@/lib/api'
import type { ShellContext } from '@/lib/asOf'
import { activeDestination, SETTINGS } from '@/lib/nav'
import { persistDisplayName, readDisplayName } from '@/lib/profile'
import { INBOX_CHANGED_EVENT } from '@/lib/quests'
import { cn, todayIso } from '@/lib/utils'

/**
 * Number of Inbox items for the Quests badge; refreshed on every navigation and whenever a
 * screen announces an Inbox change (`notifyInboxChanged`).
 */
function useInboxCount(): number {
  const { pathname } = useLocation()
  const [count, setCount] = useState(0)
  const [changes, setChanges] = useState(0)
  useEffect(() => {
    const onChange = () => setChanges((value) => value + 1)
    window.addEventListener(INBOX_CHANGED_EVENT, onChange)
    return () => window.removeEventListener(INBOX_CHANGED_EVENT, onChange)
  }, [])
  useEffect(() => {
    let cancelled = false
    void pathname
    void changes
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
  }, [pathname, changes])
  return count
}

/**
 * The app shell: a rail of destinations on wide screens, a bottom tab bar on narrow ones, and
 * a header with the date ("As of") and Add.
 */
export function Layout() {
  const { pathname } = useLocation()
  const [searchParams, setSearchParams] = useSearchParams()
  const on = searchParams.get('on')
  const asOf = on ?? todayIso()
  // Only the "As of" date follows you between destinations; a page's own filters stay behind.
  const search = on === null ? '' : new URLSearchParams({ on }).toString()
  const [displayName, setDisplayNameState] = useState(readDisplayName)
  const [logOpen, setLogOpen] = useState(false)
  const [taskOpen, setTaskOpen] = useState(false)
  const inboxCount = useInboxCount()
  const active = activeDestination(pathname)

  function onDateChange(value: string) {
    const next = new URLSearchParams(searchParams)
    if (!value || value === todayIso()) next.delete('on')
    else next.set('on', value)
    setSearchParams(next, { replace: true })
  }

  const nav = { active, search, inboxCount }

  return (
    <div className="min-h-svh bg-canvas">
      <Rail {...nav} />
      <div className="md:pl-[76px]">
        <header className="sticky top-0 z-20 flex items-center gap-2 border-b border-line bg-canvas/90 px-4 py-3 backdrop-blur-md md:px-6">
          <AsOfControl asOf={asOf} onChange={onDateChange} />
          <div className="ml-auto flex shrink-0 items-center gap-1">
            <AddMenu onTask={() => setTaskOpen(true)} onEntry={() => setLogOpen(true)} />
            <Link
              to={{ pathname: SETTINGS.to, search }}
              aria-label={SETTINGS.label}
              aria-current={active === 'settings' ? 'page' : undefined}
              className={cn(
                'inline-flex size-9 items-center justify-center rounded-lg hover:bg-raised focus-visible:ring-2 focus-visible:ring-accent focus-visible:outline-none md:hidden',
                active === 'settings' ? 'text-accent' : 'text-muted hover:text-ink',
              )}
            >
              <Settings className="size-5" aria-hidden />
            </Link>
          </div>
        </header>
        <main className="px-4 pt-5 pb-24 md:px-6 md:pb-8">
          <Suspense fallback={<PageLoading />}>
            <Outlet
              context={
                {
                  asOf,
                  displayName,
                  setDisplayName: (name) => setDisplayNameState(persistDisplayName(name)),
                  inboxCount,
                  openLog: () => setLogOpen(true),
                } satisfies ShellContext
              }
            />
          </Suspense>
        </main>
      </div>
      <BottomBar {...nav} />
      <LogDialog open={logOpen} onOpenChange={setLogOpen} occurredOn={asOf} />
      <QuickTaskDialog open={taskOpen} onOpenChange={setTaskOpen} />
    </div>
  )
}
