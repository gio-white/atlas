import { CalendarDays } from 'lucide-react'
import { useRef } from 'react'

import { Button } from '@/components/ui/button'
import { dayLabel, longDateLabel } from '@/lib/dates'
import { cn, todayIso } from '@/lib/utils'

/**
 * The header's date. It is also the "As of" control: pressing it opens the date picker, and
 * while a past or future date is chosen it reads "As of …" with a way back to today.
 */
export function AsOfControl({
  asOf,
  onChange,
}: {
  asOf: string
  /** Called with a `YYYY-MM-DD` date, or `''` for today. */
  onChange: (value: string) => void
}) {
  const inputRef = useRef<HTMLInputElement>(null)
  const elsewhere = asOf !== todayIso()

  function openPicker() {
    const input = inputRef.current
    if (input === null) return
    try {
      input.showPicker()
    } catch {
      input.focus()
    }
  }

  return (
    <div className="flex min-w-0 items-center gap-1">
      <div className="relative min-w-0">
        <button
          type="button"
          onClick={openPicker}
          aria-label={
            elsewhere
              ? `As of ${dayLabel(asOf)}. Choose another date`
              : `${longDateLabel(asOf)}. View another date`
          }
          className={cn(
            'inline-flex min-h-9 max-w-full cursor-pointer items-center gap-2 rounded-lg px-2 text-sm font-medium motion-safe:transition-colors motion-safe:duration-200 focus-visible:ring-2 focus-visible:ring-accent focus-visible:outline-none',
            elsewhere
              ? 'border border-warn/40 bg-warn/10 text-ink hover:bg-warn/20'
              : 'text-muted hover:bg-raised hover:text-ink',
          )}
        >
          <CalendarDays className="size-4 shrink-0" aria-hidden />
          {elsewhere ? (
            <span className="truncate">As of {dayLabel(asOf)}</span>
          ) : (
            <>
              <span className="truncate sm:hidden">{dayLabel(asOf)}</span>
              <span className="hidden truncate sm:inline">{longDateLabel(asOf)}</span>
            </>
          )}
        </button>
        {/* The native picker anchors to this input; the button above is what people use. */}
        <input
          ref={inputRef}
          type="date"
          value={asOf}
          onChange={(event) => onChange(event.target.value)}
          tabIndex={-1}
          aria-hidden
          className="pointer-events-none absolute inset-0 size-full opacity-0"
        />
      </div>
      {elsewhere && (
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="shrink-0"
          aria-label="Back to today"
          onClick={() => onChange('')}
        >
          <span className="sm:hidden">Today</span>
          <span className="hidden sm:inline">Back to today</span>
        </Button>
      )}
    </div>
  )
}
