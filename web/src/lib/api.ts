export type ValueType = 'bool' | 'count' | 'quantity' | 'duration' | 'rating' | 'text'
export type Aggregation = 'sum' | 'last' | 'mean' | 'max' | 'min'
export type Direction = 'higher_is_better' | 'lower_is_better' | 'neutral'
export type Period = 'day' | 'week' | 'month'
export type Comparator = 'at_least' | 'at_most' | 'exactly'
export type GoalKind = 'metric_target' | 'milestone'
export type GoalStatus = 'active' | 'achieved' | 'paused' | 'abandoned'
export type PaceStatus = 'achieved' | 'overdue' | 'no_data' | 'ahead' | 'on_track' | 'behind'
export type Source = 'cli' | 'api' | 'import'

export type Area = {
  id: number
  slug: string
  name: string
  description: string | null
  archived_at: string | null
}

export type Metric = {
  id: number
  slug: string
  area: string
  name: string
  value_type: ValueType
  unit: string | null
  aggregation: Aggregation
  direction: Direction
  archived_at: string | null
}

export type Entry = {
  id: number
  metric: string
  occurred_on: string
  occurred_at: string | null
  value_num: number | null
  value_bool: boolean | null
  value_text: string | null
  note: string | null
  source: Source
  created_at: string
}

export type Habit = {
  id: number
  slug: string
  metric: string
  name: string
  period: Period
  target_value: number
  comparator: Comparator
  weekdays: number[] | null
  active_from: string
  active_to: string | null
}

export type Goal = {
  id: number
  slug: string
  area: string
  name: string
  kind: GoalKind
  metric: string | null
  target_value: number | null
  comparator: Comparator | null
  baseline_value: number | null
  measure: 'latest_value' | 'cumulative_since_start' | null
  start_on: string
  due_on: string
  status: GoalStatus
  achieved_at: string | null
}

export type HabitStatus = {
  slug: string
  name: string
  metric_slug: string
  period: Period
  target_value: number
  comparator: Comparator
  current_streak: number
  longest_streak: number
  adherence: number | null
  current_value: number | null
  satisfied: boolean
  scheduled: boolean
  as_of: string
}

export type GoalProgress = {
  slug: string
  name: string
  kind: GoalKind
  status: GoalStatus
  metric_slug: string | null
  current: number | null
  baseline: number | null
  fraction: number | null
  target_met: boolean
  pace: PaceStatus
  target_value: number | null
  start_on: string
  due_on: string
  as_of: string
}

export type LoggedEntry = {
  id: number
  metric_slug: string
  occurred_on: string
  value_num: number | null
  value_bool: boolean | null
  value_text: string | null
  note: string | null
}

export type TodayView = {
  as_of: string
  habits: HabitStatus[]
  entries: LoggedEntry[]
  goals: GoalProgress[]
}

export type WeekDayCell = {
  day: string
  scheduled: boolean
  value: number | null
  satisfied: boolean | null
}

export type WeekHabit = {
  slug: string
  name: string
  metric_slug: string
  period: Period
  target_value: number
  comparator: Comparator
  current_value: number | null
  satisfied: boolean
  current_streak: number
  days: WeekDayCell[]
}

export type WeekView = {
  as_of: string
  week_start: string
  week_end: string
  habits: WeekHabit[]
}

export type MetricSnapshot = {
  slug: string
  name: string
  unit: string | null
  aggregation: Aggregation
  latest_on: string | null
  latest_value: number | null
}

export type AreaView = {
  slug: string
  name: string
  description: string | null
  as_of: string
  metrics: MetricSnapshot[]
  habits: HabitStatus[]
  goals: GoalProgress[]
}

export type EntryCreate = {
  metric: string
  value?: boolean | number | string | null
  occurred_on?: string | null
  occurred_at?: string | null
  note?: string | null
}

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export function queryString(
  params: Record<string, string | number | boolean | null | undefined>,
): string {
  const search = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === '') continue
    search.set(key, String(value))
  }
  const encoded = search.toString()
  return encoded ? `?${encoded}` : ''
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  if (init?.body !== undefined && !headers.has('content-type')) {
    headers.set('content-type', 'application/json')
  }
  const response = await fetch(path, { ...init, headers })
  if (!response.ok) {
    const payload: unknown = await response.json().catch(() => null)
    const detail =
      payload !== null &&
      typeof payload === 'object' &&
      'detail' in payload &&
      typeof payload.detail === 'string'
        ? payload.detail
        : response.statusText
    throw new ApiError(response.status, detail)
  }
  if (response.status === 204) {
    return undefined as T
  }
  return (await response.json()) as T
}

export function listAreas(includeArchived = false): Promise<Area[]> {
  return request(`/areas${queryString({ include_archived: includeArchived || undefined })}`)
}

export function listMetrics(area?: string): Promise<Metric[]> {
  return request(`/metrics${queryString({ area })}`)
}

export function listHabits(metric?: string): Promise<Habit[]> {
  return request(`/habits${queryString({ metric })}`)
}

export function listGoals(filters?: { area?: string; status?: GoalStatus }): Promise<Goal[]> {
  return request(`/goals${queryString({ area: filters?.area, status: filters?.status })}`)
}

export function getToday(asOf?: string): Promise<TodayView> {
  return request(`/views/today${queryString({ as_of: asOf })}`)
}

export function getWeek(asOf?: string): Promise<WeekView> {
  return request(`/views/week${queryString({ as_of: asOf })}`)
}

export function getAreaView(slug: string, asOf?: string): Promise<AreaView> {
  return request(`/views/areas/${encodeURIComponent(slug)}${queryString({ as_of: asOf })}`)
}

export function getHabitStatus(slug: string, asOf?: string): Promise<HabitStatus> {
  return request(`/habits/${encodeURIComponent(slug)}/status${queryString({ as_of: asOf })}`)
}

export function getGoalProgress(slug: string, asOf?: string): Promise<GoalProgress> {
  return request(`/goals/${encodeURIComponent(slug)}/progress${queryString({ as_of: asOf })}`)
}

export function logEntry(body: EntryCreate): Promise<Entry> {
  return request('/entries', { method: 'POST', body: JSON.stringify(body) })
}

export function amendEntry(
  id: number,
  body: Partial<Pick<EntryCreate, 'value' | 'occurred_on' | 'occurred_at' | 'note'>>,
): Promise<Entry> {
  return request(`/entries/${id}`, { method: 'PATCH', body: JSON.stringify(body) })
}

export function deleteEntry(id: number): Promise<void> {
  return request(`/entries/${id}`, { method: 'DELETE' })
}
