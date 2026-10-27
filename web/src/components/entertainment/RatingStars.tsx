import { Star } from 'lucide-react'

import { cn } from '@/lib/utils'

const STARS = [1, 2, 3, 4, 5]

/** Five-star rating. Clicking the current rating clears it; read-only without onChange. */
export function RatingStars({
  value,
  onChange,
  label,
}: {
  value: number | null
  onChange?: (next: number | null) => void
  label: string
}) {
  if (onChange === undefined) {
    return (
      <span className="inline-flex" role="img" aria-label={`${label}: ${value ?? 'unrated'}`}>
        {STARS.map((star) => (
          <Star key={star} className={cn('size-3.5', starTone(value, star))} aria-hidden />
        ))}
      </span>
    )
  }
  return (
    <fieldset className="inline-flex" aria-label={label}>
      {STARS.map((star) => (
        <button
          key={star}
          type="button"
          className="cursor-pointer rounded p-0.5 hover:bg-raised focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          aria-label={value === star ? `Clear ${label}` : `${star} of 5`}
          aria-pressed={value !== null && star <= value}
          onClick={(event) => {
            event.stopPropagation()
            onChange(value === star ? null : star)
          }}
        >
          <Star className={cn('size-4', starTone(value, star))} aria-hidden />
        </button>
      ))}
    </fieldset>
  )
}

function starTone(value: number | null, star: number): string {
  return value !== null && star <= value ? 'fill-warn text-warn' : 'text-line'
}
