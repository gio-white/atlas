import {
  ArrowDown,
  ArrowUp,
  ChevronLeft,
  ChevronRight,
  Clapperboard,
  ExternalLink,
  Plus,
  Search,
} from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { CountDonut, countSlices } from '@/components/entertainment/Charts'
import { RatingStars } from '@/components/entertainment/RatingStars'
import { TitleDialog } from '@/components/entertainment/TitleDialog'
import { Segmented } from '@/components/home/Segmented'
import { EmptyState, PageHeader, PageLoading, PageUnavailable } from '@/components/PageState'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import {
  ApiError,
  type EntertainmentDashboard,
  type EntertainmentKind,
  type EntertainmentStatus,
  type EntertainmentTitle,
  type EntertainmentTopic,
  getEntertainmentDashboard,
  listEntertainmentTitles,
  listEntertainmentTopics,
  type Period,
  updateEntertainmentTitle,
} from '@/lib/api'
import { useAsOf } from '@/lib/asOf'
import { shiftPeriodDate, shortDateLabel } from '@/lib/dates'
import {
  CATEGORIES,
  type CategoryId,
  categoryFor,
  defaultDir,
  filterTitles,
  inCategory,
  KIND_LABEL,
  type LibraryFilter,
  parseCategory,
  parseSortKey,
  type SortDir,
  type SortKey,
  STATUS_LABEL,
  STATUSES,
  sortTitles,
  statusCounts,
  tagsIn,
} from '@/lib/entertainment'
import { cn, todayIso } from '@/lib/utils'

type View = 'library' | 'insights'

const VIEWS: { id: View; label: string }[] = [
  { id: 'library', label: 'Library' },
  { id: 'insights', label: 'Insights' },
]

const PERIODS: { id: Period; label: string }[] = [
  { id: 'day', label: 'Day' },
  { id: 'week', label: 'Week' },
  { id: 'month', label: 'Month' },
]

const KIND_FALLBACK: Record<EntertainmentKind, string> = {
  film: 'bg-entertainment/80',
  series: 'bg-update/80',
  anime: 'bg-adventure/80',
  video: 'bg-screen/80',
  podcast: 'bg-goal/80',
  book: 'bg-warn/80',
  music: 'bg-sleep/80',
  other: 'bg-muted/80',
}

function parsePeriod(raw: string | null): Period {
  if (raw === 'day' || raw === 'week' || raw === 'month') return raw
  return 'week'
}

export function EntertainmentPage() {
  const [params, setParams] = useSearchParams()
  const view: View = params.get('view') === 'insights' ? 'insights' : 'library'
  const category = parseCategory(params.get('cat'))
  const [titles, setTitles] = useState<EntertainmentTitle[] | null>(null)
  const [topics, setTopics] = useState<EntertainmentTopic[]>([])
  const [error, setError] = useState<string | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editing, setEditing] = useState<EntertainmentTitle | null>(null)

  const refresh = useCallback(async () => {
    const [nextTitles, nextTopics] = await Promise.all([
      listEntertainmentTitles(),
      listEntertainmentTopics().catch(() => []),
    ])
    setTitles(nextTitles)
    setTopics(nextTopics)
  }, [])

  useEffect(() => {
    let cancelled = false
    setError(null)
    refresh().catch((caught: unknown) => {
      if (!cancelled) {
        setError(caught instanceof ApiError ? caught.message : 'Could not load entertainment')
      }
    })
    return () => {
      cancelled = true
    }
  }, [refresh])

  function setParam(key: string, value: string | null) {
    const copy = new URLSearchParams(params)
    if (value === null) copy.delete(key)
    else copy.set(key, value)
    setParams(copy, { replace: true })
  }

  function openDialog(title: EntertainmentTitle | null) {
    setEditing(title)
    setDialogOpen(true)
  }

  if (error !== null) {
    return <PageUnavailable title="Entertainment" message={error} />
  }
  if (titles === null) return <PageLoading />

  const defaultKind = categoryFor(category).kinds[0]

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageHeader
          title="Entertainment"
          description="Everything you have watched, read, and listened to, and what is next."
          homeLink
        />
        <div className="flex flex-wrap items-center gap-2">
          <Segmented
            label="Entertainment view"
            options={VIEWS}
            value={view}
            onChange={(next) => setParam('view', next === 'library' ? null : next)}
          />
          <Button type="button" onClick={() => openDialog(null)}>
            <Plus className="size-4" aria-hidden />
            Add
          </Button>
        </div>
      </div>
      {view === 'library' ? (
        <LibraryView
          titles={titles}
          category={category}
          onCategory={(next) => setParam('cat', next === 'all' ? null : next)}
          onOpen={openDialog}
          onRefresh={refresh}
        />
      ) : (
        <InsightsView titleCount={titles.length} />
      )}
      <TitleDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        title={editing}
        defaultKind={defaultKind}
        topics={topics}
        takenSlugs={titles.map((title) => title.slug)}
        onSaved={refresh}
      />
    </div>
  )
}

