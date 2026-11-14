export type ValueType = 'bool' | 'count' | 'quantity' | 'duration' | 'rating' | 'text'
export type Aggregation = 'sum' | 'last' | 'mean' | 'max' | 'min'
export type Direction = 'higher_is_better' | 'lower_is_better' | 'neutral'
export type Period = 'day' | 'week' | 'month'
export type Comparator = 'at_least' | 'at_most' | 'exactly'
/** How often a habit is due (docs/domain/habits.md). */
export type HabitFrequency = 'every_day' | 'specific_days' | 'times_a_week' | 'times_a_month'
/** Ticked by you, or read from a source (sleep, screen time, planned sessions). */
export type HabitCheck = 'manual' | 'data'
export type HabitSource =
  | 'wake_time'
  | 'bedtime'
  | 'time_asleep'
  | 'screen_bad_apps'
  | 'screen_category'
  | 'screen_app'
  | 'screen_total'
  | 'sessions_planned'
export type HabitThreshold = 'at_least' | 'at_most' | 'before' | 'after'
export type TimeOfDay = 'morning' | 'afternoon' | 'evening' | 'anytime'
export type Source = 'cli' | 'api' | 'import'

/** How a metric came to exist. Only `manual` ones are set up by hand; `screen` ones are written by
 * device data. */
export type MetricOrigin = 'manual' | 'habit' | 'screen' | 'journal'

