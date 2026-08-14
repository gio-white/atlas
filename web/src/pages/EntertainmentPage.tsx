import { ChevronLeft, ChevronRight, Clapperboard, Plus } from 'lucide-react'
import { type FormEvent, useCallback, useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { CountDonut, countSlices } from '@/components/entertainment/Charts'
import { EmptyState, PageHeader, PageLoading, PageUnavailable } from '@/components/PageState'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import {
  ApiError,
  createEntertainmentTitle,
  createEntertainmentTopic,
  type EntertainmentDashboard,
  type EntertainmentKind,
  type EntertainmentStatus,
  type EntertainmentTitle,
  type EntertainmentTopic,
  getEntertainmentDashboard,
  listEntertainmentTopics,
  type Period,
  updateEntertainmentTitle,
  uploadEntertainmentImage,
} from '@/lib/api'
import { useAsOf } from '@/lib/asOf'
import { shiftPeriodDate, shortDateLabel } from '@/lib/dates'
import { isValidSlug } from '@/lib/slug'
import { cn, todayIso } from '@/lib/utils'

const PERIODS: { id: Period; label: string }[] = [
  { id: 'day', label: 'Day' },
  { id: 'week', label: 'Week' },
  { id: 'month', label: 'Month' },
]

const KINDS: EntertainmentKind[] = ['film', 'series', 'anime', 'video', 'podcast', 'book']

const STATUSES: { id: EntertainmentStatus; label: string }[] = [
  { id: 'queued', label: 'Queued' },
  { id: 'in_progress', label: 'In progress' },
  { id: 'done', label: 'Done' },
  { id: 'dropped', label: 'Dropped' },
]

const KIND_FALLBACK: Record<EntertainmentKind, string> = {
  film: 'bg-entertainment/80',
  series: 'bg-update/80',
  anime: 'bg-adventure/80',
  video: 'bg-screen/80',
  podcast: 'bg-goal/80',
  book: 'bg-warn/80',
}

function parsePeriod(raw: string | null): Period {
  if (raw === 'day' || raw === 'week' || raw === 'month') return raw
  return 'week'
}

function slugify(text: string): string {
  return text
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

function kindLabel(kind: EntertainmentKind): string {
  return kind.replace('_', ' ')
}

export function EntertainmentPage() {
  const asOf = useAsOf()
  const [params, setParams] = useSearchParams()
  const period = parsePeriod(params.get('period'))
  const [dash, setDash] = useState<EntertainmentDashboard | null>(null)
  const [topics, setTopics] = useState<EntertainmentTopic[]>([])
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    const [nextDash, nextTopics] = await Promise.all([
      getEntertainmentDashboard(period, asOf),
      listEntertainmentTopics().catch(() => []),
    ])
    setDash(nextDash)
    setTopics(nextTopics)
  }, [asOf, period])

  useEffect(() => {
    let cancelled = false
    setError(null)
    refresh().catch((caught: unknown) => {
      if (!cancelled) {
        setError(caught instanceof ApiError ? caught.message : 'Could not load entertainment')
        setDash(null)
      }
    })
    return () => {
      cancelled = true
    }
  }, [refresh])

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

  if (error !== null) {
    return <PageUnavailable title="Entertainment" message={error} />
  }
  if (dash === null) return <PageLoading />

  const empty =
    dash.queued + dash.in_progress + dash.done + dash.dropped === 0 && topics.length === 0

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <PageHeader
          title="Entertainment"
          description={`${shortDateLabel(dash.range_start)} – ${shortDateLabel(dash.range_end)}`}
          homeLink
        />
        <div className="flex flex-wrap items-center gap-2">
          <div className="flex rounded-full border border-line bg-surface p-1" role="tablist">
            {PERIODS.map((item) => (
              <button
                key={item.id}
                type="button"
                role="tab"
                aria-selected={period === item.id}
                className={cn(
                  'rounded-full px-3 py-1 text-sm motion-safe:transition-colors',
                  period === item.id ? 'bg-entertainment/20 text-ink' : 'text-muted hover:text-ink',
                )}
                onClick={() => setPeriod(item.id)}
              >
                {item.label}
              </button>
            ))}
          </div>
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
      {empty ? (
        <EmptyState
          title="Nothing in the library yet"
          hint="Add a topic, then a film, series, book, or anything else you have seen."
        />
      ) : null}
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Finished" value={dash.finished_in_range} hint="in this period" />
        <StatCard label="In progress" value={dash.in_progress} hint="currently watching" />
        <StatCard label="Queued" value={dash.queued} hint="waiting" />
        <StatCard label="Dropped" value={dash.dropped} hint="left unfinished" />
      </section>
      <section className="flex gap-4 overflow-x-auto pb-2">
        {STATUSES.map((column) => (
          <StatusColumn
            key={column.id}
            label={column.label}
            titles={dash.library[column.id]}
            onStatus={async (slug, status) => {
              await updateEntertainmentTitle(slug, { status })
              await refresh()
            }}
          />
        ))}
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
                name: kindLabel(row.kind),
                count: row.count,
              })),
            )}
          />
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Finished by topic</CardTitle>
            <CardDescription>This period</CardDescription>
          </CardHeader>
          <CountDonut
            label="Finished by topic"
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
                <PosterCard title={title} compact />
              </li>
            ))}
          </ul>
        )}
      </Card>
      <CapturePanel topics={topics} onSaved={refresh} />
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

