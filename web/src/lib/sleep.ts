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
