import { Sparkles } from 'lucide-react'
import { type FormEvent, type ReactNode, useEffect, useRef, useState } from 'react'

import { RatingStars } from '@/components/entertainment/RatingStars'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import {
  ApiError,
  createEntertainmentTitle,
  deleteEntertainmentTitle,
  type EntertainmentKind,
  type EntertainmentStatus,
  type EntertainmentTitle,
  type EntertainmentTopic,
  lookupEntertainmentLink,
  updateEntertainmentTitle,
  uploadEntertainmentImage,
} from '@/lib/api'
import { KIND_LABEL, KINDS, parseTags, STATUSES, uniqueTitleSlug } from '@/lib/entertainment'
import { isValidSlug } from '@/lib/slug'
import { cn } from '@/lib/utils'

/**
 * Adds a title when `title` is null, otherwise edits or deletes it. A pasted link is looked
 * up to prefill name, kind, creator, and poster; `initialLink` does that on open.
 */
export function TitleDialog({
  open,
  onOpenChange,
  title,
  initialLink = null,
  defaultKind,
  topics,
  takenSlugs,
  onSaved,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: EntertainmentTitle | null
  initialLink?: string | null
  defaultKind: EntertainmentKind
  topics: EntertainmentTopic[]
  takenSlugs: string[]
  onSaved: () => Promise<void>
}) {
  const editing = title !== null
  const initialPoster = title?.image?.startsWith('http') ? title.image : ''
  const [name, setName] = useState('')
  const [kind, setKind] = useState<EntertainmentKind>(defaultKind)
  const [status, setStatus] = useState<EntertainmentStatus>('queued')
  const [rating, setRating] = useState<number | null>(null)
  const [creator, setCreator] = useState('')
  const [recommendedBy, setRecommendedBy] = useState('')
  const [progress, setProgress] = useState('')
  const [startedOn, setStartedOn] = useState('')
  const [finishedOn, setFinishedOn] = useState('')
  const [link, setLink] = useState('')
  const [note, setNote] = useState('')
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [newTags, setNewTags] = useState('')
  const [posterUrl, setPosterUrl] = useState('')
  const [posterFile, setPosterFile] = useState<File | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [lookingUp, setLookingUp] = useState(false)
  const [lookupNote, setLookupNote] = useState<string | null>(null)
  const lookupRun = useRef(0)

  async function runLookup(url: string) {
    const cleaned = url.trim()
    if (!/^https?:\/\/\S+$/.test(cleaned)) {
      setLookupNote('Paste a full http(s) link to look it up.')
      return
    }
    const run = ++lookupRun.current
    setLookingUp(true)
    setLookupNote(null)
    try {
      const found = await lookupEntertainmentLink(cleaned)
      if (run !== lookupRun.current) return
      // A new title takes everything found; an existing one only fills blanks.
      const fill = (current: string, next: string | null) =>
        next !== null && (!editing || current.trim() === '') ? next : current
      setLink(found.link)
      setName((current) => fill(current, found.name))
      setCreator((current) => fill(current, found.creator))
      if (!posterFile) setPosterUrl((current) => fill(current, found.image_url))
      if (found.kind !== null && !editing) setKind(found.kind)
      if (found.existing !== null && found.existing !== title?.slug) {
        setLookupNote(`Already in your library (${found.existing}).`)
      } else if (found.name === null) {
        setLookupNote('No title found at that link; fill it in by hand.')
      }
    } catch (caught) {
      if (run !== lookupRun.current) return
      setLookupNote(
        caught instanceof ApiError
          ? `Could not look that up: ${caught.message}`
          : 'Could not look that up.',
      )
    } finally {
      if (run === lookupRun.current) setLookingUp(false)
    }
  }

  // runLookup reads the current form state; listing it would re-run the reset on every render.
  // biome-ignore lint/correctness/useExhaustiveDependencies: reset only when the dialog opens
  useEffect(() => {
    if (!open) return
    setName(title?.name ?? '')
    setKind(title?.kind ?? defaultKind)
    setStatus(title?.status ?? 'queued')
    setRating(title?.rating ?? null)
    setCreator(title?.creator ?? '')
    setRecommendedBy(title?.recommended_by ?? '')
    setProgress(title?.progress ?? '')
    setStartedOn(title?.started_on ?? '')
    setFinishedOn(title?.finished_on ?? '')
    setLink(title?.link ?? '')
    setNote(title?.note ?? '')
    setSelectedTags(title?.topics.map((topic) => topic.slug) ?? [])
    setNewTags('')
    setPosterUrl(title?.image?.startsWith('http') ? title.image : '')
    setPosterFile(null)
    setError(null)
    setPending(false)
    setConfirmDelete(false)
    setLookingUp(false)
    setLookupNote(null)
    lookupRun.current += 1
    if (title === null && initialLink) {
      setLink(initialLink)
      void runLookup(initialLink)
    }
  }, [open, title, defaultKind, initialLink])

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    const cleaned = name.trim()
    if (cleaned === '') {
      setError('name must be a non-empty string')
      return
    }
    const fields = {
      name: cleaned,
      kind,
      status,
      rating,
      creator: creator.trim() || null,
      recommended_by: recommendedBy.trim() || null,
      progress: progress.trim() || null,
      started_on: startedOn || null,
      finished_on: finishedOn || null,
      link: link.trim() || null,
      note: note.trim() || null,
      topics: [...new Set([...selectedTags, ...parseTags(newTags)])],
    }
    setError(null)
    setPending(true)
    try {
      let saved: EntertainmentTitle
      if (title === null) {
        const slug = uniqueTitleSlug(cleaned, kind, takenSlugs)
        if (!isValidSlug(slug)) {
          setError('Name must contain letters or digits so a slug can be derived.')
          setPending(false)
          return
        }
        saved = await createEntertainmentTitle({
          slug,
          ...fields,
          image_url: posterFile ? null : posterUrl.trim() || null,
        })
      } else {
        const posterChanged = posterUrl.trim() !== initialPoster
        saved = await updateEntertainmentTitle(title.slug, {
          ...fields,
          ...(posterChanged && !posterFile ? { image_url: posterUrl.trim() || null } : {}),
        })
      }
      if (posterFile) await uploadEntertainmentImage(saved.slug, posterFile)
      onOpenChange(false)
      await onSaved()
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Could not save title')
    } finally {
      setPending(false)
    }
  }

  async function onDelete() {
    if (title === null) return
    if (!confirmDelete) {
      setConfirmDelete(true)
      return
    }
    setPending(true)
    try {
      await deleteEntertainmentTitle(title.slug)
      onOpenChange(false)
      await onSaved()
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Could not delete title')
      setPending(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[calc(100dvh-2rem)] max-w-2xl overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{editing ? 'Edit title' : 'Add to the library'}</DialogTitle>
          <DialogDescription>
            Something you have seen, are into, or want to get to.
          </DialogDescription>
        </DialogHeader>
        <form className="grid gap-3 sm:grid-cols-2" onSubmit={onSubmit}>
          <Field id="title-link" label="Link" wide>
            <div className="flex gap-2">
              <Input
                id="title-link"
                type="url"
                value={link}
                placeholder="Paste a link to fill the rest in: YouTube, Spotify, Goodreads…"
                onChange={(event) => setLink(event.target.value)}
                onPaste={(event) => {
                  const pasted = event.clipboardData.getData('text').trim()
                  if (!editing && /^https?:\/\//.test(pasted)) {
                    event.preventDefault()
                    setLink(pasted)
                    void runLookup(pasted)
                  }
                }}
              />
              <Button
                type="button"
                variant="secondary"
                className="shrink-0 whitespace-nowrap"
                disabled={lookingUp || link.trim() === ''}
                onClick={() => void runLookup(link)}
              >
                <Sparkles className="size-4" aria-hidden />
                {lookingUp ? 'Looking up…' : 'Look up'}
              </Button>
            </div>
            {lookupNote !== null ? (
              <p className="text-xs text-warn" role="status">
                {lookupNote}
              </p>
            ) : null}
          </Field>
          <Field id="title-name" label="Title" wide>
            <Input
              id="title-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              required
              autoFocus={!initialLink}
            />
          </Field>
          <Field id="title-kind" label="Kind">
            <Select
              id="title-kind"
              value={kind}
              onChange={(event) => setKind(event.target.value as EntertainmentKind)}
            >
              {KINDS.map((item) => (
                <option key={item} value={item}>
                  {KIND_LABEL[item]}
                </option>
              ))}
            </Select>
          </Field>
          <Field id="title-status" label="Status">
            <Select
              id="title-status"
              value={status}
              onChange={(event) => setStatus(event.target.value as EntertainmentStatus)}
            >
              {STATUSES.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.label}
                </option>
              ))}
            </Select>
          </Field>
          <Field id="title-creator" label="Creator">
            <Input
              id="title-creator"
              value={creator}
              placeholder="Director, author, artist, host"
              onChange={(event) => setCreator(event.target.value)}
            />
          </Field>
          <div className="flex flex-col gap-1">
            <span className="text-xs font-medium text-muted">Rating</span>
            <RatingStars value={rating} onChange={setRating} label="rating" />
          </div>
          <Field id="title-started" label="Started">
            <Input
              id="title-started"
              type="date"
              value={startedOn}
              onChange={(event) => setStartedOn(event.target.value)}
            />
          </Field>
          <Field id="title-finished" label="Finished">
            <Input
              id="title-finished"
              type="date"
              value={finishedOn}
              onChange={(event) => setFinishedOn(event.target.value)}
            />
          </Field>
          <Field id="title-recommended" label="Recommended by">
            <Input
              id="title-recommended"
              value={recommendedBy}
              onChange={(event) => setRecommendedBy(event.target.value)}
            />
          </Field>
          <Field id="title-progress" label="Bookmark">
            <Input
              id="title-progress"
              value={progress}
              placeholder="S2E5, p. 120, 34:10"
              onChange={(event) => setProgress(event.target.value)}
            />
          </Field>
          <fieldset className="flex flex-col gap-2 sm:col-span-2">
            <legend className="text-xs font-medium text-muted">Tags</legend>
            {topics.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {topics.map((topic) => {
                  const checked = selectedTags.includes(topic.slug)
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
                        onChange={() =>
                          setSelectedTags((current) =>
                            checked
                              ? current.filter((slug) => slug !== topic.slug)
                              : [...current, topic.slug],
                          )
                        }
                      />
                      {topic.name}
                    </label>
                  )
                })}
              </div>
            ) : null}
            <Input
              aria-label="New tags"
              value={newTags}
              placeholder="New tags, comma separated: sci-fi, comfort watch"
              onChange={(event) => setNewTags(event.target.value)}
            />
          </fieldset>
          <Field id="title-note" label="Notes" wide>
            <textarea
              id="title-note"
              rows={3}
              value={note}
              onChange={(event) => setNote(event.target.value)}
              className="w-full rounded-lg border border-line bg-canvas px-3 py-2 text-sm text-ink placeholder:text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              placeholder="What stuck with you, quotes, why you want to see it"
            />
          </Field>
          <Field id="title-image-url" label="Poster URL">
            <div className="flex items-center gap-2">
              {/^https?:\/\//.test(posterUrl.trim()) ? (
                <img
                  src={posterUrl.trim()}
                  alt=""
                  className="size-9 shrink-0 rounded-md border border-line object-cover"
                />
              ) : null}
              <Input
                id="title-image-url"
                value={posterUrl}
                placeholder="https://"
                onChange={(event) => setPosterUrl(event.target.value)}
              />
            </div>
          </Field>
          <Field id="title-image-file" label="Or upload a poster">
            <Input
              id="title-image-file"
              type="file"
              accept="image/jpeg,image/png,image/webp,image/gif"
              onChange={(event) => setPosterFile(event.target.files?.[0] ?? null)}
            />
          </Field>
          {error !== null ? (
            <p className="text-sm text-bad sm:col-span-2" role="alert">
              {error}
            </p>
          ) : null}
          <div className="flex flex-wrap items-center justify-between gap-2 sm:col-span-2">
            {editing ? (
              <Button type="button" variant="destructive" disabled={pending} onClick={onDelete}>
                {confirmDelete ? 'Click again to delete' : 'Delete'}
              </Button>
            ) : (
              <span />
            )}
            <Button type="submit" disabled={pending}>
              {editing ? 'Save' : 'Add title'}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function Field({
  id,
  label,
  wide = false,
  children,
}: {
  id: string
  label: string
  wide?: boolean
  children: ReactNode
}) {
  return (
    <div className={cn('flex flex-col gap-1', wide && 'sm:col-span-2')}>
      <Label htmlFor={id}>{label}</Label>
      {children}
    </div>
  )
}
