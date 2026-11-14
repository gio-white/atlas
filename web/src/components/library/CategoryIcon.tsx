import type { ReactNode } from 'react'

import type { CategoryId } from '@/lib/library'
import { cn } from '@/lib/utils'

export type IconId = CategoryId | 'insights'

// Sections are told apart by glyph, not colour (redesign brief §11): every tile is the same
// neutral surface with the glyph in the app accent and its details cut out in the surface colour.
const GLYPH = 'var(--accent)'
const INK = 'var(--raised)'

/** A rounded neutral tile with the category's glyph. */
export function CategoryIcon({ id, className }: { id: IconId; className?: string }) {
  return (
    <svg
      viewBox="0 0 100 100"
      className={cn('block overflow-visible', className)}
      aria-hidden="true"
      focusable="false"
    >
      <rect
        x="1"
        y="1"
        width="98"
        height="98"
        rx="23"
        fill="var(--raised)"
        stroke="var(--line)"
        strokeWidth="2"
      />
      {GLYPHS[id](INK)}
    </svg>
  )
}

const GLYPHS: Record<IconId, (ink: string) => ReactNode> = {
  videos: (ink) => (
    <>
      <g transform="rotate(-11 24 40)">
        <rect x="22" y="28" width="56" height="12" rx="4" fill={GLYPH} />
        <path d="M33 28h7l-6 12h-7zM49 28h7l-6 12h-7zM65 28h7l-6 12h-7z" fill={ink} />
      </g>
      <rect x="22" y="42" width="56" height="36" rx="7" fill={GLYPH} />
      <path d="M45 51.5v17.5l15-8.75z" fill={ink} />
    </>
  ),
  books: (ink) => (
    <>
      <path d="M50 33c-8-6-19-7-29-5v43c10-2 21-1 29 5z" fill={GLYPH} />
      <path d="M50 33c8-6 19-7 29-5v43c-10-2-21-1-29 5z" fill={GLYPH} fillOpacity="0.86" />
      <path d="M50 33v43" stroke={ink} strokeOpacity="0.35" strokeWidth="1.5" />
      <path
        d="M29 40h13M29 47h13M29 54h10"
        stroke={ink}
        strokeOpacity="0.3"
        strokeWidth="2.4"
        strokeLinecap="round"
      />
      <path d="M63 28.5v20l4.5-3.5 4.5 3.5v-21.5" fill={ink} />
    </>
  ),
  podcasts: (ink) => (
    <>
      <path
        d="M27 30a32 32 0 0 0 0 36M73 30a32 32 0 0 1 0 36"
        stroke={GLYPH}
        strokeOpacity="0.55"
        strokeWidth="4"
        strokeLinecap="round"
        fill="none"
      />
      <rect x="40" y="20" width="20" height="36" rx="10" fill={GLYPH} />
      <path
        d="M44 31h12M44 37h12M44 43h12"
        stroke={ink}
        strokeOpacity="0.35"
        strokeWidth="2.2"
        strokeLinecap="round"
      />
      <path
        d="M33 50a17 17 0 0 0 34 0M50 67v9M41 78h18"
        stroke={GLYPH}
        strokeWidth="4.5"
        strokeLinecap="round"
        fill="none"
      />
    </>
  ),
  music: (ink) => (
    <>
      <path d="M41 30l34-8v8l-34 8z" fill={GLYPH} />
      <rect x="39" y="30" width="5" height="40" rx="2.5" fill={GLYPH} />
      <rect x="72" y="22" width="5" height="40" rx="2.5" fill={GLYPH} />
      <ellipse cx="34" cy="71" rx="10" ry="8" transform="rotate(-18 34 71)" fill={GLYPH} />
      <ellipse cx="67" cy="63" rx="10" ry="8" transform="rotate(-18 67 63)" fill={GLYPH} />
      <circle cx="31" cy="69" r="2.5" fill={ink} fillOpacity="0.25" />
      <circle cx="64" cy="61" r="2.5" fill={ink} fillOpacity="0.25" />
    </>
  ),
  other: () => (
    <>
      <path
        d="M46 22c2.5 13 7 17.5 20 20-13 2.5-17.5 7-20 20-2.5-13-7-17.5-20-20 13-2.5 17.5-7 20-20z"
        fill={GLYPH}
      />
      <path
        d="M70 56c1.3 7 3.8 9.5 10.8 10.8-7 1.3-9.5 3.8-10.8 10.8-1.3-7-3.8-9.5-10.8-10.8 7-1.3 9.5-3.8 10.8-10.8z"
        fill={GLYPH}
        fillOpacity="0.85"
      />
      <circle cx="28" cy="72" r="4.5" fill={GLYPH} fillOpacity="0.7" />
      <circle cx="74" cy="27" r="3" fill={GLYPH} fillOpacity="0.6" />
    </>
  ),
  all: (ink) => (
    <>
      <rect x="23" y="23" width="24" height="24" rx="7" fill={GLYPH} />
      <rect x="53" y="23" width="24" height="24" rx="7" fill={GLYPH} fillOpacity="0.8" />
      <rect x="23" y="53" width="24" height="24" rx="7" fill={GLYPH} fillOpacity="0.8" />
      <rect x="53" y="53" width="24" height="24" rx="7" fill={GLYPH} />
      <path d="M31.5 29.5v11l9-5.5z" fill={ink} />
      <circle cx="65" cy="65" r="5.5" fill={ink} />
    </>
  ),
  insights: (ink) => (
    <>
      <rect x="24" y="56" width="12" height="20" rx="3.5" fill={GLYPH} fillOpacity="0.8" />
      <rect x="44" y="44" width="12" height="32" rx="3.5" fill={GLYPH} fillOpacity="0.9" />
      <rect x="64" y="30" width="12" height="46" rx="3.5" fill={GLYPH} />
      <path
        d="M26 46l18-12 12 6 18-16"
        stroke={GLYPH}
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      <circle cx="74" cy="24" r="5" fill={GLYPH} />
      <circle cx="74" cy="24" r="2.2" fill={ink} />
    </>
  ),
}
