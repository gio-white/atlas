import { useEffect, useState } from 'react'

import { LogForm } from '@/components/LogForm'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { ApiError, listMetrics, type Metric } from '@/lib/api'

type LogDialogProps = {
  open: boolean
  onOpenChange: (open: boolean) => void
  occurredOn: string
}

export function LogDialog({ open, onOpenChange, occurredOn }: LogDialogProps) {
  const [metrics, setMetrics] = useState<Metric[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!open) return
    let cancelled = false
    setError(null)
    listMetrics()
      .then((rows) => {
        if (!cancelled) setMetrics(rows)
      })
      .catch((caught: unknown) => {
        if (!cancelled) {
          setError(caught instanceof ApiError ? caught.message : 'Could not load metrics')
          setMetrics([])
        }
      })
    return () => {
      cancelled = true
    }
  }, [open])

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>New entry</DialogTitle>
          <DialogDescription>One capture path. Counts for {occurredOn}.</DialogDescription>
        </DialogHeader>
        {error !== null && (
          <p className="text-sm text-bad" role="alert">
            {error}
          </p>
        )}
        {metrics === null ? (
          <p className="text-sm text-muted">Loading metrics…</p>
        ) : (
          <LogForm metrics={metrics} occurredOn={occurredOn} onLogged={() => onOpenChange(false)} />
        )}
      </DialogContent>
    </Dialog>
  )
}
