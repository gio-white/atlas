export type ValueType = 'bool' | 'count' | 'quantity' | 'duration' | 'rating' | 'text'
export type Aggregation = 'sum' | 'last' | 'mean' | 'max' | 'min'
export type Direction = 'higher_is_better' | 'lower_is_better' | 'neutral'
export type Period = 'day' | 'week' | 'month'
export type Comparator = 'at_least' | 'at_most' | 'exactly'
export type HabitKind = 'check' | 'count' | 'duration' | 'quit'
export type TimeOfDay = 'morning' | 'afternoon' | 'evening' | 'anytime'
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
  kind: HabitKind
  period: Period
  target_value: number
  comparator: Comparator
  unit: string | null
  weekdays: number[] | null
  time_of_day: TimeOfDay
  active_from: string
  active_to: string | null
  archived_at: string | null
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
  kind: HabitKind
  time_of_day: TimeOfDay
  unit: string | null
  archived: boolean
  bucket_start: string | null
  bucket_end: string | null
  days_left: number
  effective_target: number | null
  excused: boolean
  skipped_today: boolean
  today_value: number | null
  last_entry_on: string | null
  weekdays: number[] | null
}

export type HabitBreak = {
  id: number
  start_on: string
  end_on: string
  note: string | null
}

export type HabitCheckIn = {
  id: number
  occurred_on: string
  value: number | null
  note: string | null
  created_at: string
}

export type HabitDetail = {
  habit: Habit
  status: HabitStatus
  breaks: HabitBreak[]
  recent: HabitCheckIn[]
}

export type WeekDayCell = {
  day: string
  scheduled: boolean
  value: number | null
  satisfied: boolean | null
  excused: boolean
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
  kind: HabitKind
  weekdays: number[] | null
}