function StatusColumn({
  label,
  titles,
  onStatus,
}: {
  label: string
  titles: EntertainmentTitle[]
  onStatus: (slug: string, status: EntertainmentStatus) => Promise<void>
}) {
  return (
    <div className="flex min-w-64 flex-1 flex-col gap-3">
      <div className="flex items-baseline justify-between">
        <h2 className="font-serif text-lg font-medium tracking-tight">{label}</h2>
        <span className="text-xs text-muted">{titles.length}</span>
      </div>
      {titles.length === 0 ? (
        <p className="rounded-2xl border border-dashed border-line px-3 py-6 text-sm text-muted">
          Empty
        </p>
      ) : (
        titles.map((title) => <PosterCard key={title.slug} title={title} onStatus={onStatus} />)
      )}
    </div>
  )
}

function PosterCard({
  title,
  compact = false,
  onStatus,
}: {
  title: EntertainmentTitle
  compact?: boolean
  onStatus?: (slug: string, status: EntertainmentStatus) => Promise<void>
}) {
  return (
    <article className="overflow-hidden rounded-2xl border border-line bg-surface shadow-[var(--shadow-card)]">
      <div className={cn('relative', compact ? 'aspect-[16/10]' : 'aspect-[2/3]')}>
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
            {kindLabel(title.kind)}
            {title.creator ? ` · ${title.creator}` : ''}
          </p>
        </div>
      </div>
      <div className="flex flex-col gap-2 p-3">
        <div className="flex flex-wrap gap-1">
          <Badge tone="accent">{kindLabel(title.kind)}</Badge>
          {title.topics.map((topic) => (
            <Badge key={topic.slug}>{topic.name}</Badge>
          ))}
        </div>
        {title.recommended_by ? (
          <p className="text-xs text-muted">Recommended by {title.recommended_by}</p>
        ) : null}
        {title.progress ? <p className="text-xs text-muted">{title.progress}</p> : null}
        {title.finished_on ? (
          <p className="text-xs text-muted">Finished {shortDateLabel(title.finished_on)}</p>
        ) : null}
        {onStatus ? (
          <Select
            value={title.status}
            aria-label={`Status for ${title.name}`}
            onChange={(event) => {
              void onStatus(title.slug, event.target.value as EntertainmentStatus)
            }}
          >
            {STATUSES.map((status) => (
              <option key={status.id} value={status.id}>
                {status.label}
              </option>
            ))}
          </Select>
        ) : null}
      </div>
    </article>
  )
}

