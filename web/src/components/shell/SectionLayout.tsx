import { Suspense } from 'react'
import { NavLink, Outlet, useSearchParams } from 'react-router-dom'

import { PageLoading } from '@/components/PageState'
import { useShell } from '@/lib/asOf'
import { INBOX_PATH, SECTIONS, type SectionId } from '@/lib/nav'
import { cn } from '@/lib/utils'

/**
 * A destination with sub-pages: its title, a row of text tabs (each with its own address),
 * and the active tab's page underneath. Detail pages (a goal, a habit) sit outside it.
 */
export function SectionLayout({ section }: { section: SectionId }) {
  const shell = useShell()
  const [params] = useSearchParams()
  const on = params.get('on')
  const search = on === null ? '' : new URLSearchParams({ on }).toString()
  const { title, tabs } = SECTIONS[section]

  return (
    <div className="flex flex-col gap-5">
      <div className="flex flex-col gap-3">
        <h1 className="text-2xl font-semibold tracking-tight text-ink">{title}</h1>
        <nav
          aria-label={title}
          className="-mx-4 flex gap-6 overflow-x-auto border-b border-line px-4 md:mx-0 md:px-0"
        >
          {tabs.map((tab) => {
            const badge = tab.to === INBOX_PATH && shell.inboxCount > 0 ? shell.inboxCount : null
            return (
              <NavLink
                key={tab.to}
                to={{ pathname: tab.to, search }}
                end
                className={({ isActive }) =>
                  cn(
                    '-mb-px inline-flex min-h-10 shrink-0 items-center gap-2 border-b-2 text-sm font-medium whitespace-nowrap motion-safe:transition-colors motion-safe:duration-200 focus-visible:text-iris focus-visible:outline-none',
                    isActive
                      ? 'border-iris text-ink'
                      : 'border-transparent text-muted hover:text-ink',
                  )
                }
              >
                {tab.label}
                {badge !== null && (
                  <span className="rounded-full bg-raised px-2 py-0.5 text-xs text-muted tabular-nums">
                    {badge}
                    <span className="sr-only"> to sort</span>
                  </span>
                )}
              </NavLink>
            )
          })}
        </nav>
      </div>
      <Suspense fallback={<PageLoading />}>
        <Outlet context={shell} />
      </Suspense>
    </div>
  )
}
