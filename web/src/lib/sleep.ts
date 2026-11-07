import type { SleepStage, SleepStageMinutes, SleepView } from './api'

export const SLEEP_STAGES: SleepStage[] = ['deep', 'light', 'rem', 'awake']

export const SLEEP_STAGE_META: Record<SleepStage, { label: string; bg: string; fill: string }> = {
  deep: { label: 'Deep', bg: 'bg-stage-deep', fill: 'fill-stage-deep' },
  light: { label: 'Light', bg: 'bg-stage-light', fill: 'fill-stage-light' },
  rem: { label: 'REM', bg: 'bg-stage-rem', fill: 'fill-stage-rem' },
  awake: { label: 'Awake', bg: 'bg-stage-awake', fill: 'fill-stage-awake' },
}

const DAY_MINUTES = 24 * 60

export function formatClock(offset: number | null): string {
  if (offset === null) return '—'
  const wrapped = ((Math.round(offset) % DAY_MINUTES) + DAY_MINUTES) % DAY_MINUTES
  const hours = String(Math.floor(wrapped / 60)).padStart(2, '0')
  const minutes = String(wrapped % 60).padStart(2, '0')
  return `${hours}:${minutes}`
}

export function stageShares(
  stages: SleepStageMinutes,
): { stage: SleepStage; minutes: number; share: number }[] {
  const total = SLEEP_STAGES.reduce((sum, stage) => sum + stages[stage], 0)
  return SLEEP_STAGES.map((stage) => ({
    stage,
    minutes: stages[stage],
    share: total > 0 ? stages[stage] / total : 0,
  }))
}

export function weekAxis(view: SleepView): { start: number; end: number; ticks: number[] } {
  const nights = view.days.flatMap((day) => (day.night === null ? [] : [day.night]))
  const earliest = Math.min(-120, ...nights.map((night) => night.bed_offset))
  const latest = Math.max(480, ...nights.map((night) => night.wake_offset))
  const start = Math.floor(earliest / 60) * 60
  const end = Math.ceil(latest / 60) * 60
  const step = end - start > 12 * 60 ? 240 : 120
  const ticks: number[] = []
  for (let tick = Math.ceil(start / step) * step; tick <= end; tick += step) ticks.push(tick)
  return { start, end, ticks }
}

export type SleepRange = 'week' | 'month' | 'quarter'

export const SLEEP_RANGES: { id: SleepRange; label: string; days: number }[] = [
  { id: 'week', label: 'Week', days: 7 },
  { id: 'month', label: 'Month', days: 30 },
  { id: 'quarter', label: '90 days', days: 90 },
]

export function parseSleepRange(raw: string | null): SleepRange {
  return SLEEP_RANGES.some((range) => range.id === raw) ? (raw as SleepRange) : 'week'
}

export function rangeDays(range: SleepRange): number {
  return SLEEP_RANGES.find((item) => item.id === range)?.days ?? 7
}

/** "±25m" for a spread in minutes; a dash when there are too few nights to measure. */
export function formatSpread(spread: number | null): string {
  if (spread === null) return '—'
  const minutes = Math.round(spread)
  if (minutes < 60) return `±${minutes}m`
  const hours = Math.floor(minutes / 60)
  const rest = minutes % 60
  return rest === 0 ? `±${hours}h` : `±${hours}h ${rest}m`
}

/** Plain words for how much bed or wake time moves from night to night. */
export function consistencyLabel(spread: number | null): string {
  if (spread === null) return 'Needs two nights'
  if (spread <= 30) return 'Steady'
  if (spread <= 60) return 'Varies a little'
  return 'Irregular'
}

/** Whole-hour ticks from 0 up to at least the longest night, for the time-asleep chart. */
export function asleepAxis(view: SleepView): { max: number; ticks: number[] } {
  const longest = Math.max(
    0,
    ...view.days.flatMap((day) => (day.night === null ? [] : [day.night.asleep_minutes])),
  )
  const max = Math.max(8 * 60, Math.ceil(longest / 120) * 120)
  const ticks: number[] = []
  for (let tick = 0; tick <= max; tick += 120) ticks.push(tick)
  return { max, ticks }
}

/** Every day in the window, newest first, keeping days without a night so gaps stay visible. */
export function daysNewestFirst(view: SleepView): SleepView['days'] {
  return [...view.days].reverse()
}
