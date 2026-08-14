import { useEffect, useState } from 'react'
import { NavLink, Outlet, useSearchParams } from 'react-router-dom'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { type Area, listAreas } from '@/lib/api'
import type { ShellContext } from '@/lib/asOf'
import { todayIso } from '@/lib/utils'

const navClass = ({ isActive }: { isActive: boolean }) =>
  [
    'rounded-md px-2.5 py-1.5 text-sm transition-colors',
    isActive ? 'bg-raised text-ink' : 'text-muted hover:text-ink',
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

  return (
    <div className="mx-auto flex min-h-svh max-w-6xl flex-col px-4 py-6">
      <header className="flex flex-wrap items-center gap-4">
        <NavLink to="/" className="font-serif text-2xl tracking-tight text-ink">
          Atlas
        </NavLink>
        <nav className="flex flex-wrap items-center gap-1">
          <NavLink to={{ pathname: '/', search: searchParams.toString() }} end className={navClass}>
            Today
          </NavLink>
          <NavLink to={{ pathname: '/week', search: searchParams.toString() }} className={navClass}>
            Week
          </NavLink>
          <NavLink to={{ pathname: '/goal', search: searchParams.toString() }} className={navClass}>
            Goals
          </NavLink>
          <NavLink
            to={{ pathname: '/catalog', search: searchParams.toString() }}
            className={navClass}
          >
            Catalog
          </NavLink>
        </nav>
        <div className="ml-auto flex flex-wrap items-center gap-3">
          {areas.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {areas.map((area) => (
                <NavLink
                  key={area.slug}
                  to={{ pathname: `/area/${area.slug}`, search: searchParams.toString() }}
                  className={navClass}
                >
                  {area.name}
                </NavLink>
              ))}
            </div>
          )}
          <Input
            type="date"
            aria-label="As of date"
            className="w-auto font-mono text-xs"
            value={asOf}
            onChange={(event) => onDateChange(event.target.value)}
          />
        </div>
      </header>
      <Separator className="my-6" />
      <main className="flex-1">
        <Outlet context={{ asOf } satisfies ShellContext} />
      </main>
    </div>
  )
}
