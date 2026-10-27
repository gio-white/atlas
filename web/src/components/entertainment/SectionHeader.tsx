import { ChevronLeft } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link, useSearchParams } from 'react-router-dom'

import { CategoryIcon, type IconId } from '@/components/entertainment/CategoryIcon'

/** Search params worth carrying between entertainment pages (the `?on=` review date). */
export function useCarriedSearch(): string {
  const [params] = useSearchParams()
  const on = params.get('on')
  return on ? `?on=${on}` : ''
}

export function SectionHeader({
  icon,
  title,
  description,
  children,
}: {
  icon: IconId
  title: string
  description: string
  children?: ReactNode
}) {
  const search = useCarriedSearch()
  return (
    <div className="flex flex-col gap-3">
      <Link
        to={{ pathname: '/entertainment', search }}
        className="inline-flex w-fit items-center gap-1 text-sm text-muted hover:text-ink"
      >
        <ChevronLeft className="size-4" aria-hidden />
        Entertainment
      </Link>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <CategoryIcon id={icon} className="size-14 drop-shadow-md sm:size-16" />
          <header className="flex flex-col gap-0.5">
            <h1 className="text-2xl font-semibold tracking-tight text-ink">{title}</h1>
            <p className="text-sm text-muted">{description}</p>
          </header>
        </div>
        {children}
      </div>
    </div>
  )
}
