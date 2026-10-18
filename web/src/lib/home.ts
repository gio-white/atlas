import type { ScreenDashboard, TaskItem, WeekDayCell, WeekHabit } from './api'

export type ScreenSplit = 'category' | 'device' | 'app'
export type ScreenRange = 'day' | 'week'

export type ScreenShareRow = { slug: string; name: string; minutes: number }

export function screenRows(
  dash: ScreenDashboard | null,
  split: ScreenSplit,
  range: ScreenRange,
): ScreenShareRow[] {
  if (dash === null) return []
  const items =
    split === 'category' ? dash.categories : split === 'device' ? dash.devices : dash.apps
  const divisor = range === 'week' ? elapsedDays(dash) : 1
  return items
    .map((item) => ({ slug: item.slug, name: item.name, minutes: item.minutes / divisor }))
    .filter((item) => item.minutes > 0)
}

export function screenHeadline(dash: ScreenDashboard | null, range: ScreenRange): number | null {
  if (dash === null) return null
  return range === 'week' ? dash.daily_average : dash.total
}

export function elapsedDays(dash: Pick<ScreenDashboard, 'range_start' | 'range_end'>): number {
  const start = Date.parse(`${dash.range_start}T00:00:00Z`)
  const end = Date.parse(`${dash.range_end}T00:00:00Z`)
  return Math.max(1, Math.round((end - start) / 86_400_000) + 1)
}

export function visibleTasks(tasks: TaskItem[], asOf: string): TaskItem[] {
  return tasks
    .filter((task) => task.done_at === null || localDate(task.done_at) === asOf)
    .sort((a, b) => Number(a.done_at !== null) - Number(b.done_at !== null))
}

function localDate(iso: string): string {
  const date = new Date(iso)
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${date.getFullYear()}-${month}-${day}`
}

export type HabitCellState = 'off' | 'future' | 'done' | 'missed' | 'open'

export function habitCellState(habit: WeekHabit, cell: WeekDayCell, asOf: string): HabitCellState {
  if (!cell.scheduled) return 'off'
  if (cell.day > asOf) return 'future'
  if (habit.period === 'day') {
    if (cell.satisfied === true) return 'done'
    return cell.day < asOf ? 'missed' : 'open'
  }
  return cell.value !== null && cell.value > 0 ? 'done' : 'open'
}

export function habitWeekSummary(habit: WeekHabit, asOf: string): string {
  if (habit.period === 'day') {
    const due = habit.days.filter((cell) => cell.scheduled && cell.day <= asOf)
    const done = due.filter((cell) => cell.satisfied === true).length
    return `${done}/${due.length} this week · streak ${habit.current_streak}`
  }
  const label = habit.period === 'week' ? 'this week' : 'this month'
  return `${habit.current_value ?? 0}/${habit.target_value} ${label}`
}
