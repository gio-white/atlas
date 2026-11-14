import { describe, expect, it } from 'vitest'

import type { Habit } from './api'
import {
  clockInput,
  fieldErrors,
  fieldsFromHabit,
  NEW_HABIT,
  parseClockInput,
  ruleChanged,
  ruleFromFields,
  SOURCE_OPTIONS,
  withSource,
} from './habitForm'

const WAKE: Habit = {
  id: 1,
  slug: 'wake',
  name: 'Wake up early',
  time_of_day: 'morning',
  first_day: '2026-10-18',
  archived_at: null,
  rule: {
    starts_on: '2026-10-18',
    frequency: 'every_day',
    check: 'data',
    weekdays: null,
    times: null,
    source: 'wake_time',
    source_ref: null,
    source_ref_name: null,
    threshold: 'before',
    value: 420,
  },
}

const RUN: Habit = {
  ...WAKE,
  slug: 'run',
  name: 'Run',
  time_of_day: 'anytime',
  rule: {
    ...WAKE.rule,
    frequency: 'times_a_week',
    times: 3,
    check: 'manual',
    source: null,
    threshold: null,
    value: null,
  },
}

describe('habit sheet fields', () => {
  it('starts a new habit as every day, ticked, any time', () => {
    expect(ruleFromFields({ ...NEW_HABIT, name: 'Read' })).toEqual({
      frequency: 'every_day',
      check: 'manual',
      weekdays: null,
      times: null,
      source: null,
      source_ref: null,
      threshold: null,
      value: null,
    })
    expect(NEW_HABIT.timeOfDay).toBe('anytime')
  })

  it('sends only the fields the frequency uses', () => {
    expect(
      ruleFromFields({ ...NEW_HABIT, frequency: 'specific_days', weekdays: [5, 1, 3] }).weekdays,
    ).toEqual([1, 3, 5])
    expect(ruleFromFields({ ...NEW_HABIT, frequency: 'times_a_week', timesAWeek: 4 }).times).toBe(4)
    expect(ruleFromFields({ ...NEW_HABIT, frequency: 'times_a_month', timesAMonth: 2 }).times).toBe(
      2,
    )
  })

  it('takes a source’s default threshold and value, and its category or app', () => {
    const bad = withSource({ ...NEW_HABIT, check: 'data' }, 'screen_bad_apps')
    expect(bad).toMatchObject({ threshold: 'at_most', value: 90 })
    const insta = { ...withSource(bad, 'screen_app'), sourceRef: 'instagram' }
    expect(ruleFromFields(insta)).toMatchObject({
      check: 'data',
      source: 'screen_app',
      source_ref: 'instagram',
      threshold: 'at_most',
      value: 30,
    })
    expect(ruleFromFields(withSource(bad, 'sessions_planned'))).toMatchObject({
      threshold: 'before',
      value: 720,
      source_ref: null,
    })
  })

  it('offers every source the API knows, with its thresholds', () => {
    expect(SOURCE_OPTIONS.map((option) => option.source)).toEqual([
      'wake_time',
      'bedtime',
      'time_asleep',
      'screen_bad_apps',
      'screen_category',
      'screen_app',
      'screen_total',
      'sessions_planned',
    ])
  })

  it('fills the sheet from a habit and sees when the rule changes', () => {
    const wake = fieldsFromHabit(WAKE)
    expect(wake).toMatchObject({ name: 'Wake up early', check: 'data', value: 420 })
    expect(ruleChanged(WAKE, wake)).toBe(false)
    expect(ruleChanged(WAKE, { ...wake, name: 'Rise early', timeOfDay: 'evening' })).toBe(false)
    expect(ruleChanged(WAKE, { ...wake, value: 390 })).toBe(true)
    const run = fieldsFromHabit(RUN)
    expect(run.timesAWeek).toBe(3)
    expect(ruleChanged(RUN, run)).toBe(false)
    expect(ruleChanged(RUN, { ...run, timesAWeek: 4 })).toBe(true)
    expect(ruleChanged(RUN, { ...run, check: 'data' })).toBe(true)
  })

  it('says what stops a save', () => {
    expect(fieldErrors(NEW_HABIT).name).toBe('Give the habit a name.')
    expect(
      fieldErrors({ ...NEW_HABIT, name: 'Gym', frequency: 'specific_days', weekdays: [] }),
    ).toEqual({ weekdays: 'Pick at least one day.' })
    const category = withSource(
      { ...NEW_HABIT, name: 'Less social', check: 'data' },
      'screen_category',
    )
    expect(fieldErrors(category)).toEqual({ sourceRef: 'Pick a category.' })
    expect(fieldErrors({ ...category, sourceRef: 'social', value: 0 }).value).toBe(
      'Enter a time between 1 minute and 24 hours.',
    )
    expect(fieldErrors({ ...withSource(category, 'wake_time'), value: Number.NaN }).value).toBe(
      'Enter a time of day.',
    )
    expect(fieldErrors({ ...NEW_HABIT, name: 'Read' })).toEqual({})
  })

  it('reads and writes time inputs', () => {
    expect(clockInput(420)).toBe('07:00')
    expect(clockInput(Number.NaN)).toBe('')
    expect(parseClockInput('06:45')).toBe(405)
    expect(parseClockInput('')).toBeNull()
    expect(parseClockInput('25:00')).toBeNull()
  })
})
