// Display helpers for the quest screens (docs/domain/quests.md#screens).
// Nothing here computes progress, eligibility, chapter state, or next action: the API returns
// those. These helpers only label, link, order, and search what the API sent.

import type {
  ChapterState,
  GoalTree,
  ItemRef,
  MainQuests,
  ParentKind,
  PromoteKind,
  QuestKind,
  SideQuestTree,
  TaskPriority,
  TaskStatus,
} from './api'
import { parseIsoDate } from './dates'
import { formatMinutes } from './format'

export const KIND_LABELS: Record<QuestKind, string> = {
  ambition: 'Ambition',
  goal: 'Goal',
  milestone: 'Milestone',
  chapter: 'Chapter',
  side_quest: 'Side quest',
  task: 'Task',
}

export const TASK_STATUS_LABELS: Record<TaskStatus, string> = {
  todo: 'To do',
  in_progress: 'In progress',
  completed: 'Done',
}

export const PRIORITY_LABELS: Record<TaskPriority, string> = {
  low: 'Low',
  normal: 'Normal',
  high: 'High',
}

export const CHAPTER_STATE_LABELS: Record<ChapterState, string> = {
  empty: 'Empty',
  not_started: 'Not started',
  in_progress: 'In progress',
  completed: 'Completed',
}

export const NOT_BROKEN_DOWN = 'Not broken down yet'

/** "42%" for a 0–1 progress value; the plain "Not broken down yet" when the API sent null. */
export function progressLabel(progress: number | null): string {
  if (progress === null) return NOT_BROKEN_DOWN
  return `${Math.round(clamp01(progress) * 100)}%`
}

/** "35%" for a normalized weight share, or null when there is nothing to show. */
export function shareLabel(share: number | null): string | null {
  if (share === null) return null
  return `${Math.round(clamp01(share) * 100)}%`
}

function clamp01(value: number): number {
  return Math.min(1, Math.max(0, value))
}

