import type { GoalProgress, PaceStatus } from './api'

const ON_TRACK: PaceStatus[] = ['on_track', 'achieved']
const BEHIND: PaceStatus[] = ['behind', 'overdue']
const AHEAD: PaceStatus[] = ['ahead']

export function summarizeGoals(goals: Pick<GoalProgress, 'pace' | 'fraction'>[]): {
  overall: number | null
  onTrack: number
  behind: number
  ahead: number
} {
  const fractions = goals
    .map((goal) => goal.fraction)
    .filter((value): value is number => value !== null)
  const overall =
    fractions.length === 0
      ? null
      : fractions.reduce((sum, value) => sum + value, 0) / fractions.length
  return {
    overall,
    onTrack: goals.filter((goal) => ON_TRACK.includes(goal.pace)).length,
    behind: goals.filter((goal) => BEHIND.includes(goal.pace)).length,
    ahead: goals.filter((goal) => AHEAD.includes(goal.pace)).length,
  }
}
