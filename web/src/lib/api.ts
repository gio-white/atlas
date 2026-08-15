export type ValueType = 'bool' | 'count' | 'quantity' | 'duration' | 'rating' | 'text'
export type Aggregation = 'sum' | 'last' | 'mean' | 'max' | 'min'
export type Direction = 'higher_is_better' | 'lower_is_better' | 'neutral'
export type Period = 'day' | 'week' | 'month'
export type Comparator = 'at_least' | 'at_most' | 'exactly'
export type GoalKind = 'metric_target' | 'milestone'
export type GoalHorizon = 'long' | 'medium' | 'short'
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
  area: string | null
  name: string
  kind: GoalKind
  metric: string | null
  target_value: number | null
  comparator: Comparator | null
  baseline_value: number | null
  measure: 'latest_value' | 'cumulative_since_start' | null
  start_on: string
  due_on: string
  horizon: GoalHorizon
  parent: string | null
  description: string | null
  status: GoalStatus
  achieved_at: string | null
}

export type Milestone = {
  name: string
  due_on: string | null
  done_at: string | null
}

export type GoalDetail = Goal & { milestones: Milestone[] }

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
  horizon: GoalHorizon
  parent: string | null
  description: string | null
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

export type HomeWeek = {
  as_of: string
  week_start: string
  week_end: string
  updates: number
  updates_last_week: number
  updates_delta: number | null
  slips: number
  slips_last_week: number
  slips_delta: number | null
  focus_minutes: number
  focus_minutes_last_week: number
  focus_delta: number | null
  tasks_done: number
  tasks_done_last_week: number
  tasks_delta: number | null
  series_updates: number[]
  series_slips: number[]
}

export type ScreenJudgment = 'useful' | 'waste' | 'neutral'
export type ScreenScoreBand = 'good' | 'ok' | 'poor'
export type ScreenInsightKind =
  | 'weekend_spike'
  | 'waste_share'
  | 'late_night'
  | 'improving'
  | 'sequence'
  | 'budget'
export type ScreenBudgetTargetKind = 'judgment' | 'category'

export type ScreenJudgmentTotals = {
  useful: number | null
  waste: number | null
  neutral: number | null
  total: number | null
}

export type ScreenAppRow = {
  slug: string
  name: string
  category: string
  metric: string
  minutes: number | null
  archived_at: string | null
}

export type ScreenCategoryRow = {
  slug: string
  name: string
  judgment: ScreenJudgment
  minutes: number | null
  apps: ScreenAppRow[]
  archived_at: string | null
}

export type ScreenSessionRow = {
  id: number
  app: string
  category: string
  metric: string
  occurred_on: string
  minutes: number | null
  note: string | null
}

export type ScreenBudgetStatus = {
  slug: string
  name: string
  target_kind: ScreenBudgetTargetKind
  target_slug: string
  period: Period
  target_value: number
  comparator: Comparator
  current_value: number | null
  satisfied: boolean
  scheduled: boolean
  current_streak: number
  longest_streak: number
  adherence: number | null
  as_of: string
}

export type ScreenView = {
  as_of: string
  categories: ScreenCategoryRow[]
  judgments: ScreenJudgmentTotals
  sessions: ScreenSessionRow[]
  budgets: ScreenBudgetStatus[]
}

export type ScreenAppShare = {
  slug: string
  name: string
  category: string
  category_name: string
  judgment: ScreenJudgment
  minutes: number
  share: number
}

export type ScreenCategoryShare = {
  slug: string
  name: string
  judgment: ScreenJudgment
  minutes: number
  share: number
  apps: ScreenAppShare[]
}

export type ScreenDeviceShare = {
  slug: string
  name: string
  minutes: number
  share: number
}

export type ScreenDayBar = {
  date: string
  useful: number
  waste: number
  neutral: number
  total: number
}

export type ScreenComparisonPoint = {
  current: number
  previous: number
}

export type ScreenTrendPoint = {
  week_start: string
  daily_average: number | null
}

export type ScreenLongestDay = {
  date: string
  minutes: number
}

