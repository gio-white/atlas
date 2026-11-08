# Home

## Purpose

The dashboard at `/`: three cards summarising sleep, screen time, and this week's habits. A "Today's quests" card (today's sessions and next actions) is added by Q3 of the [quest plan](../plans/quests-plan.md).

## Concepts

- **Card** — one self-contained summary that loads and fails on its own.

## Data model

Home stores nothing. It reads the sleep, screen, and habit endpoints.

## Rules and calculations

Nothing is computed in the browser; each card shows server-computed values.

## API

Home has no endpoints of its own. It calls `GET /sleep/view`, `GET /screen/dashboard`, `GET /views/habits/calendar`, and `PUT /habits/{slug}/days/{day}` (documented in each feature's doc).

## Screens

Home is three cards and nothing else. Top row: **Sleep** from `GET /sleep/view` (last night: asleep time, bed → wake, a four-lane stage timeline, and per-stage minutes and share; past 7 nights: average sleep / bedtime / wake and a bed-to-wake range bar per night drawn in stage colors; View all goes to `/sleep`; display-only, with no capture; with no nights: "No sleep data yet. It will appear here once a data source is connected.") and **Screen Time** from `GET /screen/dashboard` for `day` and `week` (Today shows the day total, Week avg shows the week's `daily_average` and each row's minutes divided by elapsed days; a second toggle splits by category, device, or app as ranked bars; View all goes to `/screen`; display-only; with no sessions at all: "No screen time data yet. It will appear here once a data source is connected.", and "No screen time recorded today / this week." for an empty period). Main row: **Habits** from `GET /views/habits/calendar?period=week` (one row per habit, Monday–Sunday cells; tapping a scheduled past-or-today cell confirms or clears a bool habit via `PUT /habits/{slug}/days/{day}`, and opens the log form for that metric and date otherwise). The habit name column is pinned while the day columns scroll sideways on narrow screens, and the grid opens scrolled so today is in view. Daily habits show their schedule under the name ("Every day", "Weekdays", "Weekends", or a list such as "Mon, Wed"), from the calendar's `kind` and `weekdays`. Each card degrades to its own unavailable message if its request fails. The quote on Home is static copy. Habits are not tasks: Home copy says habits scheduled, not tasks planned. The old Tasks card (today / upcoming / someday) was removed with the old task model.

Route inventory with status: [navigation](../product/navigation.md).

## Tests

- `web/src/lib/home.test.ts`, `web/src/lib/greeting.test.ts`

## Status

Implemented.
