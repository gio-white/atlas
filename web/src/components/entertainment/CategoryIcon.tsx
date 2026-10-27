import { type ReactNode, useId } from 'react'

import type { CategoryId } from '@/lib/entertainment'
import { cn } from '@/lib/utils'

export type IconId = CategoryId | 'insights'

type Palette = { from: string; to: string; ink: string }

/** Background gradient (top-left → bottom-right) and the accent used inside each glyph. */
const PALETTES: Record<IconId, Palette> = {
  all: { from: '#7c9cff', to: '#3d4ed8', ink: '#3346c4' },
  videos: { from: '#ff8a5c', to: '#e8304f', ink: '#d92d4c' },
  books: { from: '#ffd060', to: '#f2792c', ink: '#e0662a' },
  podcasts: { from: '#c07bff', to: '#6b3cf0', ink: '#6b3cf0' },
  music: { from: '#ff7aa8', to: '#e0245e', ink: '#e0245e' },
  other: { from: '#4fe3c8', to: '#0d8f8a', ink: '#0d8f8a' },
  insights: { from: '#5ee08f', to: '#1592c9', ink: '#1592c9' },
}

/** App-icon style tile: a rounded square with a gradient, soft gloss, and a white glyph. */
export function CategoryIcon({ id, className }: { id: IconId; className?: string }) {
  const uid = useId().replace(/:/g, '')
  const palette = PALETTES[id]
  const bg = `bg-${uid}`
  const gloss = `gloss-${uid}`
  const shadow = `shadow-${uid}`
  return (
    <svg
      viewBox="0 0 100 100"
      className={cn('block overflow-visible', className)}
      aria-hidden="true"
      focusable="false"
    >
      <defs>
        <linearGradient id={bg} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor={palette.from} />
          <stop offset="1" stopColor={palette.to} />
        </linearGradient>
        <linearGradient id={gloss} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#fff" stopOpacity="0.38" />
          <stop offset="0.5" stopColor="#fff" stopOpacity="0.06" />
          <stop offset="1" stopColor="#fff" stopOpacity="0" />
        </linearGradient>
        <filter id={shadow} x="-20%" y="-20%" width="140%" height="140%">
          <feDropShadow dx="0" dy="2" stdDeviation="2" floodColor="#000" floodOpacity="0.22" />
        </filter>
      </defs>
      <rect width="100" height="100" rx="23" fill={`url(#${bg})`} />
      <rect width="100" height="100" rx="23" fill={`url(#${gloss})`} />
      <rect
        x="0.5"
        y="0.5"
        width="99"
        height="99"
        rx="22.5"
        fill="none"
        stroke="#fff"
        strokeOpacity="0.22"
      />
      <g filter={`url(#${shadow})`}>{GLYPHS[id](palette.ink)}</g>
    </svg>
  )
}

const GLYPHS: Record<IconId, (ink: string) => ReactNode> = {
  videos: (ink) => (
    <>
      <g transform="rotate(-11 24 40)">
        <rect x="22" y="28" width="56" height="12" rx="4" fill="#fff" />
        <path d="M33 28h7l-6 12h-7zM49 28h7l-6 12h-7zM65 28h7l-6 12h-7z" fill={ink} />
      </g>
      <rect x="22" y="42" width="56" height="36" rx="7" fill="#fff" />
      <path d="M45 51.5v17.5l15-8.75z" fill={ink} />
    </>
  ),
  books: (ink) => (
    <>
      <path d="M50 33c-8-6-19-7-29-5v43c10-2 21-1 29 5z" fill="#fff" />
      <path d="M50 33c8-6 19-7 29-5v43c-10-2-21-1-29 5z" fill="#fff" fillOpacity="0.86" />
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
        stroke="#fff"
        strokeOpacity="0.55"
        strokeWidth="4"
        strokeLinecap="round"
        fill="none"
      />
      <rect x="40" y="20" width="20" height="36" rx="10" fill="#fff" />
      <path
        d="M44 31h12M44 37h12M44 43h12"
        stroke={ink}
        strokeOpacity="0.35"
        strokeWidth="2.2"
        strokeLinecap="round"
      />
      <path
        d="M33 50a17 17 0 0 0 34 0M50 67v9M41 78h18"
        stroke="#fff"
        strokeWidth="4.5"
        strokeLinecap="round"
        fill="none"
      />
    </>
  ),
  music: (ink) => (
    <>
      <path d="M41 30l34-8v8l-34 8z" fill="#fff" />
      <rect x="39" y="30" width="5" height="40" rx="2.5" fill="#fff" />
      <rect x="72" y="22" width="5" height="40" rx="2.5" fill="#fff" />
      <ellipse cx="34" cy="71" rx="10" ry="8" transform="rotate(-18 34 71)" fill="#fff" />
      <ellipse cx="67" cy="63" rx="10" ry="8" transform="rotate(-18 67 63)" fill="#fff" />
      <circle cx="31" cy="69" r="2.5" fill={ink} fillOpacity="0.25" />
      <circle cx="64" cy="61" r="2.5" fill={ink} fillOpacity="0.25" />
    </>
  ),
  other: () => (
    <>
      <path
        d="M46 22c2.5 13 7 17.5 20 20-13 2.5-17.5 7-20 20-2.5-13-7-17.5-20-20 13-2.5 17.5-7 20-20z"
        fill="#fff"
      />
      <path
        d="M70 56c1.3 7 3.8 9.5 10.8 10.8-7 1.3-9.5 3.8-10.8 10.8-1.3-7-3.8-9.5-10.8-10.8 7-1.3 9.5-3.8 10.8-10.8z"
        fill="#fff"
        fillOpacity="0.85"
      />
      <circle cx="28" cy="72" r="4.5" fill="#fff" fillOpacity="0.7" />
      <circle cx="74" cy="27" r="3" fill="#fff" fillOpacity="0.6" />
    </>
  ),
  all: (ink) => (
    <>
      <rect x="23" y="23" width="24" height="24" rx="7" fill="#fff" />
      <rect x="53" y="23" width="24" height="24" rx="7" fill="#fff" fillOpacity="0.8" />
      <rect x="23" y="53" width="24" height="24" rx="7" fill="#fff" fillOpacity="0.8" />
      <rect x="53" y="53" width="24" height="24" rx="7" fill="#fff" />
      <path d="M31.5 29.5v11l9-5.5z" fill={ink} />
      <circle cx="65" cy="65" r="5.5" fill={ink} />
    </>
  ),
  insights: (ink) => (
    <>
      <rect x="24" y="56" width="12" height="20" rx="3.5" fill="#fff" fillOpacity="0.8" />
      <rect x="44" y="44" width="12" height="32" rx="3.5" fill="#fff" fillOpacity="0.9" />
      <rect x="64" y="30" width="12" height="46" rx="3.5" fill="#fff" />
      <path
        d="M26 46l18-12 12 6 18-16"
        stroke="#fff"
        strokeWidth="4"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      <circle cx="74" cy="24" r="5" fill="#fff" />
      <circle cx="74" cy="24" r="2.2" fill={ink} />
    </>
  ),
}