export type ScreenInsight = {
  kind: ScreenInsightKind
  summary: string
  prescription: string
}

export type ScreenDashboard = {
  period: Period
  as_of: string
  range_start: string
  range_end: string
  previous_start: string
  previous_end: string
  total: number | null
  daily_average: number | null
  longest_day: ScreenLongestDay | null
  delta_minutes: number | null
  delta_fraction: number | null
  score: number | null
  score_band: ScreenScoreBand | null
  judgments: ScreenJudgmentTotals
  apps: ScreenAppShare[]
  categories: ScreenCategoryShare[]
  devices: ScreenDeviceShare[]
  daily: ScreenDayBar[]
  comparison: ScreenComparisonPoint[]
  hours: number[][]
  trend: ScreenTrendPoint[]
  insights: ScreenInsight[]
  budgets: ScreenBudgetStatus[]
}

export type ScreenCategory = {
  id: number
  slug: string
  name: string
  judgment: ScreenJudgment
  archived_at: string | null
}

export type ScreenApp = {
  id: number
  slug: string
  name: string
  category: string
  metric: string
  archived_at: string | null
}

export type ScreenDevice = {
  id: number
  slug: string
  name: string
  archived_at: string | null
}

export type ScreenSessionRecord = {
  id: number
  app: string
  device: string | null
  started_at: string | null
  ended_at: string | null
  minutes: number
  occurred_on: string
  note: string | null
  source: Source
  created_at: string
  entry_id: number | null
}

export type UpdatesStatus = {
  as_of: string
  checked_in: boolean
  current_streak: number
  longest_streak: number
}

export type SlipsWeek = {
  as_of: string
  week_start: string
  week_end: string
  this_week: number
  last_week: number
  delta_fraction: number | null
  series: number[]
}

export type TaskBucket = 'today' | 'upcoming' | 'someday'
export type TaskPriority = 'high' | 'normal' | 'low'

export type TaskItem = {
  id: number
  title: string
  bucket: TaskBucket
  due_on: string | null
  due_at: string | null
  priority: TaskPriority
  goal: string | null
  done_at: string | null
  created_at: string
}

export type GoalBoardColumn = {
  horizon: GoalHorizon
  on_track: number
  total: number
  fraction: number | null
  goals: GoalProgress[]
}

export type GoalBoardWeek = {
  total: number
  done: number
  fraction: number | null
  tasks: TaskItem[]
}

export type GoalsBoard = {
  as_of: string
  long: GoalBoardColumn
  medium: GoalBoardColumn
  short: GoalBoardColumn
  week: GoalBoardWeek
}

export type HabitsBoard = {
  as_of: string
  scheduled: number
  satisfied: number
  fraction: number | null
  day: HabitStatus[]
  week: HabitStatus[]
  month: HabitStatus[]
}

export type JournalDay = {
  as_of: string
  text: string | null
  entry_id: number | null
}

export type EntertainmentKind = 'film' | 'series' | 'anime' | 'video' | 'podcast' | 'book'
export type EntertainmentStatus = 'queued' | 'in_progress' | 'done' | 'dropped'

export type EntertainmentTopic = {
  id: number
  slug: string
  name: string
  archived_at: string | null
}

export type EntertainmentTopicRef = {
  slug: string
  name: string
}

export type EntertainmentTitle = {
  slug: string
  name: string
  kind: EntertainmentKind
  creator: string | null
  recommended_by: string | null
  status: EntertainmentStatus
  started_on: string | null
  finished_on: string | null
  progress: string | null
  note: string | null
  topics: EntertainmentTopicRef[]
  image: string | null
}

export type EntertainmentKindCount = {
  kind: EntertainmentKind
  count: number
  share: number
}

export type EntertainmentTopicCount = {
  slug: string
  name: string
  count: number
  share: number
}

export type EntertainmentLibrary = {
  queued: EntertainmentTitle[]
  in_progress: EntertainmentTitle[]
  done: EntertainmentTitle[]
  dropped: EntertainmentTitle[]
}

export type EntertainmentView = {
  as_of: string
  in_progress: number
  finished_this_week: number
  last_finished: EntertainmentTitle | null
}

