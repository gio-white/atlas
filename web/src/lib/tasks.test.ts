import { describe, expect, it } from 'vitest'

import type { Goal, TaskItem } from './api'
import {
  activeGoals,
  filterTasks,
  goalNameBySlug,
  groupTasksByBucket,
  resolveGoalName,
  withGoalParam,
} from './tasks'

function task(overrides: Partial<TaskItem> & Pick<TaskItem, 'id' | 'title' | 'bucket'>): TaskItem {
  return {
    due_on: null,
    due_at: null,
    priority: 'normal',
    goal: null,
    done_at: null,
    created_at: '2026-08-14T12:00:00+00:00',
    ...overrides,
  }
}

function goal(overrides: Partial<Goal> & Pick<Goal, 'slug' | 'name'>): Goal {
  return {
    id: 1,
    area: null,
    kind: 'milestone',
    metric: null,
    target_value: null,
    comparator: null,
    baseline_value: null,
    measure: null,
    start_on: '2026-08-01',
    due_on: '2026-08-31',
    horizon: 'short',
    parent: null,
    description: null,
    status: 'active',
    achieved_at: null,
    ...overrides,
  }
}

describe('filterTasks', () => {
  const rows = [
    task({ id: 1, title: 'Open today', bucket: 'today', goal: 'workout' }),
    task({
      id: 2,
      title: 'Done today',
      bucket: 'today',
      goal: 'workout',
      done_at: '2026-08-14T12:00:00+00:00',
    }),
    task({ id: 3, title: 'Other goal', bucket: 'upcoming', goal: 'read' }),
    task({ id: 4, title: 'Unlinked', bucket: 'someday' }),
  ]

  it('hides completed tasks by default', () => {
    expect(filterTasks(rows).map((item) => item.id)).toEqual([1, 3, 4])
  })

  it('can include completed tasks', () => {
    expect(filterTasks(rows, { includeDone: true }).map((item) => item.id)).toEqual([1, 2, 3, 4])
  })

  it('filters by goal slug', () => {
    expect(filterTasks(rows, { goal: 'workout' }).map((item) => item.title)).toEqual(['Open today'])
    expect(
      filterTasks(rows, { goal: 'workout', includeDone: true }).map((item) => item.title),
    ).toEqual(['Open today', 'Done today'])
  })
})

describe('groupTasksByBucket', () => {
  it('groups into today, upcoming, and someday', () => {
    const grouped = groupTasksByBucket([
      task({ id: 1, title: 'A', bucket: 'someday' }),
      task({ id: 2, title: 'B', bucket: 'today' }),
      task({ id: 3, title: 'C', bucket: 'upcoming' }),
      task({ id: 4, title: 'D', bucket: 'today' }),
    ])
    expect(grouped.today.map((item) => item.title)).toEqual(['B', 'D'])
    expect(grouped.upcoming.map((item) => item.title)).toEqual(['C'])
    expect(grouped.someday.map((item) => item.title)).toEqual(['A'])
  })
})

describe('resolveGoalName', () => {
  it('looks up the display name and falls back to the slug', () => {
    const names = goalNameBySlug([
      goal({ slug: 'workout-week', name: 'Workout this week' }),
      goal({ slug: 'read-12', name: 'Read 12 books' }),
    ])
    expect(resolveGoalName('workout-week', names)).toBe('Workout this week')
    expect(resolveGoalName('missing', names)).toBe('missing')
    expect(resolveGoalName(null, names)).toBeNull()
  })
})

describe('activeGoals', () => {
  it('keeps only active goals', () => {
    const rows = [
      goal({ slug: 'a', name: 'A', status: 'active' }),
      goal({ slug: 'b', name: 'B', status: 'paused' }),
      goal({ slug: 'c', name: 'C', status: 'achieved' }),
    ]
    expect(activeGoals(rows).map((item) => item.slug)).toEqual(['a'])
  })
})

describe('withGoalParam', () => {
  it('sets, replaces, and clears the goal query param', () => {
    expect(withGoalParam('on=2026-08-14', 'workout')).toBe('on=2026-08-14&goal=workout')
    expect(withGoalParam('?on=2026-08-14&goal=old', 'workout')).toBe('on=2026-08-14&goal=workout')
    expect(withGoalParam('on=2026-08-14&goal=workout', null)).toBe('on=2026-08-14')
  })
})