/** Dates read as "7 Nov 2026" (docs/product/ux-writing.md). */
export function questDateLabel(isoDate: string): string {
  return parseIsoDate(isoDate.slice(0, 10)).toLocaleDateString('en-GB', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

export function estimateLabel(minutes: number | null): string | null {
  if (minutes === null) return null
  return formatMinutes(minutes)
}

/** "2 milestones", "1 task", "No tasks". */
export function countLabel(count: number, singular: string, plural = `${singular}s`): string {
  if (count === 0) return `No ${plural}`
  return `${count} ${count === 1 ? singular : plural}`
}

/** "3 of 7 tasks done", or null when there are no tasks under the item. */
export function doneTasksLabel(done: number, total: number): string | null {
  if (total === 0) return null
  return `${done} of ${total} ${total === 1 ? 'task' : 'tasks'} done`
}

/** Ancestor titles joined for a context line: "Become a better engineer › Move to Copenhagen". */
export function pathLabel(path: ItemRef[]): string {
  return path.map((ref) => ref.title).join(' › ')
}

/**
 * The screen that shows an item. Goals, ambitions, and side quests have their own pages;
 * milestones and chapters live on the nearest goal or side quest page, so the ancestor path
 * decides. Returns null when nothing navigable is known (an Inbox task).
 */
export function itemHref(item: ItemRef, path: ItemRef[] = []): string | null {
  const direct = pageHref(item)
  if (direct !== null) return direct
  for (const ancestor of [...path].reverse()) {
    const href = pageHref(ancestor)
    if (href !== null) return href
  }
  return null
}

function pageHref(ref: ItemRef): string | null {
  if (ref.kind === 'goal') return `/quests/goals/${ref.id}`
  if (ref.kind === 'ambition') return `/quests/ambitions/${ref.id}`
  if (ref.kind === 'side_quest') return `/quests/side-quests/${ref.id}`
  return null
}

/** Where a task's parent lives on screen, or null for Inbox and standalone tasks. */
export function taskContextHref(task: { parent: ItemRef | null; path: ItemRef[] }): string | null {
  if (task.parent === null) return null
  return itemHref(task.parent, task.path.slice(0, -1))
}

export type Positioned = { id: number; position: number }

/**
 * Move the item at `index` one step up (-1) or down (+1) and return the position updates to
 * send, one PATCH per changed item. Siblings are renumbered 0…n-1 in the new order, so ties
 * and gaps in stored positions cannot make a move a no-op (plan D16).
 */
export function reorder(items: Positioned[], index: number, direction: -1 | 1): Positioned[] {
  const target = index + direction
  if (index < 0 || index >= items.length || target < 0 || target >= items.length) return []
  const next = [...items]
  ;[next[index], next[target]] = [next[target], next[index]]
  return next
    .map((item, position) => ({ id: item.id, position, changed: item.position !== position }))
    .filter((item) => item.changed)
    .map(({ id, position }) => ({ id, position }))
}

// --- Organize / promote targets -------------------------------------------------------------

export type QuestTarget = {
  kind: ParentKind
  id: number
  title: string
  /** Ancestor titles for display ("Ambition › Goal"), empty at the top level. */
  context: string
}

/**
 * Every place a task can go, in tree order: ambitions, their goals, each goal's milestones and
 * chapters, independent goals, then side quests and their chapters. Built from the read models
 * the screens already use (archived items are not in them). Completed items still accept tasks.
 */
export function collectTargets(
  main: MainQuests,
  goalTrees: GoalTree[],
  sideQuestTrees: SideQuestTree[],
): QuestTarget[] {
  const trees = new Map(goalTrees.map((tree) => [tree.goal.id, tree]))
  const targets: QuestTarget[] = []

  function addGoal(goal: { id: number; title: string }, context: string[]) {
    targets.push({ kind: 'goal', id: goal.id, title: goal.title, context: context.join(' › ') })
    const tree = trees.get(goal.id)
    if (tree === undefined) return
    const goalContext = [...context, goal.title]
    for (const { milestone, chapters } of tree.milestones) {
      targets.push({
        kind: 'milestone',
        id: milestone.id,
        title: milestone.title,
        context: goalContext.join(' › '),
      })
      for (const { chapter } of chapters) {
        targets.push({
          kind: 'chapter',
          id: chapter.id,
          title: chapter.title,
          context: [...goalContext, milestone.title].join(' › '),
        })
      }
    }
  }

  for (const section of main.ambitions) {
    const { ambition } = section
    targets.push({ kind: 'ambition', id: ambition.id, title: ambition.title, context: '' })
    for (const goal of section.goals) addGoal(goal, [ambition.title])
  }
  for (const goal of main.independent_goals) addGoal(goal, [])
  for (const tree of sideQuestTrees) {
    const { side_quest: quest } = tree
    targets.push({ kind: 'side_quest', id: quest.id, title: quest.title, context: '' })
    for (const { chapter } of tree.chapters) {
      targets.push({ kind: 'chapter', id: chapter.id, title: chapter.title, context: quest.title })
    }
  }
  return targets
}

/**
 * Search-as-you-type over targets: every word of the query must appear in the title, the
 * context, or the level name, ignoring case. An empty query keeps everything.
 */
export function searchTargets(
  targets: QuestTarget[],
  query: string,
  kinds?: readonly ParentKind[],
): QuestTarget[] {
  const words = query.toLowerCase().split(/\s+/).filter(Boolean)
  return targets.filter((target) => {
    if (kinds !== undefined && !kinds.includes(target.kind)) return false
    const haystack =
      `${target.title} ${target.context} ${KIND_LABELS[target.kind]}`.toLocaleLowerCase()
    return words.every((word) => haystack.includes(word))
  })
}

/** What a promoted Inbox task needs as its parent (plan §5 promote rule). */
export const PROMOTE_PARENTS: Record<
  PromoteKind,
  { kinds: readonly ParentKind[]; required: boolean }
> = {
  ambition: { kinds: [], required: false },
  goal: { kinds: ['ambition'], required: false },
  side_quest: { kinds: [], required: false },
  milestone: { kinds: ['goal'], required: true },
  chapter: { kinds: ['milestone', 'side_quest'], required: true },
}

export const PROMOTE_KINDS: readonly PromoteKind[] = [
  'ambition',
  'goal',
  'side_quest',
  'milestone',
  'chapter',
]

// --- Inbox count ----------------------------------------------------------------------------

/** Window event the sidebar listens to so its Inbox count follows changes made on a page. */
export const INBOX_CHANGED_EVENT = 'atlas:inbox-changed'

export function notifyInboxChanged(): void {
  if (typeof window !== 'undefined') window.dispatchEvent(new Event(INBOX_CHANGED_EVENT))
}