export type Metric = {
  id: number
  slug: string
  origin: MetricOrigin
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

/** A rule version: the one in force today. A data rule's `value` is minutes (a duration) or
 * minutes after midnight (a time of day). */
export type HabitRule = {
  starts_on: string
  frequency: HabitFrequency
  check: HabitCheck
  weekdays: number[] | null
  times: number | null
  source: HabitSource | null
  source_ref: string | null
  /** The category's or app's name, for a rule on one. */
  source_ref_name: string | null
  threshold: HabitThreshold | null
  value: number | null
}

export type Habit = {
  id: number
  slug: string
  name: string
  time_of_day: TimeOfDay
  first_day: string
  archived_at: string | null
  rule: HabitRule
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
export type ScreenBudgetTargetKind = 'judgment' | 'category' | 'total'

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
  /** Everything up to this moment has arrived from the device (UTC); null until it says so. */
  complete_through: string | null
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

export type JournalDay = {
  as_of: string
  text: string | null
  entry_id: number | null
}

export type LibraryKind =
  | 'film'
  | 'series'
  | 'anime'
  | 'video'
  | 'podcast'
  | 'book'
  | 'music'
  | 'other'
export type LibraryStatus = 'queued' | 'in_progress' | 'done' | 'dropped'

export type LibraryTopic = {
  id: number
  slug: string
  name: string
  archived_at: string | null
}

export type LibraryTopicRef = {
  slug: string
  name: string
}

export type LibraryTitle = {
  slug: string
  name: string
  kind: LibraryKind
  creator: string | null
  recommended_by: string | null
  status: LibraryStatus
  started_on: string | null
  finished_on: string | null
  progress: string | null
  note: string | null
  rating: number | null
  link: string | null
  topics: LibraryTopicRef[]
  image: string | null
  created_at: string | null
}

export type LibraryLinkSuggestion = {
  link: string
  name: string | null
  kind: LibraryKind | null
  creator: string | null
  image_url: string | null
  existing: string | null
}

export type LibraryKindCount = {
  kind: LibraryKind
  count: number
  share: number
}

export type LibraryTopicCount = {
  slug: string
  name: string
  count: number
  share: number
}

export type LibraryShelves = {
  queued: LibraryTitle[]
  in_progress: LibraryTitle[]
  done: LibraryTitle[]
  dropped: LibraryTitle[]
}

export type LibraryDashboard = {
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
  by_kind: LibraryKindCount[]
  by_topic: LibraryTopicCount[]
  recently_finished: LibraryTitle[]
  library: LibraryShelves
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

export function listMetrics(includeArchived = false): Promise<Metric[]> {
  return request(`/metrics${queryString({ include_archived: includeArchived || undefined })}`)
}

export function listEntries(filters?: {
  metric?: string
  /** `false` leaves out entries written by device data (screen time) rather than typed. */
  include_automatic?: boolean
  start_on?: string
  end_on?: string
  limit?: number
}): Promise<Entry[]> {
  return request(`/entries${queryString(filters ?? {})}`)
}

export function listHabits(): Promise<Habit[]> {
  return request('/habits')
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

export function getLibraryDashboard(period: Period, asOf?: string): Promise<LibraryDashboard> {
  return request(`/library/dashboard${queryString({ period, as_of: asOf })}`)
}

export function listLibraryTopics(includeArchived = false): Promise<LibraryTopic[]> {
  return request(
    `/library/topics${queryString({ include_archived: includeArchived || undefined })}`,
  )
}

export function listLibraryTitles(filters?: {
  kind?: LibraryKind
  status?: LibraryStatus
  topic?: string
}): Promise<LibraryTitle[]> {
  return request(
    `/library/titles${queryString({
      kind: filters?.kind,
      status: filters?.status,
      topic: filters?.topic,
    })}`,
  )
}

export function createLibraryTitle(body: {
  slug: string
  kind: LibraryKind
  name?: string | null
  creator?: string | null
  recommended_by?: string | null
  status?: LibraryStatus
  started_on?: string | null
  finished_on?: string | null
  progress?: string | null
  note?: string | null
  rating?: number | null
  link?: string | null
  topics?: string[]
  image_url?: string | null
}): Promise<LibraryTitle> {
  return request('/library/titles', { method: 'POST', body: JSON.stringify(body) })
}

export function updateLibraryTitle(
  slug: string,
  body: {
    name?: string
    kind?: LibraryKind
    creator?: string | null
    recommended_by?: string | null
    status?: LibraryStatus
    started_on?: string | null
    finished_on?: string | null
    progress?: string | null
    note?: string | null
    rating?: number | null
    link?: string | null
    topics?: string[]
    image_url?: string | null
  },
): Promise<LibraryTitle> {
  return request(`/library/titles/${encodeURIComponent(slug)}`, {
    method: 'PATCH',
    body: JSON.stringify(body),
  })
}

export function lookupLibraryLink(url: string): Promise<LibraryLinkSuggestion> {
  return request('/library/lookup', { method: 'POST', body: JSON.stringify({ url }) })
}

export function deleteLibraryTitle(slug: string): Promise<void> {
  return request(`/library/titles/${encodeURIComponent(slug)}`, { method: 'DELETE' })
}

export async function uploadLibraryImage(slug: string, file: File): Promise<LibraryTitle> {
  const body = new FormData()
  body.append('file', file)
  let response: Response
  try {
    response = await fetch(`/library/titles/${encodeURIComponent(slug)}/image`, {
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
  return (await response.json()) as LibraryTitle
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

export function createMetric(body: {
  /** Left out, the slug is made from the name. */
  slug?: string
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

// --- Quests (docs/domain/quests.md, docs/domain/time-blocks.md) ------------------------------
// Every quest entity uses its integer id. Q2 and Q3 build on these; add nothing here for them.

export type QuestKind = 'ambition' | 'goal' | 'milestone' | 'side_quest' | 'chapter' | 'task'
export type ParentKind = 'ambition' | 'goal' | 'milestone' | 'chapter' | 'side_quest'
export type PromoteKind = Exclude<QuestKind, 'task'>
export type QuestStatus = 'active' | 'completed' | 'archived'
export type TaskStatus = 'todo' | 'in_progress' | 'completed'
export type TaskPriority = 'low' | 'normal' | 'high'
export type ChapterState = 'empty' | 'not_started' | 'in_progress' | 'completed'
/** `missed`: the session's time came and it did not happen ("Didn't happen"). */
export type TimeBlockStatus = 'scheduled' | 'completed' | 'cancelled' | 'missed'

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
/** A week of sessions, and the next actions that have no upcoming session (`not_scheduled`). */
export type Plan = {
  start: string
  end: string
  blocks: ScheduledBlock[]
  not_scheduled: QuestTask[]
}
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

/** Didn't happen: only for a session that has started. Unlike cancel, it counts as not kept. */
export function missTimeBlock(id: number): Promise<TimeBlock> {
  return send(`/time-blocks/${id}/miss`, 'POST')
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
export function getPlan(start: string, end: string): Promise<Plan> {
  return request(`/views/plan${queryString({ start, end })}`)
}

/** This week so far (local Monday to the end of `as_of`), for Home. Every number is computed
 * by the API from its section's own rules. */
export type WeekSoFar = {
  as_of: string
  week_start: string
  sessions_kept: number
  sessions_total: number
  habits_kept: number
  habits_judged: number
  habits_kept_share: number | null
  sleep_average_minutes: number | null
  sleep_nights: number
  screen_score: number | null
}

export function getWeekSoFar(asOf?: string): Promise<WeekSoFar> {
  return request(`/views/week-so-far${queryString({ as_of: asOf })}`)
}

/** One Monday-to-`as_of` window of This week; minutes for sleep and screen time. */
export type WeekNumbers = {
  as_of: string
  week_start: string
  sessions_kept: number
  sessions_total: number
  tasks_completed: number
  milestones_completed: number
  habits_kept: number
  habits_judged: number
  habits_kept_share: number | null
  sleep_average_minutes: number | null
  /** Minutes from local midnight; negative is the evening before. */
  sleep_average_bedtime: number | null
  sleep_average_wake: number | null
  sleep_nights: number
  sleep_missing_nights: number
  screen_total: number | null
  screen_daily_average: number | null
  screen_score: number | null
  screen_good: number | null
  screen_neutral: number | null
  screen_bad: number | null
  titles_finished: number
}

/** An active habit on This week. Its week's result returns with the habits calculations. */
/** An active habit on This week with its part of Habits kept (Done, capped, over the target). */
export type WeekHabit = {
  slug: string
  name: string
  done: number
  target: number
}

export type ThisWeek = {
  as_of: string
  week_start: string
  week_end: string
  complete: boolean
  current: WeekNumbers
  previous: WeekNumbers
  habits: WeekHabit[]
}

export function getThisWeek(asOf?: string): Promise<ThisWeek> {
  return request(`/views/this-week${queryString({ as_of: asOf })}`)
}
