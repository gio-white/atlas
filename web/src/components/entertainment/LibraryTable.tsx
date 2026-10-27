import { ArrowDown, ArrowUp, ExternalLink, Search } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { Thumb } from '@/components/entertainment/Posters'
import { RatingStars } from '@/components/entertainment/RatingStars'
import { EmptyState } from '@/components/PageState'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Select } from '@/components/ui/select'
import {
  type EntertainmentStatus,
  type EntertainmentTitle,
  updateEntertainmentTitle,
} from '@/lib/api'
import { shortDateLabel } from '@/lib/dates'
import {
  type CategoryId,
  categoryFor,
  defaultDir,
  filterTitles,
  inCategory,
  KIND_LABEL,
  type LibraryFilter,
  parseSortKey,
  type SortDir,
  type SortKey,
  STATUSES,
  sortTitles,
  statusCounts,
  tagsIn,
} from '@/lib/entertainment'
import { cn } from '@/lib/utils'

/** Filterable, sortable table of one category; status and rating edit inline. */
export function LibraryTable({
  titles,
  category,
  onOpen,
  onRefresh,
}: {
  titles: EntertainmentTitle[]
  category: CategoryId
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
