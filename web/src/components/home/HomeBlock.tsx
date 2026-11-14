import { ChevronRight } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

import { cn } from '@/lib/utils'

/** Where a block leads, keeping the "As of" date. */
export type BlockLink = { label: string; to: string }

/**
 * One block on Home. It loads and fails on its own: with `unavailable` it shows a one-line
 * message instead of its content. `to` makes the heading the doorway into its section;
 * `action` adds a separate link on the right ("All habits").
 */
export function HomeBlock({
  id,
  title,
  to,
  action,
  search,
  unavailable = false,
  className,
  children,
}: {
  id: string
  title: string
  to?: string
  action?: BlockLink
  search: string
  unavailable?: boolean
  className?: string
  children: ReactNode
}) {
  const headingId = `home-${id}`
  return (
    <section
      aria-labelledby={headingId}
      className={cn(
        'flex flex-col gap-3 rounded-2xl border border-line bg-surface p-4 shadow-[var(--shadow-card)]',
        className,
      )}
    >
      <div className="flex items-center justify-between gap-3">
        <h2 id={headingId} className="text-base font-semibold text-ink">
          {to === undefined ? (
            title
          ) : (
            <Link
              to={{ pathname: to, search }}
              className="inline-flex items-center gap-1 hover:text-accent focus-visible:text-accent focus-visible:outline-none"
            >
              {title}
              <ChevronRight className="size-4 text-muted" aria-hidden />
            </Link>
          )}
        </h2>
        {action !== undefined && (
          <Link
            to={{ pathname: action.to, search }}
            className="shrink-0 text-xs font-medium text-accent hover:underline"
          >
            {action.label}
          </Link>
        )}
      </div>
      {unavailable ? (
        <p className="text-sm text-muted" role="status">
          Couldn’t load this right now.
        </p>
      ) : (
        children
      )}
    </section>
  )
}

/** The one-line empty state a block shows when there is nothing to list. */
export function BlockEmpty({ children }: { children: ReactNode }) {
  return <p className="text-sm text-muted">{children}</p>
}
