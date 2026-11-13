import { type FormEvent, useEffect, useState } from 'react'

import { errorMessage } from '@/components/quests/useQuestView'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { createQuestTask } from '@/lib/api'
import { notifyInboxChanged } from '@/lib/quests'

/** Add → Task: capture a title into the Inbox from any page, the same way the Inbox does. */
export function QuickTaskDialog({
  open,
  onOpenChange,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
}) {
  const [title, setTitle] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      setTitle('')
      setError(null)
    }
  }, [open])

  async function onSubmit(event: FormEvent) {
    event.preventDefault()
    const trimmed = title.trim()
    if (trimmed === '' || busy) return
    setBusy(true)
    setError(null)
    try {
      await createQuestTask({ title: trimmed })
      notifyInboxChanged()
      onOpenChange(false)
    } catch (caught) {
      setError(errorMessage(caught, "Couldn't add it. Try again."))
    } finally {
      setBusy(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New task</DialogTitle>
          <DialogDescription>It goes to your Inbox, to sort later.</DialogDescription>
        </DialogHeader>
        <form className="flex flex-col gap-3" onSubmit={onSubmit}>
          <Input
            autoFocus
            aria-label="Task title"
            placeholder="What's on your mind?"
            value={title}
            readOnly={busy}
            onChange={(event) => setTitle(event.target.value)}
          />
          {error !== null && (
            <p className="text-sm text-bad" role="alert">
              {error}
            </p>
          )}
          <div>
            <Button
              type="submit"
              className="bg-iris hover:bg-iris/90"
              disabled={busy || title.trim() === ''}
            >
              Add to Inbox
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
