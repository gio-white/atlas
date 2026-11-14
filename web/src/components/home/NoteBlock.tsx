import { type FormEvent, type KeyboardEvent, useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import { ApiError, amendEntry, type JournalDay, logJournal } from '@/lib/api'

import { HomeBlock } from './HomeBlock'

/**
 * Today's note: a one-line field that grows while you write. Saving writes today's journal note
 * (the first save creates it, later ones amend it). "Earlier notes" lists the past ones.
 */
export function NoteBlock({
  journal,
  asOf,
  search,
  onSaved,
  className,
}: {
  journal: JournalDay | null
  asOf: string
  search: string
  onSaved: () => Promise<void>
  className?: string
}) {
  const saved = journal?.text ?? ''
  const [text, setText] = useState(saved)
  const [focused, setFocused] = useState(false)
  const [pending, setPending] = useState(false)
  const [status, setStatus] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    setText(saved)
    setStatus(null)
    setError(null)
  }, [saved])

  const trimmed = text.trim()
  const changed = trimmed !== saved.trim()
  const open = focused || text.includes('\n') || changed

  async function save() {
    if (journal === null || trimmed === '' || !changed || pending) return
    setPending(true)
    setError(null)
    setStatus(null)
    try {
      if (journal.entry_id === null) await logJournal({ text: trimmed, occurred_on: asOf })
      else await amendEntry(journal.entry_id, { value: trimmed })
      setStatus('Saved')
      await onSaved()
    } catch (caught) {
      setError(
        caught instanceof ApiError && caught.status === 0
          ? caught.message
          : 'Couldn’t save your note. Try again.',
      )
    } finally {
      setPending(false)
    }
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    void save()
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
      event.preventDefault()
      void save()
    }
  }

  return (
    <HomeBlock
      id="note"
      title="Note for today"
      action={{ label: 'Earlier notes', to: '/journal' }}
      search={search}
      unavailable={journal === null}
      className={className}
    >
      <form className="flex flex-col gap-2" onSubmit={onSubmit}>
        <textarea
          aria-labelledby="home-note"
          rows={open ? 4 : 1}
          value={text}
          placeholder="How did today go?"
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          onKeyDown={onKeyDown}
          onChange={(event) => {
            setText(event.target.value)
            setStatus(null)
          }}
          className="w-full resize-none rounded-lg border border-line bg-canvas px-3 py-2 text-sm text-ink placeholder:text-muted motion-safe:transition-[height] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-iris"
        />
        {(changed || status !== null || error !== null) && (
          <div className="flex items-center gap-3">
            {changed && (
              <Button type="submit" size="sm" disabled={pending || trimmed === ''}>
                Save note
              </Button>
            )}
            {status !== null && (
              <p className="text-sm text-muted" role="status">
                {status}
              </p>
            )}
            {error !== null && (
              <p className="text-sm text-bad" role="alert">
                {error}
              </p>
            )}
          </div>
        )}
      </form>
    </HomeBlock>
  )
}
