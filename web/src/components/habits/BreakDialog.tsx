import { type FormEvent, useEffect, useState } from 'react'

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
import { ApiError, addHabitBreak } from '@/lib/api'

/** Skip one day or pause a habit for a range; covered days never break a streak. */
export function BreakDialog({
  open,
  onOpenChange,
  slug,
  name,
  defaultDay,
  onSaved,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  slug: string
  name: string
  defaultDay: string
  onSaved: () => Promise<void>
}) {
  const [startOn, setStartOn] = useState(defaultDay)
  const [endOn, setEndOn] = useState(defaultDay)
  const [note, setNote] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  useEffect(() => {
    if (!open) return
    setStartOn(defaultDay)
    setEndOn(defaultDay)
    setNote('')
    setError(null)
  }, [open, defaultDay])

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    if (endOn < startOn) {
      setError('The pause must end on or after it starts.')
      return
    }
    setPending(true)
    try {
      await addHabitBreak(slug, { start_on: startOn, end_on: endOn, note: note.trim() || null })
      onOpenChange(false)
      await onSaved()
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'Could not save the pause')
    } finally {
      setPending(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Skip or pause {name}</DialogTitle>
          <DialogDescription>
            Days in a pause don’t count against you and don’t break the streak. A weekly or monthly
            target shrinks to the days you have left.
          </DialogDescription>
        </DialogHeader>
        <form className="grid gap-3 sm:grid-cols-2" onSubmit={onSubmit}>
          <div className="flex flex-col gap-1">
            <Label htmlFor="break-start">From</Label>
            <Input
              id="break-start"
              type="date"
              value={startOn}
              onChange={(event) => {
                setStartOn(event.target.value)
                if (endOn < event.target.value) setEndOn(event.target.value)
              }}
            />
          </div>
          <div className="flex flex-col gap-1">
            <Label htmlFor="break-end">To</Label>
            <Input
              id="break-end"
              type="date"
              value={endOn}
              onChange={(event) => setEndOn(event.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1 sm:col-span-2">
            <Label htmlFor="break-note">Reason (optional)</Label>
            <Input
              id="break-note"
              value={note}
              placeholder="Travel, sick, rest week…"
              onChange={(event) => setNote(event.target.value)}
            />
          </div>
          {error !== null ? (
            <p className="text-sm text-bad sm:col-span-2" role="alert">
              {error}
            </p>
          ) : null}
          <Button type="submit" className="sm:col-span-2" disabled={pending}>
            {startOn === endOn ? 'Skip this day' : 'Pause'}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}
