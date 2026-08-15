import type { Goal, TaskBucket, TaskItem } from './api'

export const TASK_BUCKETS: TaskBucket[] = ['today', 'upcoming', 'someday']

export const TASK_BUCKET_META: Record<TaskBucket, { label: string; kicker: string }> = {
  today: { label: 'Today', kicker: 'What you will do now.' },
  upcoming: { label: 'Upcoming', kicker: 'Queued for the next few days.' },
  someday: { label: 'Someday', kicker: 'Parked until you are ready.' },
}

export function filterTasks(
  tasks: TaskItem[],
  options: { goal?: string | null; includeDone?: boolean } = {},
): TaskItem[] {
  const goal = options.goal ?? null
  const includeDone = options.includeDone ?? false
  return tasks.filter((task) => {
    if (!includeDone && task.done_at !== null) return false
    if (goal !== null && task.goal !== goal) return false
    return true
  })
}

export function groupTasksByBucket(tasks: TaskItem[]): Record<TaskBucket, TaskItem[]> {
  const grouped: Record<TaskBucket, TaskItem[]> = { today: [], upcoming: [], someday: [] }
  for (const task of tasks) {
    grouped[task.bucket].push(task)
  }
  return grouped
}

export function goalNameBySlug(goals: Pick<Goal, 'slug' | 'name'>[]): Map<string, string> {
  return new Map(goals.map((goal) => [goal.slug, goal.name]))
}

export function resolveGoalName(slug: string | null, names: Map<string, string>): string | null {
  if (slug === null) return null
  return names.get(slug) ?? slug
}

export function activeGoals<T extends Pick<Goal, 'status'>>(goals: T[]): T[] {
  return goals.filter((goal) => goal.status === 'active')
}

export function withGoalParam(search: string, goal: string | null): string {
  const params = new URLSearchParams(search.startsWith('?') ? search.slice(1) : search)
  if (goal === null || goal === '') params.delete('goal')
  else params.set('goal', goal)
  return params.toString()
}