export type HabitsCalendar = {
  as_of: string
  period: Period
  range_start: string
  range_end: string
  habits: WeekHabit[]
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

export type ScreenBudget = {
  id: number
  slug: string
  name: string
  target_kind: ScreenBudgetTargetKind
  target_slug: string
  period: Period
  target_value: number
  comparator: Comparator
  active_from: string
  active_to: string | null
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
  last_recorded_at: string | null
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

export type SleepStage = 'awake' | 'rem' | 'light' | 'deep'

export type SleepStageMinutes = Record<SleepStage, number>

export type SleepSegment = {
  stage: SleepStage
  start_offset: number
  end_offset: number
}

export type SleepNight = {
  date: string
  session_id: number | null
  started_at: string
  ended_at: string
  bed_offset: number
  wake_offset: number
  in_bed_minutes: number
  asleep_minutes: number
  stages: SleepStageMinutes
  segments: SleepSegment[]
}

export type SleepView = {
  as_of: string
  range_start: string
  range_end: string
  night: SleepNight | null
  days: { date: string; night: SleepNight | null }[]
  nights_logged: number
  average_asleep: number | null
  average_bed_offset: number | null
  average_wake_offset: number | null
  average_stages: SleepStageMinutes | null
  bed_spread: number | null
  wake_spread: number | null
  last_recorded_at: string | null
}

export type HabitsBoard = {
  as_of: string
  scheduled: number
  satisfied: number
  fraction: number | null
  completion_7d: number | null
  completion_30d: number | null
  day: HabitStatus[]
  week: HabitStatus[]
  month: HabitStatus[]
}

export type JournalDay = {
  as_of: string
  text: string | null
  entry_id: number | null
}

export type EntertainmentKind =
  | 'film'
  | 'series'
  | 'anime'
  | 'video'
  | 'podcast'
  | 'book'
  | 'music'
  | 'other'
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
  rating: number | null
  link: string | null
  topics: EntertainmentTopicRef[]
  image: string | null
  created_at: string | null
}

export type EntertainmentLinkSuggestion = {
  link: string
  name: string | null
  kind: EntertainmentKind | null
  creator: string | null
  image_url: string | null
  existing: string | null
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

export function listMetrics(area?: string, includeArchived = false): Promise<Metric[]> {
  return request(`/metrics${queryString({ area, include_archived: includeArchived || undefined })}`)
}

export function listEntries(filters?: {
  metric?: string
  area?: string
  exclude_area?: string
  start_on?: string
  end_on?: string
  limit?: number
}): Promise<Entry[]> {
  return request(`/entries${queryString(filters ?? {})}`)
}

export function listHabits(metric?: string): Promise<Habit[]> {
  return request(`/habits${queryString({ metric })}`)
}

export function getHabitsBoard(asOf?: string): Promise<HabitsBoard> {
  return request(`/views/habits${queryString({ as_of: asOf })}`)
}

export function getHabitsCalendar(period: Period, asOf?: string): Promise<HabitsCalendar> {
  return request(`/views/habits/calendar${queryString({ period, as_of: asOf })}`)
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

export function updateScreenCategory(
  slug: string,
  body: { name?: string | null; judgment?: ScreenJudgment | null },
): Promise<ScreenCategory> {
  return request(`/screen/categories/${encodeURIComponent(slug)}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}

export function updateScreenApp(
  slug: string,
  body: { name?: string | null; category?: string | null },
): Promise<ScreenApp> {
  return request(`/screen/apps/${encodeURIComponent(slug)}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}

export function listScreenBudgets(): Promise<ScreenBudget[]> {
  return request('/screen/budgets')
}

export function createScreenBudget(body: {
  slug: string
  name?: string | null
  target_kind: ScreenBudgetTargetKind
  target_slug: string
  period: Period
  target_value: number
  comparator: Comparator
  active_from?: string | null
}): Promise<ScreenBudget> {
  return request('/screen/budgets', { method: 'POST', body: JSON.stringify(body) })
}

export function updateScreenBudget(
  slug: string,
  body: {
    name?: string | null
    target_value?: number | null
    comparator?: Comparator | null
    active_to?: string | null
  },
): Promise<ScreenBudget> {
  return request(`/screen/budgets/${encodeURIComponent(slug)}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
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
  rating?: number | null
  link?: string | null
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
    rating?: number | null
    link?: string | null
    topics?: string[]
    image_url?: string | null
  },
): Promise<EntertainmentTitle> {
  return request(`/entertainment/titles/${encodeURIComponent(slug)}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}

export function lookupEntertainmentLink(url: string): Promise<EntertainmentLinkSuggestion> {
  return request('/entertainment/lookup', { method: 'POST', body: JSON.stringify({ url }) })
}

export function deleteEntertainmentTitle(slug: string): Promise<void> {
  return request(`/entertainment/titles/${encodeURIComponent(slug)}`, { method: 'DELETE' })
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

export function getSleepView(asOf?: string, days?: number): Promise<SleepView> {
  return request(`/sleep/view${queryString({ as_of: asOf, days })}`)
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

export function setHabitDay(
  slug: string,
  day: string,
  done: boolean,
  asOf?: string,
): Promise<HabitStatus> {
  return request(`/habits/${encodeURIComponent(slug)}/days/${day}${queryString({ as_of: asOf })}`, {
    method: 'PUT',
    body: JSON.stringify({ done }),
  })
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
  slug?: string | null
  name?: string | null
  kind?: HabitKind | null
  metric?: string | null
  period?: Period
  target_value?: number | null
  comparator?: Comparator | null
  unit?: string | null
  weekdays?: number[] | null
  time_of_day?: TimeOfDay
  active_from?: string | null
  active_to?: string | null
  area?: string | null
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
    time_of_day?: TimeOfDay
    unit?: string | null
  },
): Promise<Habit> {
  return request(`/habits/${encodeURIComponent(slug)}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}

function habitPath(slug: string, rest = ''): string {
  return `/habits/${encodeURIComponent(slug)}${rest}`
}

export function archiveHabit(slug: string): Promise<Habit> {
  return request(habitPath(slug, '/archive'), { method: 'POST' })
}

export function unarchiveHabit(slug: string): Promise<Habit> {
  return request(habitPath(slug, '/unarchive'), { method: 'POST' })
}

export function deleteHabit(slug: string): Promise<void> {
  return request(habitPath(slug), { method: 'DELETE' })
}

export function getHabitDetail(slug: string, asOf?: string): Promise<HabitDetail> {
  return request(habitPath(slug, `/detail${queryString({ as_of: asOf })}`))
}

export function checkInHabit(
  slug: string,
  body: { amount?: number | null; on?: string | null; note?: string | null },
  asOf?: string,
): Promise<HabitStatus> {
  return request(habitPath(slug, `/checkins${queryString({ as_of: asOf })}`), {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export function undoHabitCheckIn(slug: string, on?: string, asOf?: string): Promise<HabitStatus> {
  return request(habitPath(slug, `/checkins/last${queryString({ on, as_of: asOf })}`), {
    method: 'DELETE',
  })
}

export function addHabitBreak(
  slug: string,
  body: { start_on: string; end_on?: string | null; note?: string | null },
): Promise<HabitBreak> {
  return request(habitPath(slug, '/breaks'), { method: 'POST', body: JSON.stringify(body) })
}

export function deleteHabitBreak(slug: string, breakId: number): Promise<void> {
  return request(habitPath(slug, `/breaks/${breakId}`), { method: 'DELETE' })
}

// --- Quests (docs/domain/quests.md, docs/domain/time-blocks.md) ------------------------------
// Every quest entity uses its integer id. Q2 and Q3 build on these; add nothing here for them.

export type QuestKind = 'ambition' | 'goal' | 'milestone' | 'side_quest' | 'chapter' | 'task'
export type ParentKind = 'ambition' | 'goal' | 'milestone' | 'chapter' | 'side_quest'
export type PromoteKind = Exclude<QuestKind, 'task'>
export type QuestStatus = 'active' | 'completed' | 'archived'
export type TaskStatus = 'todo' | 'in_progress' | 'completed'
export type TaskPriority = 'low' | 'normal' | 'high'
export type ChapterState = 'empty' | 'not_started' | 'in_progress' | 'completed'
export type TimeBlockStatus = 'scheduled' | 'completed' | 'cancelled'

export type ItemRef = { kind: QuestKind; id: number; title: string }

export type TimeBlock = {
  id: number
  task_id: number
  start_at: string
  end_at: string
  status: TimeBlockStatus
  provider: 'internal'
  external_event_id: string | null
  created_at: string
  updated_at: string
  minutes: number
  unconfirmed: boolean
  overlaps: boolean
}

export type QuestTask = {
  id: number
  title: string
  description: string | null
  status: TaskStatus
  priority: TaskPriority
  estimate_minutes: number | null
  due_on: string | null
  weight: number | null
  weight_share: number | null
  position: number
  parent: ItemRef | null
  path: ItemRef[]
  inbox: boolean
  standalone: boolean
  organized_at: string | null
  started_at: string | null
  completed_at: string | null
  archived_at: string | null
  created_at: string
  updated_at: string
  planned_minutes: number
  block_count: number
}

export type QuestTaskDetail = QuestTask & { blocks: TimeBlock[] }

type QuestState = {
  id: number
  title: string
  description: string | null
  position: number
  archived_at: string | null
  created_at: string
  updated_at: string
  path: ItemRef[]
  /** 0–1, or null when nothing is under it yet ("Not broken down yet"). */
  progress: number | null
  done_tasks: number
  total_tasks: number
  planned_minutes: number
  eligible: boolean
  open_children: ItemRef[]
  next_action: QuestTask | null
}

type Completable = QuestState & {
  status: QuestStatus
  completed_at: string | null
  completed_with_open_items: boolean
}

export type Ambition = Completable & {
  target_on: string | null
  weight: number | null
  goal_count: number
  task_count: number
}

export type QuestGoal = Completable & {
  ambition_id: number | null
  success_description: string | null
  due_on: string | null
  weight: number | null
  weight_share: number | null
  milestone_count: number
  task_count: number
}

export type QuestMilestone = Completable & {
  goal_id: number
  due_on: string | null
  weight: number | null
  weight_share: number | null
  chapter_count: number
  task_count: number
}

export type SideQuest = Completable & {
  due_on: string | null
  chapter_count: number
  task_count: number
}

export type Chapter = QuestState & {
  milestone_id: number | null
  side_quest_id: number | null
  weight: number | null
  weight_share: number | null
  state: ChapterState
  task_count: number
}

export type ChapterTree = { chapter: Chapter; tasks: QuestTask[] }
export type MilestoneTree = {
  milestone: QuestMilestone
  chapters: ChapterTree[]
  tasks: QuestTask[]
}
export type AmbitionSection = { ambition: Ambition; goals: QuestGoal[]; tasks: QuestTask[] }
export type MainQuests = { ambitions: AmbitionSection[]; independent_goals: QuestGoal[] }
export type GoalTree = { goal: QuestGoal; milestones: MilestoneTree[]; tasks: QuestTask[] }
export type SideQuestTree = { side_quest: SideQuest; chapters: ChapterTree[]; tasks: QuestTask[] }
export type SideQuests = { side_quests: SideQuest[]; standalone_tasks: QuestTask[] }
export type Inbox = { count: number; tasks: QuestTask[] }
export type ScheduledBlock = { block: TimeBlock; task: QuestTask }
export type TodayQuests = {
  date: string
  blocks: ScheduledBlock[]
  unconfirmed: ScheduledBlock[]
  due_today: QuestTask[]
  up_next: QuestTask[]
}
export type QuestCalendar = { start: string; end: string; blocks: ScheduledBlock[] }
export type PromoteResult = { kind: PromoteKind; id: number; title: string }

type ContainerFields = {
  title?: string
  description?: string | null
  position?: number
}
type Archivable = { archived?: boolean }

export type AmbitionCreate = ContainerFields & {
  title: string
  target_on?: string | null
  weight?: number | null
}
export type AmbitionUpdate = Omit<AmbitionCreate, 'title'> & { title?: string } & Archivable
export type GoalCreate = ContainerFields & {
  title: string
  success_description?: string | null
  due_on?: string | null
  ambition_id?: number | null
  weight?: number | null
}
export type GoalUpdate = Omit<GoalCreate, 'title'> & { title?: string } & Archivable
export type MilestoneCreate = ContainerFields & {
  title: string
  goal_id: number
  due_on?: string | null
  weight?: number | null
}
export type MilestoneUpdate = Partial<MilestoneCreate> & Archivable
export type SideQuestCreate = ContainerFields & { title: string; due_on?: string | null }
export type SideQuestUpdate = Partial<SideQuestCreate> & Archivable
export type ChapterCreate = ContainerFields & {
  title: string
  milestone_id?: number | null
  side_quest_id?: number | null
  weight?: number | null
}
export type ChapterUpdate = Partial<ChapterCreate> & Archivable

export type TaskCreate = {
  title: string
  description?: string | null
  parent_kind?: ParentKind | null
  parent_id?: number | null
  standalone?: boolean
  priority?: TaskPriority
  estimate_minutes?: number | null
  due_on?: string | null
  weight?: number | null
  position?: number
}
export type TaskUpdate = {
  title?: string
  description?: string | null
  status?: TaskStatus
  priority?: TaskPriority
  estimate_minutes?: number | null
  due_on?: string | null
  weight?: number | null
  position?: number
  archived?: boolean
}
export type TaskOrganize =
  | { parent_kind: ParentKind; parent_id: number; standalone?: false }
  | { standalone: true }
export type TaskPromote = {
  kind: PromoteKind
  parent_kind?: ParentKind | null
  parent_id?: number | null
}
export type TaskFilters = {
  parent_kind?: ParentKind
  parent_id?: number
  status?: TaskStatus
  inbox?: boolean
  standalone?: boolean
  due_on?: string
  include_archived?: boolean
}

function send<T>(path: string, method: string, body?: unknown): Promise<T> {
  return request(path, {
    method,
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  })
}

function archivedQuery(includeArchived?: boolean): string {
  return queryString({ include_archived: includeArchived || undefined })
}

export function listAmbitions(includeArchived?: boolean): Promise<Ambition[]> {
  return request(`/ambitions${archivedQuery(includeArchived)}`)
}
export function createAmbition(body: AmbitionCreate): Promise<Ambition> {
  return send('/ambitions', 'POST', body)
}
export function getAmbition(id: number): Promise<Ambition> {
  return request(`/ambitions/${id}`)
}
export function updateAmbition(id: number, body: AmbitionUpdate): Promise<Ambition> {
  return send(`/ambitions/${id}`, 'PATCH', body)
}
export function deleteAmbition(id: number): Promise<void> {
  return send(`/ambitions/${id}`, 'DELETE')
}
export function completeAmbition(id: number, override = false): Promise<Ambition> {
  return send(`/ambitions/${id}/complete`, 'POST', { override })
}
export function reopenAmbition(id: number): Promise<Ambition> {
  return send(`/ambitions/${id}/reopen`, 'POST')
}

export function listQuestGoals(filters?: {
  ambition_id?: number
  include_archived?: boolean
}): Promise<QuestGoal[]> {
  return request(
    `/goals${queryString({
      ambition_id: filters?.ambition_id,
      include_archived: filters?.include_archived || undefined,
    })}`,
  )
}
export function createQuestGoal(body: GoalCreate): Promise<QuestGoal> {
  return send('/goals', 'POST', body)
}
export function getQuestGoal(id: number): Promise<QuestGoal> {
  return request(`/goals/${id}`)
}
export function updateQuestGoal(id: number, body: GoalUpdate): Promise<QuestGoal> {
  return send(`/goals/${id}`, 'PATCH', body)
}
export function deleteQuestGoal(id: number): Promise<void> {
  return send(`/goals/${id}`, 'DELETE')
}
export function completeQuestGoal(id: number, override = false): Promise<QuestGoal> {
  return send(`/goals/${id}/complete`, 'POST', { override })
}
export function reopenQuestGoal(id: number): Promise<QuestGoal> {
  return send(`/goals/${id}/reopen`, 'POST')
}

export function createMilestone(body: MilestoneCreate): Promise<QuestMilestone> {
  return send('/milestones', 'POST', body)
}
export function getMilestone(id: number): Promise<QuestMilestone> {
  return request(`/milestones/${id}`)
}
export function updateMilestone(id: number, body: MilestoneUpdate): Promise<QuestMilestone> {
  return send(`/milestones/${id}`, 'PATCH', body)
}
export function deleteMilestone(id: number): Promise<void> {
  return send(`/milestones/${id}`, 'DELETE')
}
export function completeMilestone(id: number, override = false): Promise<QuestMilestone> {
  return send(`/milestones/${id}/complete`, 'POST', { override })
}
export function reopenMilestone(id: number): Promise<QuestMilestone> {
  return send(`/milestones/${id}/reopen`, 'POST')
}

export function listSideQuests(includeArchived?: boolean): Promise<SideQuest[]> {
  return request(`/side-quests${archivedQuery(includeArchived)}`)
}
export function createSideQuest(body: SideQuestCreate): Promise<SideQuest> {
  return send('/side-quests', 'POST', body)
}
export function getSideQuest(id: number): Promise<SideQuest> {
  return request(`/side-quests/${id}`)
}
export function updateSideQuest(id: number, body: SideQuestUpdate): Promise<SideQuest> {
  return send(`/side-quests/${id}`, 'PATCH', body)
}
export function deleteSideQuest(id: number): Promise<void> {
  return send(`/side-quests/${id}`, 'DELETE')
}
export function completeSideQuest(id: number, override = false): Promise<SideQuest> {
  return send(`/side-quests/${id}/complete`, 'POST', { override })
}
export function reopenSideQuest(id: number): Promise<SideQuest> {
  return send(`/side-quests/${id}/reopen`, 'POST')
}

export function createChapter(body: ChapterCreate): Promise<Chapter> {
  return send('/chapters', 'POST', body)
}
export function getChapter(id: number): Promise<Chapter> {
  return request(`/chapters/${id}`)
}
export function updateChapter(id: number, body: ChapterUpdate): Promise<Chapter> {
  return send(`/chapters/${id}`, 'PATCH', body)
}
export function deleteChapter(id: number): Promise<void> {
  return send(`/chapters/${id}`, 'DELETE')
}

export function listQuestTasks(filters?: TaskFilters): Promise<QuestTask[]> {
  return request(`/tasks${queryString({ ...filters })}`)
}
export function createQuestTask(body: TaskCreate): Promise<QuestTaskDetail> {
  return send('/tasks', 'POST', body)
}
export function getQuestTask(id: number): Promise<QuestTaskDetail> {
  return request(`/tasks/${id}`)
}
export function updateQuestTask(id: number, body: TaskUpdate): Promise<QuestTaskDetail> {
  return send(`/tasks/${id}`, 'PATCH', body)
}
export function deleteQuestTask(id: number): Promise<void> {
  return send(`/tasks/${id}`, 'DELETE')
}
export function organizeTask(id: number, body: TaskOrganize): Promise<QuestTaskDetail> {
  return send(`/tasks/${id}/organize`, 'POST', body)
}
export function promoteTask(id: number, body: TaskPromote): Promise<PromoteResult> {
  return send(`/tasks/${id}/promote`, 'POST', body)
}

export function listTimeBlocks(filters?: {
  start?: string
  end?: string
  task_id?: number
}): Promise<TimeBlock[]> {
  return request(`/time-blocks${queryString({ ...filters })}`)
}
export function createTimeBlock(body: {
  task_id: number
  start_at: string
  end_at: string
}): Promise<TimeBlock> {
  return send('/time-blocks', 'POST', body)
}
export function updateTimeBlock(
  id: number,
  body: { start_at?: string; end_at?: string },
): Promise<TimeBlock> {
  return send(`/time-blocks/${id}`, 'PATCH', body)
}
export function deleteTimeBlock(id: number): Promise<void> {
  return send(`/time-blocks/${id}`, 'DELETE')
}
export function completeTimeBlock(id: number): Promise<TimeBlock> {
  return send(`/time-blocks/${id}/complete`, 'POST')
}
export function cancelTimeBlock(id: number): Promise<TimeBlock> {
  return send(`/time-blocks/${id}/cancel`, 'POST')
}

export function getMainQuests(includeArchived?: boolean): Promise<MainQuests> {
  return request(`/views/main-quests${archivedQuery(includeArchived)}`)
}
export function getAmbitionView(id: number, includeArchived?: boolean): Promise<AmbitionSection> {
  return request(`/views/ambitions/${id}${archivedQuery(includeArchived)}`)
}
export function getGoalTree(id: number, includeArchived?: boolean): Promise<GoalTree> {
  return request(`/views/goals/${id}${archivedQuery(includeArchived)}`)
}
export function getSideQuestsView(includeArchived?: boolean): Promise<SideQuests> {
  return request(`/views/side-quests${archivedQuery(includeArchived)}`)
}
export function getSideQuestTree(id: number, includeArchived?: boolean): Promise<SideQuestTree> {
  return request(`/views/side-quests/${id}${archivedQuery(includeArchived)}`)
}
export function getInbox(): Promise<Inbox> {
  return request('/views/inbox')
}
export function getTodayQuests(asOf?: string): Promise<TodayQuests> {
  return request(`/views/today${queryString({ as_of: asOf })}`)
}
export function getQuestCalendar(start: string, end: string): Promise<QuestCalendar> {
  return request(`/views/calendar${queryString({ start, end })}`)
}
