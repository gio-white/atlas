import { Minus, Plus } from 'lucide-react'
import type { ReactNode } from 'react'

import { cn } from '@/lib/utils'

/** A question in a sheet: its legend, then its answers. */
export function Question({
  legend,
  children,
  className,
}: {
  legend: string
  children: ReactNode
  className?: string
}) {
  return (
    <fieldset className={cn('flex min-w-0 flex-col gap-2', className)}>
      <legend className="mb-2 text-sm font-medium text-ink">{legend}</legend>
      {children}
    </fieldset>
  )
}

const CHIP =
  'inline-flex min-h-11 cursor-pointer items-center justify-center rounded-full border px-4 text-sm select-none motion-safe:transition-colors motion-safe:duration-200 has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-accent'

/** One answer of several, as a row of chips (radio buttons underneath). */
export function Choices<T extends string>({
  name,
  options,
  value,
  onChange,
}: {
  name: string
  options: { id: T; label: string }[]
  value: T
  onChange: (next: T) => void
}) {
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((option) => (
        <label
          key={option.id}
          className={cn(
            CHIP,
            value === option.id
              ? 'border-accent bg-accent/10 font-medium text-ink'
              : 'border-line text-muted hover:text-ink',
          )}
        >
          <input
            type="radio"
            className="sr-only"
            name={name}
            value={option.id}
            checked={value === option.id}
            onChange={() => onChange(option.id)}
          />
          {option.label}
        </label>
      ))}
    </div>
  )
}

const WEEKDAYS = [
  { day: 1, short: 'M', long: 'Monday' },
  { day: 2, short: 'T', long: 'Tuesday' },
  { day: 3, short: 'W', long: 'Wednesday' },
  { day: 4, short: 'T', long: 'Thursday' },
  { day: 5, short: 'F', long: 'Friday' },
  { day: 6, short: 'S', long: 'Saturday' },
  { day: 7, short: 'S', long: 'Sunday' },
]

/** Monday to Sunday as seven round toggles (checkboxes underneath). */
export function WeekdayPicker({
  value,
  onChange,
}: {
  value: number[]
  onChange: (next: number[]) => void
}) {
  return (
    <div className="flex gap-1.5">
      {WEEKDAYS.map(({ day, short, long }) => {
        const on = value.includes(day)
        return (
          <label
            key={day}
            className={cn(
              CHIP,
              'size-11 rounded-full px-0',
              on ? 'border-accent bg-accent text-on-accent' : 'border-line text-muted',
            )}
          >
            <input
              type="checkbox"
              className="sr-only"
              checked={on}
              onChange={() =>
                onChange(
                  on ? value.filter((item) => item !== day) : [...value, day].sort((a, b) => a - b),
                )
              }
            />
            <span aria-hidden>{short}</span>
            <span className="sr-only">{long}</span>
          </label>
        )
      })}
    </div>
  )
}

/** A count with − and + (1 to `most`), then its unit: "3 times a week". */
export function Stepper({
  value,
  most,
  unit,
  onChange,
}: {
  value: number
  most: number
  unit: string
  onChange: (next: number) => void
}) {
  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        aria-label="Fewer"
        disabled={value <= 1}
        onClick={() => onChange(Math.max(1, value - 1))}
        className="inline-flex size-11 items-center justify-center rounded-full border border-line text-ink hover:bg-raised disabled:opacity-40 focus-visible:ring-2 focus-visible:ring-accent focus-visible:outline-none"
      >
        <Minus className="size-4" aria-hidden />
      </button>
      <output
        className="w-8 text-center text-lg font-semibold text-ink tabular-nums"
        aria-live="polite"
      >
        {value}
      </output>
      <button
        type="button"
        aria-label="More"
        disabled={value >= most}
        onClick={() => onChange(Math.min(most, value + 1))}
        className="inline-flex size-11 items-center justify-center rounded-full border border-line text-ink hover:bg-raised disabled:opacity-40 focus-visible:ring-2 focus-visible:ring-accent focus-visible:outline-none"
      >
        <Plus className="size-4" aria-hidden />
      </button>
      <span className="text-sm text-muted">{unit}</span>
    </div>
  )
}