function LibraryView({
  titles,
  category,
  onCategory,
  onOpen,
  onRefresh,
}: {
  titles: EntertainmentTitle[]
  category: CategoryId
  onCategory: (next: CategoryId) => void
  onOpen: (title: EntertainmentTitle) => void
  onRefresh: () => Promise<void>
}) {
  const [params, setParams] = useSearchParams()
  const sortKey = parseSortKey(params.get('sort'))
  const sortDir: SortDir =
    params.get('dir') === 'asc' || params.get('dir') === 'desc'
      ? (params.get('dir') as SortDir)
      : defaultDir(sortKey)
  const [filter, setFilter] = useState<LibraryFilter>({
    status: null,
    tag: null,
    minRating: null,
    query: '',
  })

  const inScope = useMemo(
    () => titles.filter((title) => inCategory(title, category)),
    [titles, category],
  )
  const counts = useMemo(() => statusCounts(inScope), [inScope])
  const tags = useMemo(() => tagsIn(inScope), [inScope])
  const rows = useMemo(
    () => sortTitles(filterTitles(titles, category, filter), sortKey, sortDir),
    [titles, category, filter, sortKey, sortDir],
  )
  const showKind = categoryFor(category).kinds.length > 1

  function sortBy(key: SortKey) {
    const copy = new URLSearchParams(params)
    const nextDir: SortDir =
      key === sortKey ? (sortDir === 'asc' ? 'desc' : 'asc') : defaultDir(key)
    copy.set('sort', key)
    copy.set('dir', nextDir)
    setParams(copy, { replace: true })
  }

  async function patch(slug: string, body: Parameters<typeof updateEntertainmentTitle>[1]) {
    await updateEntertainmentTitle(slug, body)
    await onRefresh()
  }

  return (
    <div className="flex flex-col gap-4">
      <div className="flex gap-1 overflow-x-auto border-b border-line" role="tablist">
        {CATEGORIES.map((item) => {
          const count = titles.filter((title) => inCategory(title, item.id)).length
          return (
            <button
              key={item.id}
              type="button"
              role="tab"
              aria-selected={category === item.id}
              className={cn(
                '-mb-px flex shrink-0 items-baseline gap-1.5 border-b-2 px-3 py-2 text-sm motion-safe:transition-colors',
                category === item.id
                  ? 'border-entertainment font-medium text-ink'
                  : 'border-transparent text-muted hover:text-ink',
              )}
              onClick={() => {
                onCategory(item.id)
                setFilter((current) => ({ ...current, tag: null }))
              }}
            >
              {item.label}
              <span className="text-xs text-muted">{count}</span>
            </button>
          )
        })}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="relative min-w-48 flex-1 sm:max-w-xs">
          <Search
            className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted"
            aria-hidden
          />
          <Input
            aria-label="Search the library"
            className="pl-9"
            placeholder="Search title, creator, notes"
            value={filter.query}
            onChange={(event) => setFilter({ ...filter, query: event.target.value })}
          />
        </div>
        <div className="flex flex-wrap gap-1">
          <StatusChip
            label="Any status"
            count={inScope.length}
            active={filter.status === null}
            onClick={() => setFilter({ ...filter, status: null })}
          />
          {STATUSES.map((status) => (
            <StatusChip
              key={status.id}
              label={status.label}
              count={counts[status.id]}
              active={filter.status === status.id}
              onClick={() => setFilter({ ...filter, status: status.id })}
            />
          ))}
        </div>
        <Select
          aria-label="Filter by tag"
          className="w-auto"
          value={filter.tag ?? ''}
          onChange={(event) => setFilter({ ...filter, tag: event.target.value || null })}
        >
          <option value="">All tags</option>
          {tags.map((tag) => (
            <option key={tag.slug} value={tag.slug}>
              {tag.name}
            </option>
          ))}
        </Select>
        <Select
          aria-label="Minimum rating"
          className="w-auto"
          value={filter.minRating ?? ''}
          onChange={(event) =>
            setFilter({
              ...filter,
              minRating: event.target.value === '' ? null : Number(event.target.value),
            })
          }
        >
          <option value="">Any rating</option>
          {[5, 4, 3, 2].map((stars) => (
            <option key={stars} value={stars}>
              {stars === 5 ? '5 stars' : `${stars}+ stars`}
            </option>
          ))}
        </Select>
      </div>

      {rows.length === 0 ? (
        <EmptyState
          title={inScope.length === 0 ? 'Nothing here yet' : 'No titles match these filters'}
          hint={
            inScope.length === 0
              ? 'Use Add to save something you have seen or want to see.'
              : 'Clear a filter or search for something else.'
          }
        />
      ) : (
        <div className="overflow-x-auto rounded-2xl border border-line bg-surface">
          <table className="w-full min-w-[44rem] text-sm">
            <thead className="border-b border-line text-left text-xs text-muted">
              <tr>
                <SortHeader
                  label="Title"
                  column="name"
                  sortKey={sortKey}
                  dir={sortDir}
                  onSort={sortBy}
                />
                {showKind ? (
                  <SortHeader
                    label="Kind"
                    column="kind"
                    sortKey={sortKey}
                    dir={sortDir}
                    onSort={sortBy}
                  />
                ) : null}
                <SortHeader
                  label="Status"
                  column="status"
                  sortKey={sortKey}
                  dir={sortDir}
                  onSort={sortBy}
                />
                <SortHeader
                  label="Rating"
                  column="rating"
                  sortKey={sortKey}
                  dir={sortDir}
                  onSort={sortBy}
                />
                <th className="px-3 py-2 font-medium">Tags</th>
                <SortHeader
                  label="Finished"
                  column="finished_on"
                  sortKey={sortKey}
                  dir={sortDir}
                  onSort={sortBy}
                />
                <SortHeader
                  label="Added"
                  column="created_at"
                  sortKey={sortKey}
                  dir={sortDir}
                  onSort={sortBy}
                />
              </tr>
            </thead>
            <tbody>
              {rows.map((title) => (
                <tr
                  key={title.slug}
                  className="border-b border-line/60 last:border-0 hover:bg-raised/60"
                >
                  <td className="px-3 py-2">
                    <div className="flex items-center gap-3">
                      <Thumb title={title} />
                      <div className="min-w-0">
                        <div className="flex items-center gap-1.5">
                          <button
                            type="button"
                            className="cursor-pointer truncate text-left font-medium text-ink hover:underline"
                            onClick={() => onOpen(title)}
                          >
                            {title.name}
                          </button>
                          {title.link ? (
                            <a
                              href={title.link}
                              target="_blank"
                              rel="noreferrer"
                              className="text-muted hover:text-ink"
                              aria-label={`Open ${title.name}`}
                            >
                              <ExternalLink className="size-3.5" aria-hidden />
                            </a>
                          ) : null}
                        </div>
                        <p className="truncate text-xs text-muted">
                          {[title.creator, title.progress].filter(Boolean).join(' · ')}
                        </p>
                      </div>
                    </div>
                  </td>
                  {showKind ? (
                    <td className="px-3 py-2 text-muted">{KIND_LABEL[title.kind]}</td>
                  ) : null}
                  <td className="px-3 py-2">
                    <Select
                      aria-label={`Status for ${title.name}`}
                      className="h-8 w-32"
                      value={title.status}
                      onChange={(event) =>
                        void patch(title.slug, {
                          status: event.target.value as EntertainmentStatus,
                        })
                      }
                    >
                      {STATUSES.map((status) => (
                        <option key={status.id} value={status.id}>
                          {status.label}
                        </option>
                      ))}
                    </Select>
                  </td>
                  <td className="px-3 py-2">
                    <RatingStars
                      value={title.rating}
                      label={`rating for ${title.name}`}
                      onChange={(rating) => void patch(title.slug, { rating })}
                    />
                  </td>
                  <td className="px-3 py-2">
                    <div className="flex flex-wrap gap-1">
                      {title.topics.map((topic) => (
                        <button
                          key={topic.slug}
                          type="button"
                          className="cursor-pointer"
                          onClick={() => setFilter({ ...filter, tag: topic.slug })}
                        >
                          <Badge className="normal-case">{topic.name}</Badge>
                        </button>
                      ))}
                    </div>
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-muted">
                    {title.finished_on ? shortDateLabel(title.finished_on) : '—'}
                  </td>
                  <td className="px-3 py-2 whitespace-nowrap text-muted">
                    {title.created_at ? shortDateLabel(title.created_at.slice(0, 10)) : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

function StatusChip({
  label,
  count,
  active,
  onClick,
}: {
  label: string
  count: number
  active: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      aria-pressed={active}
      className={cn(
        'cursor-pointer rounded-full border px-3 py-1 text-xs motion-safe:transition-colors',
        active
          ? 'border-entertainment bg-entertainment/15 text-ink'
          : 'border-line text-muted hover:text-ink',
      )}
      onClick={onClick}
    >
      {label} <span className="text-muted">{count}</span>
    </button>
  )
}

function SortHeader({
  label,
  column,
  sortKey,
  dir,
  onSort,
}: {
  label: string
  column: SortKey
  sortKey: SortKey
  dir: SortDir
  onSort: (key: SortKey) => void
}) {
  const active = column === sortKey
  return (
    <th
      className="px-3 py-2 font-medium"
      aria-sort={active ? (dir === 'asc' ? 'ascending' : 'descending') : 'none'}
    >
      <button
        type="button"
        className={cn(
          'inline-flex cursor-pointer items-center gap-1 hover:text-ink',
          active && 'text-ink',
        )}
        onClick={() => onSort(column)}
      >
        {label}
        {active ? (
          dir === 'asc' ? (
            <ArrowUp className="size-3" aria-hidden />
          ) : (
            <ArrowDown className="size-3" aria-hidden />
          )
        ) : null}
      </button>
    </th>
  )
}

function Thumb({ title }: { title: EntertainmentTitle }) {
  if (title.image) {
    return <img src={title.image} alt="" className="size-10 shrink-0 rounded-md object-cover" />
  }
  return (
    <div
      className={cn(
        'flex size-10 shrink-0 items-center justify-center rounded-md text-white/90',
        KIND_FALLBACK[title.kind],
      )}
    >
      <Clapperboard className="size-4" aria-hidden />
    </div>
  )
}

function InsightsView({ titleCount }: { titleCount: number }) {
  const asOf = useAsOf()
  const [params, setParams] = useSearchParams()
  const period = parsePeriod(params.get('period'))
  const [dash, setDash] = useState<EntertainmentDashboard | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    setError(null)
    getEntertainmentDashboard(period, asOf)
      .then((next) => {
        if (!cancelled) setDash(next)
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setError(caught instanceof ApiError ? caught.message : 'Could not load insights')
        }
      })
    return () => {
      cancelled = true
    }
  }, [asOf, period])

  function setPeriod(next: Period) {
    const copy = new URLSearchParams(params)
    if (next === 'week') copy.delete('period')
    else copy.set('period', next)
    setParams(copy, { replace: true })
  }

  function shift(delta: number) {
    const copy = new URLSearchParams(params)
    const next = shiftPeriodDate(asOf, period, delta)
    if (next === todayIso()) copy.delete('on')
    else copy.set('on', next)
    setParams(copy, { replace: true })
  }

  if (error !== null) return <p className="text-sm text-bad">{error}</p>
  if (dash === null) return <PageLoading />
  if (titleCount === 0) {
    return (
      <EmptyState
        title="Nothing in the library yet"
        hint="Add a film, series, book, podcast, or album and insights will appear here."
      />
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm text-muted">
          {shortDateLabel(dash.range_start)} – {shortDateLabel(dash.range_end)}
        </p>
        <div className="flex items-center gap-2">
          <Segmented label="Period" options={PERIODS} value={period} onChange={setPeriod} />
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => shift(-1)}
            aria-label="Previous"
          >
            <ChevronLeft className="size-4" />
          </Button>
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={() => shift(1)}
            aria-label="Next"
          >
            <ChevronRight className="size-4" />
          </Button>
        </div>
      </div>
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Finished" value={dash.finished_in_range} hint="in this period" />
        <StatCard label="In progress" value={dash.in_progress} hint="right now" />
        <StatCard label={STATUS_LABEL.queued} value={dash.queued} hint="waiting" />
        <StatCard label="Dropped" value={dash.dropped} hint="left unfinished" />
      </section>
      <section className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Finished by kind</CardTitle>
            <CardDescription>This period</CardDescription>
          </CardHeader>
          <CountDonut
            label="Finished by kind"
            slices={countSlices(
              dash.by_kind.map((row) => ({
                slug: row.kind,
                name: KIND_LABEL[row.kind],
                count: row.count,
              })),
            )}
          />
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Finished by tag</CardTitle>
            <CardDescription>This period</CardDescription>
          </CardHeader>
          <CountDonut
            label="Finished by tag"
            slices={countSlices(
              dash.by_topic.map((row) => ({
                slug: row.slug,
                name: row.name,
                count: row.count,
              })),
            )}
          />
        </Card>
      </section>
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Recently finished</CardTitle>
        </CardHeader>
        {dash.recently_finished.length === 0 ? (
          <p className="text-sm text-muted">Nothing marked done yet.</p>
        ) : (
          <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {dash.recently_finished.map((title) => (
              <li key={title.slug}>
                <PosterCard title={title} />
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  )
}

function StatCard({ label, value, hint }: { label: string; value: number; hint: string }) {
  return (
    <Card>
      <p className="text-sm text-muted">{label}</p>
      <p className="mt-1 text-3xl font-semibold tracking-tight">{value}</p>
      <p className="mt-1 text-xs text-muted">{hint}</p>
    </Card>
  )
}

function PosterCard({ title }: { title: EntertainmentTitle }) {
  return (
    <article className="overflow-hidden rounded-2xl border border-line bg-surface shadow-[var(--shadow-card)]">
      <div className="relative aspect-[16/10]">
        {title.image ? (
          <img src={title.image} alt="" className="size-full object-cover" />
        ) : (
          <div
            className={cn(
              'flex size-full items-center justify-center text-white/90',
              KIND_FALLBACK[title.kind],
            )}
          >
            <Clapperboard className="size-8" aria-hidden />
          </div>
        )}
        <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 to-transparent p-3 text-white">
          <p className="font-medium leading-tight">{title.name}</p>
          <p className="mt-0.5 text-xs text-white/80">
            {KIND_LABEL[title.kind]}
            {title.creator ? ` · ${title.creator}` : ''}
          </p>
        </div>
      </div>
      <div className="flex items-center justify-between gap-2 p-3">
        {title.finished_on ? (
          <p className="text-xs text-muted">Finished {shortDateLabel(title.finished_on)}</p>
        ) : (
          <span />
        )}
        {title.rating !== null ? <RatingStars value={title.rating} label="rating" /> : null}
      </div>
    </article>
  )
}
