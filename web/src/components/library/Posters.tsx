import { Clapperboard } from 'lucide-react'

import { RatingStars } from '@/components/library/RatingStars'
import type { LibraryTitle } from '@/lib/api'
import { shortDateLabel } from '@/lib/dates'
import { KIND_LABEL } from '@/lib/library'

export function Thumb({ title }: { title: LibraryTitle }) {
  if (title.image) {
    return <img src={title.image} alt="" className="size-10 shrink-0 rounded-md object-cover" />
  }
  return (
    <div className="flex size-10 shrink-0 items-center justify-center rounded-md border border-line bg-raised text-muted">
      <Clapperboard className="size-4" aria-hidden />
    </div>
  )
}

export function PosterCard({ title }: { title: LibraryTitle }) {
  return (
    <article className="overflow-hidden rounded-2xl border border-line bg-surface shadow-[var(--shadow-card)]">
      <div className="relative aspect-[16/10]">
        {title.image ? (
          <img src={title.image} alt="" className="size-full object-cover" />
        ) : (
          <div className="flex size-full items-center justify-center bg-raised text-muted">
            <Clapperboard className="size-8" aria-hidden />
          </div>
        )}
        <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/80 to-transparent p-3 text-white">
          <p className="font-medium leading-tight">{title.name}</p>
          <p className="mt-0.5 text-xs text-white/80">
            {KIND_LABEL[title.kind]}
            {title.creator ? ` · ${title.creator}` : ''}
          </p>
        </div>
      </div>
      <div className="flex items-center justify-between gap-2 p-3">
        {title.finished_on ? (
          <p className="text-xs text-muted">Finished {shortDateLabel(title.finished_on)}</p>
        ) : (
          <span />
        )}
        {title.rating !== null ? <RatingStars value={title.rating} label="rating" /> : null}
      </div>
    </article>
  )
}
