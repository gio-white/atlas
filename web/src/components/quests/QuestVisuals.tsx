import {
  Bookmark,
  ChevronRight,
  Circle,
  CircleCheck,
  CircleDot,
  Compass,
  Diamond,
  Flag,
  type LucideIcon,
  Scroll,
} from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

import type { ItemRef, QuestKind, QuestStatus } from '@/lib/api'
import { itemHref, KIND_LABELS, NOT_BROKEN_DOWN, progressLabel } from '@/lib/quests'
import { cn } from '@/lib/utils'

// The quest accent is the theme's iris; every other surface stays neutral.

/** Levels are told apart by icon and shape (plan §6 visual direction). */
export const LEVEL_ICONS: Record<QuestKind, LucideIcon> = {
  ambition: Compass,
  goal: Flag,
  milestone: Diamond,
  chapter: Bookmark,
  side_quest: Scroll,
  task: Circle,
}

export function LevelIcon({
  kind,
  className,
  label = false,
}: {
  kind: QuestKind
  className?: string
  /** Announce the level to screen readers (when the icon is the only level cue). */
  label?: boolean
}) {
  const Icon = LEVEL_ICONS[kind]
  return (
    <Icon
      className={cn('size-4 shrink-0 text-iris', className)}
      aria-hidden={!label}
      aria-label={label ? KIND_LABELS[kind] : undefined}
      role={label ? 'img' : undefined}
    />
  )
}

/** Progress ring for cards. A null value is drawn as a dashed ring: nothing to measure yet. */
export function QuestRing({
  value,
  completed = false,
  size = 56,
}: {
  value: number | null
  completed?: boolean
  size?: number
}) {
  const radius = 20
  const circumference = 2 * Math.PI * radius
  const fraction = value === null ? 0 : Math.min(1, Math.max(0, value))
  const label = value === null ? NOT_BROKEN_DOWN : `${progressLabel(value)} done`
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <svg
        viewBox="0 0 48 48"
        width={size}
        height={size}
        className="-rotate-90"
        role="img"
        aria-label={label}
      >
        <circle
          cx="24"
          cy="24"
          r={radius}
          fill="none"
          strokeWidth="4"
          className="stroke-raised"
          strokeDasharray={value === null ? '3 4' : undefined}
        />
        {value !== null && (
          <circle
            cx="24"
            cy="24"
            r={radius}
            fill="none"
            strokeWidth="4"
            strokeLinecap="round"
            strokeDasharray={circumference}
            strokeDashoffset={circumference * (1 - fraction)}
            className={cn(
              'motion-safe:transition-[stroke-dashoffset] motion-safe:duration-300',
              completed ? 'stroke-good' : 'stroke-iris',
            )}
          />
        )}
      </svg>
      <span
        className="absolute inset-0 flex items-center justify-center text-xs font-semibold tabular-nums text-ink"
        aria-hidden
      >
        {value === null ? '—' : progressLabel(value)}
      </span>
    </div>
  )
}

/** Thin progress bar for rows. */
export function QuestBar({
  value,
  completed = false,
  className,
}: {
  value: number | null
  completed?: boolean
  className?: string
}) {
  const pct = value === null ? 0 : Math.round(Math.min(1, Math.max(0, value)) * 100)
  return (
    <div
      className={cn('h-1 overflow-hidden rounded-full bg-raised', className)}
      role="progressbar"
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={value === null ? undefined : pct}
      aria-valuetext={progressLabel(value)}
    >
      <div
        className={cn(
          'h-full rounded-full motion-safe:transition-[width] motion-safe:duration-300',
          completed ? 'bg-good' : 'bg-iris',
        )}
        style={{ width: `${pct}%` }}
      />
    </div>
  )
}

/** Status chip for containers, with the override note when completed with open items. */
export function StatusChip({
  status,
  openItems = false,
}: {
  status: QuestStatus
  openItems?: boolean
}) {
  if (status === 'archived') return <Chip tone="muted">Archived</Chip>
  if (status === 'completed') {
    return (
      <Chip tone="good">
        <CircleCheck className="size-3" aria-hidden />
        {openItems ? 'Completed with open items' : 'Completed'}
      </Chip>
    )
  }
  return (
    <Chip tone="iris">
      <CircleDot className="size-3" aria-hidden />
      Active
    </Chip>
  )
}

export function Chip({
  tone = 'muted',
  children,
  className,
}: {
  tone?: 'muted' | 'iris' | 'good' | 'warn'
  children: ReactNode
  className?: string
}) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium whitespace-nowrap',
        tone === 'muted' && 'bg-raised text-muted',
        tone === 'iris' && 'bg-iris/12 text-iris',
        tone === 'good' && 'bg-good/12 text-good',
        tone === 'warn' && 'bg-warn/15 text-warn',
        className,
      )}
    >
      {children}
    </span>
  )
}

/** Ancestor trail: "Main quests › Ambition › Goal". Each step links to its page. */
export function QuestBreadcrumb({
  root,
  path,
  current,
}: {
  root: { label: string; to: string }
  path: ItemRef[]
  current: string
}) {
  return (
    <nav aria-label="Breadcrumb" className="text-sm text-muted">
      <ol className="flex flex-wrap items-center gap-1">
        <li>
          <Link to={root.to} className="hover:text-ink">
            {root.label}
          </Link>
        </li>
        {path.map((ref, index) => {
          const href = itemHref(ref, path.slice(0, index))
          return (
            <li key={`${ref.kind}-${ref.id}`} className="inline-flex items-center gap-1">
              <ChevronRight className="size-3.5" aria-hidden />
              <LevelIcon kind={ref.kind} className="size-3.5" />
              {href === null ? (
                ref.title
              ) : (
                <Link to={href} className="hover:text-ink">
                  {ref.title}
                </Link>
              )}
            </li>
          )
        })}
        <li aria-current="page" className="inline-flex items-center gap-1 font-medium text-ink">
          <ChevronRight className="size-3.5 text-muted" aria-hidden />
          {current}
        </li>
      </ol>
    </nav>
  )
}
