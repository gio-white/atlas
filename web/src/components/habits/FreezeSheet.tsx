import { type FormEvent, useEffect, useId, useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { ApiError, createFreeze, type Habit } from '@/lib/api'
import { cn } from '@/lib/utils'

/**
 * Freeze… (habits brief §9): From and To (both the given day at first), an optional reason, and
 * a switch to freeze every habit instead of this one. Frozen days count neither way.
 */
export function FreezeSheet({
  open,
  onOpenChange,
  habit,
  day,
  onSaved,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  habit: Pick<Habit, 'slug' | 'name'>
  day: string
  onSaved: () => void
}) {
  const id = useId()
  const [from, setFrom] = useState(day)
  const [to, setTo] = useState(day)
  const [reason, setReason] = useState('')
  const [allHabits, setAllHabits] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!open) return
    setFrom(day)
    setTo(day)
    setReason('')
    setAllHabits(false)
    setError(null)
  }, [open, day])

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (from === '' || to === '') {
      setError('Pick both dates.')
      return
    }
    if (to < from) {
      setError('To can’t be before From.')
      return
    }
    setSaving(true)
    setError(null)
    try {
      await createFreeze({
        ...(allHabits ? {} : { habit: habit.slug }),
        start_on: from,
        end_on: to,
        ...(reason.trim() === '' ? {} : { reason: reason.trim() }),
      })
      onSaved()
      onOpenChange(false)
    } catch (caught: unknown) {
      setError(caught instanceof ApiError ? caught.message : 'Couldn’t save the freeze. Try again.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Freeze {allHabits ? 'all habits' : habit.name}</DialogTitle>
          <DialogDescription>
            A frozen day is neither done nor not done, and doesn’t break a streak.
          </DialogDescription>
        </DialogHeader>
        <form className="flex flex-col gap-4" onSubmit={submit} noValidate>
          <div className="grid grid-cols-2 gap-3">
            <div className="flex flex-col gap-1.5">
              <label htmlFor={`${id}-from`} className="text-sm font-medium text-ink">
                From
              </label>
              <Input
                id={`${id}-from`}
                type="date"
                className="h-11"
                value={from}
                onChange={(event) => {
                  setFrom(event.target.value)
                  if (to < event.target.value) setTo(event.target.value)
                }}
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor={`${id}-to`} className="text-sm font-medium text-ink">
                To
              </label>
              <Input
                id={`${id}-to`}
                type="date"
                className="h-11"
                min={from}
                value={to}
                onChange={(event) => setTo(event.target.value)}
              />
            </div>
          </div>
          <div className="flex flex-col gap-1.5">
            <label htmlFor={`${id}-reason`} className="text-sm font-medium text-ink">
              Reason <span className="font-normal text-muted">(optional)</span>
            </label>
            <Input
              id={`${id}-reason`}
              className="h-11"
              placeholder="Holiday"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
            />
          </div>
          <label className="flex min-h-11 cursor-pointer items-center justify-between gap-3 has-[:focus-visible]:rounded-lg has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-accent">
            <span className="text-sm font-medium text-ink">Freeze all habits</span>
            <input
              type="checkbox"
              role="switch"
              aria-checked={allHabits}
              className="sr-only"
              checked={allHabits}
              onChange={(event) => setAllHabits(event.target.checked)}
            />
            <span
              aria-hidden
              className={cn(
                'relative inline-flex h-6 w-11 shrink-0 rounded-full motion-safe:transition-colors motion-safe:duration-200',
                allHabits ? 'bg-accent' : 'bg-line',
              )}
            >
              <span
                className={cn(
                  'absolute top-0.5 left-0.5 size-5 rounded-full bg-surface shadow-sm motion-safe:transition-transform motion-safe:duration-200',
                  allHabits && 'translate-x-5',
                )}
              />
            </span>
          </label>
          {error !== null && (
            <p className="text-sm text-bad" role="alert">
              {error}
            </p>
          )}
          <div className="flex justify-end gap-2">
            <Button type="button" variant="ghost" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={saving}>
              Freeze
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
