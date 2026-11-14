import { Search } from 'lucide-react'
import { type KeyboardEvent, useEffect, useId, useMemo, useState } from 'react'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import {
  getGoalTree,
  getMainQuests,
  getSideQuestsView,
  getSideQuestTree,
  type ItemRef,
  type ParentKind,
} from '@/lib/api'
import { collectTargets, KIND_LABELS, type QuestTarget, searchTargets } from '@/lib/quests'
import { cn } from '@/lib/utils'

import { LevelIcon } from './QuestVisuals'
import { errorMessage } from './useQuestView'

/** Every place a task can go, read from the same views the screens use. */
export async function loadQuestTargets(): Promise<QuestTarget[]> {
  const [main, side] = await Promise.all([getMainQuests(), getSideQuestsView()])
  const goalIds = [
    ...main.ambitions.flatMap((section) => section.goals.map((goal) => goal.id)),
    ...main.independent_goals.map((goal) => goal.id),
  ]
  const [goalTrees, sideTrees] = await Promise.all([
    Promise.all(goalIds.map((id) => getGoalTree(id))),
    Promise.all(side.side_quests.map((quest) => getSideQuestTree(quest.id))),
  ])
  return collectTargets(main, goalTrees, sideTrees)
}

export function OrganizePicker({
  open,
  onOpenChange,
  title,
  description,
  kinds,
  current,
  onPick,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  description?: string
  /** Limit the picker to these levels (promote needs a goal, a milestone, …). */
  kinds?: readonly ParentKind[]
  /** The task's current parent, marked in the list. */
  current?: ItemRef | null
  onPick: (target: QuestTarget) => Promise<void> | void
}) {
  const [targets, setTargets] = useState<QuestTarget[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)
  const [busy, setBusy] = useState(false)
  const hintId = useId()

  useEffect(() => {
    if (!open) return
    let cancelled = false
    setQuery('')
    setActive(0)
    setError(null)
    loadQuestTargets()
      .then((next) => {
        if (!cancelled) setTargets(next)
      })
      .catch((caught: unknown) => {
        if (!cancelled) setError(errorMessage(caught, "Couldn't load your quests."))
      })
    return () => {
      cancelled = true
    }
  }, [open])

  const matches = useMemo(
    () => (targets === null ? [] : searchTargets(targets, query, kinds)),
    [targets, query, kinds],
  )

  async function pick(target: QuestTarget | undefined) {
    if (target === undefined || busy) return
    if (current?.kind === target.kind && current.id === target.id) return
    setBusy(true)
    try {
      await onPick(target)
    } finally {
      setBusy(false)
    }
  }

  function onKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setActive((index) => Math.min(matches.length - 1, index + 1))
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActive((index) => Math.max(0, index - 1))
    } else if (event.key === 'Enter') {
      event.preventDefault()
      void pick(matches[active])
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>
            {description ?? 'Search your ambitions, goals, milestones, chapters, and side quests.'}
          </DialogDescription>
        </DialogHeader>
        <div className="relative">
          <Search
            className="pointer-events-none absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted"
            aria-hidden
          />
          <Input
            autoFocus
            type="search"
            aria-label="Search quests"
            aria-describedby={hintId}
            placeholder="Type to search"
            className="h-11 pl-9"
            value={query}
            onChange={(event) => {
              setQuery(event.target.value)
              setActive(0)
            }}
            onKeyDown={onKeyDown}
          />
          <span id={hintId} className="sr-only">
            Use the arrow keys to choose and Enter to pick.
          </span>
        </div>
        {error !== null && (
          <p role="alert" className="text-sm text-bad">
            {error}
          </p>
        )}
        {targets === null && error === null && (
          <p role="status" className="text-sm text-muted">
            Loading your quests…
          </p>
        )}
        {targets !== null && (
          <ul
            aria-label="Places"
            className="-mx-1 flex max-h-[55svh] flex-col gap-0.5 overflow-y-auto px-1"
          >
            {matches.length === 0 && (
              <li className="px-3 py-6 text-center text-sm text-muted">
                {targets.length === 0
                  ? 'Nothing to organize into yet. Create a goal or side quest first.'
                  : 'No matches. Try another word.'}
              </li>
            )}
            {matches.map((target, index) => {
              const isCurrent = current?.kind === target.kind && current.id === target.id
              return (
                <li key={`${target.kind}-${target.id}`}>
                  <button
                    type="button"
                    disabled={busy || isCurrent}
                    data-active={index === active || undefined}
                    className={cn(
                      'flex min-h-11 w-full items-center gap-3 rounded-lg px-3 py-2 text-left',
                      index === active ? 'bg-accent/10' : 'hover:bg-raised',
                      isCurrent && 'cursor-default opacity-60',
                    )}
                    onMouseEnter={() => setActive(index)}
                    onClick={() => void pick(target)}
                  >
                    <LevelIcon kind={target.kind} />
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm font-medium text-ink">
                        {target.title}
                      </span>
                      <span className="block truncate text-xs text-muted">
                        {KIND_LABELS[target.kind]}
                        {target.context !== '' && ` · ${target.context}`}
                      </span>
                    </span>
                    {isCurrent && <span className="text-xs text-muted">Here now</span>}
                  </button>
                </li>
              )
            })}
          </ul>
        )}
      </DialogContent>
    </Dialog>
  )
}
