import type { GoalHorizon } from './api'

export const HORIZONS: GoalHorizon[] = ['long', 'medium', 'short']

export const PARENT_HORIZON: Record<GoalHorizon, GoalHorizon | null> = {
  long: null,
  medium: 'long',
  short: 'medium',
}

export const HORIZON_META: Record<GoalHorizon, { label: string; window: string; kicker: string }> =
  {
    long: {
      label: 'Long Term',
      window: '1+ year',
      kicker: 'Your big vision. Where you want to be in the long run.',
    },
    medium: {
      label: 'Medium Term',
      window: 'Months',
      kicker: 'Milestones that move you closer to your long-term goals.',
    },
    short: {
      label: 'Short Term',
      window: 'This week',
      kicker: 'Focus areas for the week that create real momentum.',
    },
  }

export function slugFromName(name: string): string {
  return name
    .toLowerCase()
    .replaceAll(/[^a-z0-9]+/g, '-')
    .replaceAll(/^-|-$/g, '')
}