export type EntertainmentDashboard = {
  period: Period
  as_of: string
  range_start: string
  range_end: string
  finished_in_range: number
  started_in_range: number
  queued: number
  in_progress: number
  done: number
  dropped: number
  by_kind: EntertainmentKindCount[]
  by_topic: EntertainmentTopicCount[]
  recently_finished: EntertainmentTitle[]
  library: EntertainmentLibrary
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

export const API_UNREACHABLE = 'API is not reachable. Start it with atlas serve.'

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

function errorDetail(payload: unknown, status: number, statusText: string): string {
  if (
    payload !== null &&
    typeof payload === 'object' &&
    'detail' in payload &&
    typeof payload.detail === 'string' &&
    payload.detail !== ''
  ) {
    return payload.detail
  }
  if (status === 502 || status === 503 || status === 504) {
    return API_UNREACHABLE
  }
  return statusText || API_UNREACHABLE
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  if (init?.body !== undefined && !headers.has('content-type')) {
    headers.set('content-type', 'application/json')
  }
  let response: Response
  try {
    response = await fetch(path, { ...init, headers })
  } catch {
    throw new ApiError(0, API_UNREACHABLE)
  }
  if (!response.ok) {
    const payload: unknown = await response.json().catch(() => null)
    throw new ApiError(response.status, errorDetail(payload, response.status, response.statusText))
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

export function listGoals(filters?: {
  area?: string
  status?: GoalStatus
  horizon?: GoalHorizon
  parent?: string
}): Promise<Goal[]> {
  return request(
    `/goals${queryString({
      area: filters?.area,
      status: filters?.status,
      horizon: filters?.horizon,
      parent: filters?.parent,
    })}`,
  )
}

export function getGoalsBoard(asOf?: string): Promise<GoalsBoard> {
  return request(`/views/goals${queryString({ as_of: asOf })}`)
}

export function getHabitsBoard(asOf?: string): Promise<HabitsBoard> {
  return request(`/views/habits${queryString({ as_of: asOf })}`)
}

export function getToday(asOf?: string): Promise<TodayView> {
  return request(`/views/today${queryString({ as_of: asOf })}`)
}

export function getWeek(asOf?: string): Promise<WeekView> {
  return request(`/views/week${queryString({ as_of: asOf })}`)
}

export function getHomeWeek(asOf?: string): Promise<HomeWeek> {
  return request(`/views/home${queryString({ as_of: asOf })}`)
}

export function getScreenView(asOf?: string): Promise<ScreenView> {
  return request(`/screen/view${queryString({ as_of: asOf })}`)
}

export function getScreenDashboard(period: Period, asOf?: string): Promise<ScreenDashboard> {
  return request(`/screen/dashboard${queryString({ period, as_of: asOf })}`)
}

export function listScreenCategories(includeArchived = false): Promise<ScreenCategory[]> {
  return request(
    `/screen/categories${queryString({ include_archived: includeArchived || undefined })}`,
  )
}

export function createScreenCategory(body: {
  slug: string
  judgment: ScreenJudgment
  name?: string | null
}): Promise<ScreenCategory> {
  return request('/screen/categories', { method: 'POST', body: JSON.stringify(body) })
}

export function listScreenApps(includeArchived = false): Promise<ScreenApp[]> {
  return request(`/screen/apps${queryString({ include_archived: includeArchived || undefined })}`)
}

export function createScreenApp(body: {
  slug: string
  category: string
  name?: string | null
}): Promise<ScreenApp> {
  return request('/screen/apps', { method: 'POST', body: JSON.stringify(body) })
}

export function listScreenDevices(includeArchived = false): Promise<ScreenDevice[]> {
  return request(
    `/screen/devices${queryString({ include_archived: includeArchived || undefined })}`,
  )
}

export function createScreenDevice(body: {
  slug: string
  name?: string | null
}): Promise<ScreenDevice> {
  return request('/screen/devices', { method: 'POST', body: JSON.stringify(body) })
}

export function logScreenSession(body: {
  app: string
  minutes?: number | null
  started_at?: string | null
  ended_at?: string | null
  occurred_on?: string | null
  device?: string | null
  note?: string | null
}): Promise<ScreenSessionRecord> {
  return request('/screen/sessions', { method: 'POST', body: JSON.stringify(body) })
}

export function getEntertainmentView(asOf?: string): Promise<EntertainmentView> {
  return request(`/entertainment/view${queryString({ as_of: asOf })}`)
}

export function getEntertainmentDashboard(
  period: Period,
  asOf?: string,
): Promise<EntertainmentDashboard> {
  return request(`/entertainment/dashboard${queryString({ period, as_of: asOf })}`)
}

export function listEntertainmentTopics(includeArchived = false): Promise<EntertainmentTopic[]> {
  return request(
    `/entertainment/topics${queryString({ include_archived: includeArchived || undefined })}`,
  )
}

export function createEntertainmentTopic(body: {
  slug: string
  name?: string | null
}): Promise<EntertainmentTopic> {
  return request('/entertainment/topics', { method: 'POST', body: JSON.stringify(body) })
}

export function listEntertainmentTitles(filters?: {
  kind?: EntertainmentKind
  status?: EntertainmentStatus
  topic?: string
}): Promise<EntertainmentTitle[]> {
  return request(
    `/entertainment/titles${queryString({
      kind: filters?.kind,
      status: filters?.status,
      topic: filters?.topic,
    })}`,
  )
}

export function createEntertainmentTitle(body: {
  slug: string
  kind: EntertainmentKind
  name?: string | null
  creator?: string | null
  recommended_by?: string | null
  status?: EntertainmentStatus
  started_on?: string | null
  finished_on?: string | null
  progress?: string | null
  note?: string | null
  topics?: string[]
  image_url?: string | null
}): Promise<EntertainmentTitle> {
  return request('/entertainment/titles', { method: 'POST', body: JSON.stringify(body) })
}

export function updateEntertainmentTitle(
  slug: string,
  body: {
    name?: string
    kind?: EntertainmentKind
    creator?: string | null
    recommended_by?: string | null
    status?: EntertainmentStatus
    started_on?: string | null
    finished_on?: string | null
    progress?: string | null
    note?: string | null
    topics?: string[]
    image_url?: string | null
  },
): Promise<EntertainmentTitle> {
  return request(`/entertainment/titles/${encodeURIComponent(slug)}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}

export async function uploadEntertainmentImage(
  slug: string,
  file: File,
): Promise<EntertainmentTitle> {
  const body = new FormData()
  body.append('file', file)
  let response: Response
  try {
    response = await fetch(`/entertainment/titles/${encodeURIComponent(slug)}/image`, {
      method: 'PUT',
      body,
    })
  } catch {
    throw new ApiError(0, API_UNREACHABLE)
  }
  if (!response.ok) {
    const payload: unknown = await response.json().catch(() => null)
    throw new ApiError(response.status, errorDetail(payload, response.status, response.statusText))
  }
  return (await response.json()) as EntertainmentTitle
}

export function getUpdates(asOf?: string): Promise<UpdatesStatus> {
  return request(`/updates${queryString({ as_of: asOf })}`)
}

export function logUpdate(body?: {
  occurred_on?: string | null
  note?: string | null
}): Promise<Entry> {
  return request('/updates', { method: 'POST', body: JSON.stringify(body ?? {}) })
}

export function getSlips(asOf?: string): Promise<SlipsWeek> {
  return request(`/slips${queryString({ as_of: asOf })}`)
}

export function logSlip(body?: {
  occurred_on?: string | null
  note?: string | null
}): Promise<Entry> {
  return request('/slips', { method: 'POST', body: JSON.stringify(body ?? {}) })
}

export function listTasks(filters?: {
  bucket?: TaskBucket
  include_done?: boolean
  goal?: string
}): Promise<TaskItem[]> {
  return request(
    `/tasks${queryString({
      bucket: filters?.bucket,
      include_done: filters?.include_done,
      goal: filters?.goal,
    })}`,
  )
}

export function createTask(body: {
  title: string
  bucket?: TaskBucket
  due_on?: string | null
  due_at?: string | null
  priority?: TaskPriority
  goal?: string | null
}): Promise<TaskItem> {
  return request('/tasks', { method: 'POST', body: JSON.stringify(body) })
}

export function updateTask(
  id: number,
  body: Partial<{
    title: string
    bucket: TaskBucket
    due_on: string | null
    due_at: string | null
    priority: TaskPriority
    done: boolean
    goal: string | null
  }>,
): Promise<TaskItem> {
  return request(`/tasks/${id}`, { method: 'PATCH', body: JSON.stringify(body) })
}

export function getJournal(asOf?: string): Promise<JournalDay> {
  return request(`/journal${queryString({ as_of: asOf })}`)
}

export function logJournal(body: { text: string; occurred_on?: string | null }): Promise<Entry> {
  return request('/journal', { method: 'POST', body: JSON.stringify(body) })
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

export function createArea(body: {
  slug: string
  name?: string | null
  description?: string | null
}): Promise<Area> {
  return request('/areas', { method: 'POST', body: JSON.stringify(body) })
}

export function updateArea(
  slug: string,
  body: { name?: string; description?: string | null },
): Promise<Area> {
  return request(`/areas/${encodeURIComponent(slug)}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}

export function archiveArea(slug: string): Promise<Area> {
  return request(`/areas/${encodeURIComponent(slug)}/archive`, { method: 'POST' })
}

export function createMetric(body: {
  slug: string
  area: string
  value_type: ValueType
  aggregation: Aggregation
  name?: string | null
  unit?: string | null
  direction?: Direction
}): Promise<Metric> {
  return request('/metrics', { method: 'POST', body: JSON.stringify(body) })
}

export function updateMetric(
  slug: string,
  body: { name?: string; unit?: string | null; direction?: Direction },
): Promise<Metric> {
  return request(`/metrics/${encodeURIComponent(slug)}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}

export function archiveMetric(slug: string): Promise<Metric> {
  return request(`/metrics/${encodeURIComponent(slug)}/archive`, { method: 'POST' })
}

export function createHabit(body: {
  slug: string
  metric: string
  period: Period
  target_value: number
  comparator: Comparator
  name?: string | null
  weekdays?: number[] | null
  active_from?: string | null
  active_to?: string | null
}): Promise<Habit> {
  return request('/habits', { method: 'POST', body: JSON.stringify(body) })
}

export function updateHabit(
  slug: string,
  body: {
    name?: string
    target_value?: number
    comparator?: Comparator
    weekdays?: number[] | null
    active_to?: string | null
  },
): Promise<Habit> {
  return request(`/habits/${encodeURIComponent(slug)}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}

export function createGoal(body: {
  slug: string
  area?: string | null
  kind: GoalKind
  start_on: string
  due_on: string
  name?: string | null
  metric?: string | null
  target_value?: number | null
  comparator?: Comparator | null
  baseline_value?: number | null
  measure?: 'latest_value' | 'cumulative_since_start' | null
  milestones?: { name: string; due_on?: string | null }[] | null
  horizon?: GoalHorizon | null
  parent?: string | null
  description?: string | null
}): Promise<Goal> {
  return request('/goals', { method: 'POST', body: JSON.stringify(body) })
}

export function getGoal(slug: string): Promise<GoalDetail> {
  return request(`/goals/${encodeURIComponent(slug)}`)
}

export function updateGoal(
  slug: string,
  body: {
    name?: string
    due_on?: string
    target_value?: number
    status?: Exclude<GoalStatus, 'achieved'>
    horizon?: GoalHorizon
    parent?: string | null
    description?: string | null
    area?: string | null
  },
): Promise<Goal> {
  return request(`/goals/${encodeURIComponent(slug)}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}

export function toggleMilestone(
  goalSlug: string,
  name: string,
  done?: boolean,
): Promise<Milestone> {
  return request(
    `/goals/${encodeURIComponent(goalSlug)}/milestones/${encodeURIComponent(name)}/toggle${queryString({ done })}`,
    { method: 'POST' },
  )
}
