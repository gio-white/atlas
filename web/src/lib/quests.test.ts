import { describe, expect, it } from 'vitest'

import { chapter, milestone, sideQuest, task } from '@/components/quests/testFixtures'

import type { Ambition, GoalTree, MainQuests, QuestGoal } from './api'
import {
  collectTargets,
  countLabel,
  doneTasksLabel,
  itemHref,
  progressLabel,
  questDateLabel,
  reorder,
  searchTargets,
  shareLabel,
  taskContextHref,
} from './quests'

describe('labels', () => {
  it('shows "Not broken down yet" for null progress and rounds percentages', () => {
    expect(progressLabel(null)).toBe('Not broken down yet')
    expect(progressLabel(0.18888)).toBe('19%')
    expect(progressLabel(1)).toBe('100%')
  })

  it('formats weight shares, dates, and counts in plain words', () => {
    expect(shareLabel(null)).toBeNull()
    expect(shareLabel(1 / 3)).toBe('33%')
    expect(questDateLabel('2026-11-07')).toBe('7 Nov 2026')
    expect(questDateLabel('2026-10-25T09:00:00Z')).toBe('25 Oct 2026')
    expect(countLabel(0, 'milestone')).toBe('No milestones')
    expect(countLabel(1, 'milestone')).toBe('1 milestone')
    expect(countLabel(3, 'milestone')).toBe('3 milestones')
    expect(doneTasksLabel(0, 0)).toBeNull()
    expect(doneTasksLabel(2, 7)).toBe('2 of 7 tasks done')
    expect(doneTasksLabel(1, 1)).toBe('1 of 1 task done')
  })
})

describe('links', () => {
  it('links pages directly and milestones and chapters to the nearest page above them', () => {
    expect(itemHref({ kind: 'goal', id: 4, title: 'G' })).toBe('/quests/goals/4')
    expect(itemHref({ kind: 'ambition', id: 2, title: 'A' })).toBe('/quests/ambitions/2')
    expect(itemHref({ kind: 'side_quest', id: 3, title: 'S' })).toBe('/quests/side-quests/3')
    expect(
      itemHref({ kind: 'chapter', id: 9, title: 'C' }, [
        { kind: 'ambition', id: 1, title: 'A' },
        { kind: 'goal', id: 5, title: 'G' },
        { kind: 'milestone', id: 7, title: 'M' },
      ]),
    ).toBe('/quests/goals/5')
    expect(itemHref({ kind: 'milestone', id: 7, title: 'M' })).toBeNull()
  })

  it('finds where a task lives, or nothing for Inbox tasks', () => {
    expect(taskContextHref(task(1, 'Inbox thing'))).toBeNull()
    const path = [
      { kind: 'side_quest' as const, id: 2, title: 'Taxes' },
      { kind: 'chapter' as const, id: 8, title: 'Collect' },
    ]
    expect(taskContextHref(task(1, 'Receipts', { parent: path[1], path }))).toBe(
      '/quests/side-quests/2',
    )
  })
})

describe('reorder', () => {
  it('swaps neighbours and renumbers only what changed', () => {
    const items = [
      { id: 10, position: 0 },
      { id: 11, position: 1 },
      { id: 12, position: 2 },
    ]
    expect(reorder(items, 2, -1)).toEqual([
      { id: 12, position: 1 },
      { id: 11, position: 2 },
    ])
    expect(reorder(items, 0, -1)).toEqual([])
    expect(reorder(items, 2, 1)).toEqual([])
  })

  it('still moves an item when stored positions tie', () => {
    const items = [
      { id: 1, position: 0 },
      { id: 2, position: 0 },
    ]
    expect(reorder(items, 1, -1)).toEqual([{ id: 1, position: 1 }])
  })
})

describe('organize targets', () => {
  const ambition = { id: 1, title: 'Grow as an engineer' } as Ambition
  const goal = { id: 5, title: 'Move to Copenhagen' } as QuestGoal
  const solo = { id: 6, title: 'Run a half marathon' } as QuestGoal
  const main: MainQuests = {
    ambitions: [{ ambition, goals: [goal], tasks: [] }],
    independent_goals: [solo],
  }
  const goalTree: GoalTree = {
    goal,
    milestones: [
      {
        milestone: milestone(7, 'Learn Rust'),
        chapters: [{ chapter: chapter(9, 'Async'), tasks: [] }],
        tasks: [],
      },
    ],
    tasks: [],
  }
  const sideTree = {
    side_quest: sideQuest(3, 'Tax declaration'),
    chapters: [{ chapter: chapter(4, 'Collect documents'), tasks: [] }],
    tasks: [],
  }
  const targets = collectTargets(main, [goalTree], [sideTree])

  it('lists every level in tree order with its context', () => {
    expect(targets.map((t) => `${t.kind}:${t.title}:${t.context}`)).toEqual([
      'ambition:Grow as an engineer:',
      'goal:Move to Copenhagen:Grow as an engineer',
      'milestone:Learn Rust:Grow as an engineer › Move to Copenhagen',
      'chapter:Async:Grow as an engineer › Move to Copenhagen › Learn Rust',
      'goal:Run a half marathon:',
      'side_quest:Tax declaration:',
      'chapter:Collect documents:Tax declaration',
    ])
  })

  it('matches every word against title, context, and level, ignoring case', () => {
    expect(searchTargets(targets, 'rust').map((t) => t.id)).toEqual([7, 9])
    expect(searchTargets(targets, 'copenhagen async').map((t) => t.id)).toEqual([9])
    expect(searchTargets(targets, 'CHAPTER tax').map((t) => t.id)).toEqual([4])
    expect(searchTargets(targets, '')).toHaveLength(targets.length)
    expect(searchTargets(targets, '', ['goal']).map((t) => t.id)).toEqual([5, 6])
  })
})
