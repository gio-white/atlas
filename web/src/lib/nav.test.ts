import { describe, expect, it } from 'vitest'

import APP from '../App.tsx?raw'
import { activeDestination, DESTINATIONS, INBOX_PATH, SECTIONS, SETTINGS } from './nav'

describe('destinations', () => {
  it('lists the five rail destinations in order, with Settings apart', () => {
    expect(DESTINATIONS.map((destination) => destination.label)).toEqual([
      'Home',
      'Quests',
      'Habits',
      'Stats',
      'Library',
    ])
    expect(SETTINGS.label).toBe('Settings')
  })

  it('names the tabs inside each section', () => {
    expect(SECTIONS.quests.tabs.map((tab) => tab.label)).toEqual([
      'Main quests',
      'Side quests',
      'Inbox',
      'Plan',
    ])
    expect(SECTIONS.stats.tabs.map((tab) => tab.label)).toEqual(['Sleep', 'Screen time', 'Health'])
    expect(SECTIONS.settings.tabs.map((tab) => tab.label)).toEqual([
      'Appearance',
      'Screen time setup',
      'Devices',
      'Metrics',
      'All entries',
    ])
  })

  it('gives every tab its own address, and the Inbox tab the badge path', () => {
    const paths = Object.values(SECTIONS).flatMap((section) => section.tabs.map((tab) => tab.to))
    expect(new Set(paths).size).toBe(paths.length)
    expect(paths).toContain(INBOX_PATH)
  })

  it('points every destination and tab at a route in App.tsx', () => {
    const targets = [
      ...DESTINATIONS.map((destination) => destination.to),
      SETTINGS.to,
      ...Object.values(SECTIONS).flatMap((section) => section.tabs.map((tab) => tab.to)),
    ].filter((path) => path !== '/')
    for (const path of targets) {
      expect(APP, `no route for ${path}`).toContain(`path="${path}"`)
    }
  })
})

describe('activeDestination', () => {
  it('marks Home only for Home and the pages reached from it', () => {
    expect(activeDestination('/')).toBe('home')
    expect(activeDestination('/journal')).toBe('home')
    expect(activeDestination('/nowhere')).toBe('home')
  })

  it('matches a destination by its address and everything under it', () => {
    expect(activeDestination('/quests')).toBe('quests')
    expect(activeDestination('/quests/goals/4')).toBe('quests')
    expect(activeDestination('/quests/side-quests/2/')).toBe('quests')
    expect(activeDestination('/habit/meditate')).toBe('habits')
    expect(activeDestination('/stats/screen-time')).toBe('stats')
    expect(activeDestination('/library/books')).toBe('library')
  })

  it('does not match a path that only starts with the same letters', () => {
    expect(activeDestination('/habits-old')).toBe('home')
  })

  it('marks Settings for every Settings tab', () => {
    expect(activeDestination('/settings/entries')).toBe('settings')
    expect(activeDestination('/settings/metrics')).toBe('settings')
  })
})
