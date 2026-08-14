import { type FormEvent, useState } from 'react'
import { Link } from 'react-router-dom'

import { ThemeToggle } from '@/components/ThemeToggle'
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
import { persistDisplayName } from '@/lib/profile'

type ProfileDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  displayName: string
  onDisplayName: (name: string) => void
  asOf: string
  onAsOf: (value: string) => void
}

export function ProfileDialog({
  open,
  onOpenChange,
  displayName,
  onDisplayName,
  asOf,
  onAsOf,
}: ProfileDialogProps) {
  const [draft, setDraft] = useState(displayName)

  function onSubmit(event: FormEvent) {
    event.preventDefault()
    onDisplayName(persistDisplayName(draft))
    onOpenChange(false)
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (next) setDraft(displayName)
        onOpenChange(next)
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Profile</DialogTitle>
          <DialogDescription>Local display name, theme, and catalog. No account.</DialogDescription>
        </DialogHeader>
        <form className="flex flex-col gap-4" onSubmit={onSubmit}>
          <div className="flex flex-col gap-1">
            <Label htmlFor="display-name">Name</Label>
            <Input
              id="display-name"
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              autoComplete="nickname"
            />
          </div>
          <div className="flex flex-col gap-1">
            <Label htmlFor="as-of">As of</Label>
            <Input
              id="as-of"
              type="date"
              value={asOf}
              onChange={(event) => onAsOf(event.target.value)}
            />
          </div>
          <div className="flex items-center justify-between gap-3">
            <p className="text-sm text-muted">Theme</p>
            <ThemeToggle />
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Button type="submit">Save</Button>
            <Button asChild type="button" variant="outline">
              <Link to="/catalog" onClick={() => onOpenChange(false)}>
                Catalog
              </Link>
            </Button>
            <Button asChild type="button" variant="ghost">
              <Link to="/week" onClick={() => onOpenChange(false)}>
                Week
              </Link>
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}