function CapturePanel({
  topics,
  onSaved,
}: {
  topics: EntertainmentTopic[]
  onSaved: () => Promise<void>
}) {
  const [name, setName] = useState('')
  const [kind, setKind] = useState<EntertainmentKind>('film')
  const [creator, setCreator] = useState('')
  const [recommendedBy, setRecommendedBy] = useState('')
  const [status, setStatus] = useState<EntertainmentStatus>('queued')
  const [progress, setProgress] = useState('')
  const [imageUrl, setImageUrl] = useState('')
  const [imageFile, setImageFile] = useState<File | null>(null)
  const [selectedTopics, setSelectedTopics] = useState<string[]>([])
  const [topicSlug, setTopicSlug] = useState('')
  const [error, setError] = useState<string | null>(null)

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    setError(null)
    const slug = slugify(name)
    if (!isValidSlug(slug)) {
      setError('Name must contain letters or digits so a slug can be derived.')
      return
    }
    try {
      const title = await createEntertainmentTitle({
        slug,
        name,
        kind,
        creator: creator || null,
        recommended_by: recommendedBy || null,
        status,
        progress: progress || null,
        topics: selectedTopics,
        image_url: imageFile ? null : imageUrl || null,
      })
      if (imageFile) {
        await uploadEntertainmentImage(title.slug, imageFile)
      }
      setName('')
      setCreator('')
      setRecommendedBy('')
      setProgress('')
      setImageUrl('')
      setImageFile(null)
      setSelectedTopics([])
      await onSaved()
    } catch (caught: unknown) {
      setError(caught instanceof ApiError ? caught.message : 'Could not add title')
    }
  }

  async function onAddTopic(event: FormEvent) {
    event.preventDefault()
    setError(null)
    const slug = slugify(topicSlug)
    if (!isValidSlug(slug)) {
      setError('Topic slug must be lowercase letters, digits, and hyphens.')
      return
    }
    try {
      await createEntertainmentTopic({ slug, name: topicSlug })
      setTopicSlug('')
      await onSaved()
    } catch (caught: unknown) {
      setError(caught instanceof ApiError ? caught.message : 'Could not add topic')
    }
  }

  return (
    <Card>
      <CardHeader>
        <div>
          <CardTitle className="text-base">Add to the library</CardTitle>
          <CardDescription>A work you have seen, started, or want to see.</CardDescription>
        </div>
        <Plus className="size-4 text-entertainment" aria-hidden />
      </CardHeader>
      {error !== null ? (
        <p className="mb-3 text-sm text-bad" role="alert">
          {error}
        </p>
      ) : null}
      <form className="grid gap-3 sm:grid-cols-2" onSubmit={onAddTopic}>
        <div className="sm:col-span-2">
          <Label htmlFor="topic-slug">New topic</Label>
          <div className="mt-1 flex gap-2">
            <Input
              id="topic-slug"
              value={topicSlug}
              onChange={(event) => setTopicSlug(event.target.value)}
              placeholder="physics"
            />
            <Button type="submit" variant="secondary">
              Add topic
            </Button>
          </div>
        </div>
      </form>
      <form className="mt-4 grid gap-3 sm:grid-cols-2" onSubmit={onSubmit}>
        <div className="sm:col-span-2">
          <Label htmlFor="title-name">Title</Label>
          <Input
            id="title-name"
            className="mt-1"
            value={name}
            onChange={(event) => setName(event.target.value)}
            required
          />
        </div>
        <div>
          <Label htmlFor="title-kind">Kind</Label>
          <Select
            id="title-kind"
            className="mt-1"
            value={kind}
            onChange={(event) => setKind(event.target.value as EntertainmentKind)}
          >
            {KINDS.map((item) => (
              <option key={item} value={item}>
                {kindLabel(item)}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Label htmlFor="title-status">Status</Label>
          <Select
            id="title-status"
            className="mt-1"
            value={status}
            onChange={(event) => setStatus(event.target.value as EntertainmentStatus)}
          >
            {STATUSES.map((item) => (
              <option key={item.id} value={item.id}>
                {item.label}
              </option>
            ))}
          </Select>
        </div>
        <div>
          <Label htmlFor="title-creator">Creator</Label>
          <Input
            id="title-creator"
            className="mt-1"
            value={creator}
            onChange={(event) => setCreator(event.target.value)}
          />
        </div>
        <div>
          <Label htmlFor="title-recommended">Recommended by</Label>
          <Input
            id="title-recommended"
            className="mt-1"
            value={recommendedBy}
            onChange={(event) => setRecommendedBy(event.target.value)}
          />
        </div>
        <div>
          <Label htmlFor="title-progress">Bookmark</Label>
          <Input
            id="title-progress"
            className="mt-1"
            value={progress}
            placeholder="S2E5"
            onChange={(event) => setProgress(event.target.value)}
          />
        </div>
        <div>
          <Label htmlFor="title-image-url">Poster URL</Label>
          <Input
            id="title-image-url"
            className="mt-1"
            value={imageUrl}
            placeholder="https://"
            onChange={(event) => setImageUrl(event.target.value)}
          />
        </div>
        <div className="sm:col-span-2">
          <Label htmlFor="title-image-file">Or upload a poster</Label>
          <Input
            id="title-image-file"
            className="mt-1"
            type="file"
            accept="image/jpeg,image/png,image/webp,image/gif"
            onChange={(event) => setImageFile(event.target.files?.[0] ?? null)}
          />
        </div>
        {topics.length > 0 ? (
          <fieldset className="sm:col-span-2">
            <legend className="text-xs font-medium text-muted">Topics</legend>
            <div className="mt-2 flex flex-wrap gap-2">
              {topics.map((topic) => {
                const checked = selectedTopics.includes(topic.slug)
                return (
                  <label
                    key={topic.slug}
                    className={cn(
                      'cursor-pointer rounded-full border px-3 py-1 text-xs',
                      checked
                        ? 'border-entertainment bg-entertainment/15 text-ink'
                        : 'border-line text-muted',
                    )}
                  >
                    <input
                      type="checkbox"
                      className="sr-only"
                      checked={checked}
                      onChange={() => {
                        setSelectedTopics((current) =>
                          checked
                            ? current.filter((slug) => slug !== topic.slug)
                            : [...current, topic.slug],
                        )
                      }}
                    />
                    {topic.name}
                  </label>
                )
              })}
            </div>
          </fieldset>
        ) : null}
        <div className="sm:col-span-2">
          <Button type="submit">Add title</Button>
        </div>
      </form>
    </Card>
  )
}
