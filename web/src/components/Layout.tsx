import { CalendarDays, CalendarRange, Flag, Library, MapPinned } from 'lucide-react'
import { useEffect, useState } from 'react'
import { NavLink, Outlet, useSearchParams } from 'react-router-dom'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Input } from '@/components/ui/input'
import { type Area, listAreas } from '@/lib/api'
import type { ShellContext } from '@/lib/asOf'
import { todayIso } from '@/lib/utils'

const navClass = ({ isActive }: { isActive: boolean }) =>
  [
    'inline-flex min-h-9 items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm font-medium motion-safe:transition-colors motion-safe:duration-200',
    isActive ? 'bg-raised text-ink shadow-sm' : 'text-muted hover:bg-raised/80 hover:text-ink',
  ].join(' ')

export function Layout() {
  const [searchParams, setSearchParams] = useSearchParams()
  const asOf = searchParams.get('on') ?? todayIso()
  const [areas, setAreas] = useState<Area[]>([])

  useEffect(() => {
    let cancelled = false
    listAreas()
      .then((rows) => {
        if (!cancelled) setAreas(rows)
      })
      .catch(() => {
        if (!cancelled) setAreas([])
      })
    return () => {
      cancelled = true
    }
  }, [])

  function onDateChange(value: string) {
    const next = new URLSearchParams(searchParams)
    if (!value || value === todayIso()) next.delete('on')
    else next.set('on', value)
    setSearchParams(next, { replace: true })
  }

  const search = searchParams.toString()

  return (
    <div className="min-h-svh bg-canvas">
      <header className="sticky top-0 z-20 border-b border-line bg-canvas/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-3 px-4 py-3">
          <NavLink
            to="/"
            className="inline-flex items-center gap-2 font-serif text-xl font-medium tracking-tight text-ink"
          >
            <MapPinned className="size-5 text-warn" aria-hidden />
            Atlas
          </NavLink>
          <nav className="flex flex-wrap items-center gap-1" aria-label="Primary">
            <NavLink to={{ pathname: '/', search }} end className={navClass}>
              <CalendarDays className="size-4" aria-hidden />
              Today
            </NavLink>
            <NavLink to={{ pathname: '/week', search }} className={navClass}>
              <CalendarRange className="size-4" aria-hidden />
              Week
            </NavLink>
            <NavLink to={{ pathname: '/goal', search }} className={navClass}>
              <Flag className="size-4" aria-hidden />
              Goals
            </NavLink>
            <NavLink to={{ pathname: '/catalog', search }} className={navClass}>
              <Library className="size-4" aria-hidden />
              Catalog
            </NavLink>
          </nav>
          <div className="ml-auto flex flex-wrap items-center gap-3">
            {areas.length > 0 && (
              <nav className="flex flex-wrap gap-1" aria-label="Areas">
                {areas.map((area) => (
                  <NavLink
                    key={area.slug}
                    to={{ pathname: `/area/${area.slug}`, search }}
                    className={navClass}
                  >
                    {area.name}
                  </NavLink>
                ))}
              </nav>
            )}
            <ThemeToggle />
            <Input
              type="date"
              aria-label="As of date"
              className="w-auto font-mono text-xs"
              value={asOf}
              onChange={(event) => onDateChange(event.target.value)}
            />
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-4 py-5">
        <Outlet context={{ asOf } satisfies ShellContext} />
      </main>
    </div>
  )
}
