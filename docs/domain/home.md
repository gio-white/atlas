# Home

## Purpose

The dashboard at `/`: four cards summarising sleep, screen time, today's quests (sessions and next steps), and this week's habits. `/today` is the full execution screen; Home keeps a short slice of it (quest plan D13). The [redesign brief](../plans/redesign-brief.md) merges `/today` into Home in its phase 3; until then Home is as described here.

## Concepts

- **Card** — one self-contained summary that loads and fails on its own.

## Data model

Home stores nothing. It reads the sleep, screen, habit, and Today endpoints.

## Rules and calculations

Nothing is computed in the browser; each card shows server-computed values. Today's quests shows the API's `unconfirmed` list length and block statuses as returned.

## API

Home has no endpoints of its own. It calls `GET /sleep/view`, `GET /screen/dashboard`, `GET /views/habits/calendar`, `PUT /habits/{slug}/days/{day}`, `GET /views/today`, and `POST /time-blocks/{id}/complete` (documented in each feature's doc).

## Screens

Home is four cards and nothing else. Top row: **Sleep** from `GET /sleep/view` (last night: asleep time, bed → wake, a four-lane stage timeline, and per-stage minutes and share; past 7 nights: average sleep / bedtime / wake and a bed-to-wake range bar per night drawn in stage colors; View all goes to `/sleep`; display-only, with no capture; with no nights: "No sleep data yet. It will appear here once a data source is connected.") and **Screen Time** from `GET /screen/dashboard` for `day` and `week` (Today shows the day total, Week avg shows the week's `daily_average` and each row's minutes divided by elapsed days; a second toggle splits by category, device, or app as ranked bars; View all goes to `/screen`; display-only; with no sessions at all: "No screen time data yet. It will appear here once a data source is connected.", and "No screen time recorded today / this week." for an empty period).

Main row, side by side on wide screens: **Today's quests** and **Habits**.

**Today's quests** (`web/src/components/home/TodaysQuestsCard.tsx`) reads `GET /views/today?as_of=` and sits in the slot the old Tasks card had:

- When `unconfirmed` is not empty, a link to `/today`: "1 past session to confirm" / "n past sessions to confirm".
- **Sessions**, with "· n of m done" once any are done: the next three of today's blocks that are still scheduled and not unconfirmed. Each shows its time range, task, and parent path, plus a **Session done** button (`POST /time-blocks/{id}/complete`; it never completes the task, see [time blocks](time-blocks.md#screens)).
- **Next steps**: the first three of `up_next`.
- Empty cases: "No sessions planned for today.", "No more sessions planned today.", and "No next steps yet. Add tasks to your quests."
- View all goes to `/today`.

**Habits** from `GET /views/habits/calendar?period=week`:

- One row per habit with Monday–Sunday cells.
- Tapping a scheduled past-or-today cell confirms or clears a bool habit via `PUT /habits/{slug}/days/{day}`. For other habits it opens the log form for that metric and date.
- The habit name column is pinned while the day columns scroll sideways on narrow screens, and the grid opens scrolled so today is in view.
- Daily habits show their schedule under the name ("Every day", "Weekdays", "Weekends", or a list such as "Mon, Wed"), from the calendar's `kind` and `weekdays`.

A **Journal** link beside the greeting opens `/journal`, which has no entry on the rail; it stays until Home holds the note for today (brief phase 3). Each card degrades to its own unavailable message if its request fails. The quote on Home is static copy. Habits are not tasks: Home copy says habits scheduled, not tasks planned. The old Tasks card (today / upcoming / someday) was removed with the old task model, and Today's quests took its place.

Route inventory with status: [navigation](../product/navigation.md).

## Tests

- `web/src/lib/home.test.ts`, `web/src/lib/greeting.test.ts`
- `web/src/components/quests/time/execution.test.tsx` — the session controls Home's card shares with Today (Session done calls only the block endpoint)

## Status

Implemented.
