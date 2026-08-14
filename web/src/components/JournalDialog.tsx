import { type FormEvent, useEffect, useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { ApiError, getJournal, logJournal } from '@/lib/api'

type JournalDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  occurredOn: string
  onSaved?: () => Promise<void> | void
}

export function JournalDialog({ open, onOpenChange, occurredOn, onSaved }: JournalDialogProps) {
  const [text, setText] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  useEffect(() => {
    if (!open) return
    let cancelled = false
    setError(null)
    getJournal(occurredOn)
      .then((day) => {
        if (!cancelled) setText(day.text ?? '')
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setError(caught instanceof ApiError ? caught.message : 'Could not load journal')
        }
      })
    return () => {
      cancelled = true
    }
  }, [open, occurredOn])

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    const cleaned = text.trim()
    if (cleaned === '') return
    setError(null)
    setPending(true)
    try {
      await logJournal({ text: cleaned, occurred_on: occurredOn })
      await onSaved?.()
      onOpenChange(false)
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Could not save journal')
    } finally {
      setPending(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Journal</DialogTitle>
          <DialogDescription>A text entry for {occurredOn}.</DialogDescription>
        </DialogHeader>
        {error !== null && (
          <p className="text-sm text-bad" role="alert">
            {error}
          </p>
        )}
        <form className="flex flex-col gap-3" onSubmit={onSubmit}>
          <div className="flex flex-col gap-1">
            <Label htmlFor="journal-text">Today</Label>
            <textarea
              id="journal-text"
              className="min-h-32 w-full rounded-lg border border-line bg-canvas px-3 py-2 text-sm text-ink placeholder:text-muted motion-safe:transition-shadow motion-safe:duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
              value={text}
              onChange={(event) => setText(event.target.value)}
              placeholder="What happened today?"
            />
          </div>
          <Button type="submit" disabled={pending || text.trim() === ''}>
            Save
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}
