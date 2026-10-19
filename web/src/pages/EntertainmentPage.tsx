import { Link2, Plus } from 'lucide-react'
import { type FormEvent, useState } from 'react'
import { Link, Navigate, useSearchParams } from 'react-router-dom'

import { CategoryIcon, type IconId } from '@/components/entertainment/CategoryIcon'
import { useCarriedSearch } from '@/components/entertainment/SectionHeader'
import { TitleDialog } from '@/components/entertainment/TitleDialog'
import { useLibrary } from '@/components/entertainment/useLibrary'
import { PageHeader, PageLoading, PageUnavailable } from '@/components/PageState'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { CATEGORIES, categoryFromPath, inCategory } from '@/lib/entertainment'
import { cn } from '@/lib/utils'

const SHELF = CATEGORIES.filter((category) => category.id !== 'all')

/** Entertainment home: one app-style icon per category, plus Everything and Insights. */
export function EntertainmentPage() {
  const [params] = useSearchParams()
  const search = useCarriedSearch()
  const { titles, topics, error, refresh } = useLibrary()
  const [link, setLink] = useState('')
  const [dialogLink, setDialogLink] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)

  const legacyCategory = categoryFromPath(params.get('cat') ?? undefined)
  if (params.get('view') === 'insights') {
    return <Navigate to={{ pathname: '/entertainment/insights', search }} replace />
  }
  if (legacyCategory !== null) {
    return <Navigate to={{ pathname: `/entertainment/${legacyCategory}`, search }} replace />
  }
  if (error !== null) return <PageUnavailable title="Entertainment" message={error} />
  if (titles === null) return <PageLoading />

  function openAdd(fromLink: string | null) {
    setDialogLink(fromLink)
    setDialogOpen(true)
  }

  function onLinkSubmit(event: FormEvent) {
    event.preventDefault()
    const cleaned = link.trim()
    if (cleaned === '') return
    openAdd(cleaned)
    setLink('')
  }

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageHeader
          title="Entertainment"
          description="Everything you have watched, read, and listened to, and what is next."
          homeLink
        />
        <Button type="button" variant="outline" onClick={() => openAdd(null)}>
          <Plus className="size-4" aria-hidden />
          Add by hand
        </Button>
      </div>

      <form
        onSubmit={onLinkSubmit}
        className="flex flex-col gap-2 rounded-2xl border border-line bg-surface p-3 shadow-[var(--shadow-card)] sm:flex-row sm:items-center"
      >
        <label htmlFor="add-from-link" className="sr-only">
          Add from a link
        </label>
        <div className="relative flex-1">
          <Link2
            className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted"
            aria-hidden
          />
          <Input
            id="add-from-link"
            type="url"
            inputMode="url"
            className="h-11 pl-9"
            placeholder="Paste a YouTube, Spotify, Goodreads, IMDb… link to add it"
            value={link}
            onChange={(event) => setLink(event.target.value)}
          />
        </div>
        <Button type="submit" className="h-11" disabled={link.trim() === ''}>
          Add from link
        </Button>
      </form>

      <section aria-label="Categories">
        <ul className="grid grid-cols-3 gap-x-4 gap-y-7 sm:grid-cols-5">
          {SHELF.map((category) => {
            const inside = titles.filter((title) => inCategory(title, category.id))
            return (
              <li key={category.id}>
                <IconTile
                  id={category.id}
                  label={category.label}
                  to={`/entertainment/${category.id}${search}`}
                  caption={countCaption(inside.length)}
                  badge={inside.filter((title) => title.status === 'in_progress').length}
                />
              </li>
            )
          })}
        </ul>
      </section>

      <nav
        aria-label="Library views"
        className="mx-auto flex w-fit gap-8 rounded-[2rem] border border-line/70 bg-raised/60 px-8 py-4 backdrop-blur"
      >
        <IconTile
          id="all"
          label="Everything"
          to={`/entertainment/all${search}`}
          caption={countCaption(titles.length)}
          small
        />
        <IconTile
          id="insights"
          label="Insights"
          to={`/entertainment/insights${search}`}
          caption="Charts"
          small
        />
      </nav>

      <TitleDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title={null}
        initialLink={dialogLink}
        defaultKind="film"
        topics={topics}
        takenSlugs={titles.map((title) => title.slug)}
        onSaved={refresh}
      />
    </div>
  )
}

function countCaption(count: number): string {
  return count === 1 ? '1 saved' : `${count} saved`
}

function IconTile({
  id,
  label,
  to,
  caption,
  badge = 0,
  small = false,
}: {
  id: IconId
  label: string
  to: string
  caption: string
  badge?: number
  small?: boolean
}) {
  return (
    <Link
      to={to}
      className="group flex flex-col items-center gap-2 rounded-3xl p-1 text-center focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
    >
      <span className="relative">
        <CategoryIcon
          id={id}
          className={cn(
            'drop-shadow-[0_10px_18px_rgba(0,0,0,0.18)] motion-safe:transition-transform motion-safe:duration-200 group-hover:-translate-y-1 group-hover:scale-[1.04] group-active:scale-95',
            small ? 'size-16 sm:size-20' : 'size-20 sm:size-24 lg:size-28',
          )}
        />
        {badge > 0 ? (
          <span
            className="absolute -top-1.5 -right-1.5 flex h-6 min-w-6 items-center justify-center rounded-full bg-bad px-1.5 text-xs font-semibold text-white ring-2 ring-canvas"
            title={`${badge} in progress`}
          >
            {badge}
            <span className="sr-only"> in progress</span>
          </span>
        ) : null}
      </span>
      <span className="flex flex-col">
        <span className="text-sm font-medium text-ink">{label}</span>
        <span className="text-xs text-muted">{caption}</span>
      </span>
    </Link>
  )
}
