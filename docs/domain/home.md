# Home

## Purpose

The single daily entry point, at `/`: what to do today, and where you stand. It merged the old
Home dashboard and the quest Today page ([redesign brief](../plans/redesign-brief.md) §5, phase 3).
The left column is today's work; every block in the right column is a doorway into its section.

## Concepts

- **Block** — one self-contained part of Home. Each reads its own source and fails on its own:
  a block whose request fails says "Couldn't load this right now." and the rest still show.
- **This week so far** — four numbers for the local Monday up to the end of the *As of* day,
  computed when Home loads and never stored.

## Data model

Home stores nothing. It reads sessions, tasks, habits, the journal, sleep, screen time, and the
library through their own endpoints, plus `GET /views/week-so-far`.

## Rules and calculations

`week_so_far` (`src/atlas/services/week.py`) returns, for the week from the local Monday to the
end of `as_of`, four of the numbers of Stats → This week (`week_numbers`,
[this week](this-week.md)), each by reusing its section's own calculation:

- **Sessions kept** — `sessions_kept` in `src/atlas/domain/quests.py`. Of the sessions starting
  in the week that are due an answer, how many were done. Due an answer: done, didn't happen
  (`missed`), or still planned after its end (unconfirmed). Cancelled sessions are left out, and
  so is a planned session that has not ended yet; a session marked done before its end counts as
  kept at once. With nothing due the number reads "—". Looking at a past *As of* day, "now" is
  the end of that day, so later answers do not count.
- **Habits kept** — `pooled_adherence_counts` in `src/atlas/services/habits.py`: satisfied over
  judged buckets from Monday to `as_of`, pooled over every active (not archived) habit, with the
  same adherence rule as each habit ([habits](habits.md#adherence)). Only complete buckets are
  judged, so today does not count for daily habits and the current week does not count for weekly
  ones; on a Monday the number reads "—". Paused or skipped days are excused, as everywhere.
- **Sleep, average** — `average_asleep` of the sleep view over the days from Monday to `as_of`
  ([sleep](sleep.md)): nights without data are left out.
- **Screen score** — the week's score from the screen dashboard ([screen time](screen-time.md)).

## API

| Method | Path | Purpose | Status |
| ------ | ---- | ------- | ------ |
| `GET` | `/views/week-so-far` | This week so far: `sessions_kept` / `sessions_total`, `habits_kept` / `habits_judged` / `habits_kept_share`, `sleep_average_minutes` / `sleep_nights`, `screen_score`, and `week_start` (`as_of`) | implemented |

Home also calls `GET /views/today`, `GET /views/habits`, `GET /journal`, `GET /views/main-quests`,
`GET /sleep/view`, `GET /screen/dashboard?period=day`, and
`GET /entertainment/titles?status=in_progress`, and the write endpoints of the controls it
reuses (session, habit, and journal).

## Screens

`web/src/pages/HomePage.tsx`; blocks in `web/src/components/home/`. A greeting ("Good
afternoon, Alex") heads the page; the date and *As of* are in the header.

**Wide screens (1024px and up): two columns.**

Left, in order:

1. **To confirm** — only when there are unconfirmed sessions: "1 session to confirm" / "n
   sessions to confirm", each with **Session done** and **Didn't happen** (`QuestBlocks.tsx`).
2. **Today** — today's sessions as a timeline with the **Now** line, each with **Session done**,
   **Cancel** (or **Didn't happen** once it has started), **Edit**, and, apart from them,
   **Outcome achieved** ([time blocks](time-blocks.md#screens)). **Plan a session** opens the
   session dialog. Empty: "No sessions today." On another *As of* day the heading is that date.
3. **Due today** — open tasks due today or earlier; overdue ones read "Overdue · 5 Nov". Each has
   **Schedule**. Empty: "Nothing due today."
4. **Up next** — the next action of each active goal and side quest, with **Schedule**. Empty:
   "No next steps yet. Add tasks to your quests."
5. **Habits** — daily habits scheduled today, then weekly and monthly ones, each as a row with
   its one-tap control (**Done today?**, quick amounts such as "+10", or **Log a slip**). The line
   under each row reads in the habit's own words: a quit habit "No slips today" / "1 slip today"
   (red once there is a slip); a daily amount "10 of 40 today", then "Done"; a daily yes / no
   habit nothing more; a weekly or monthly habit its progress for the period ("1 of 3", "4 days
   left" or "Done"). Only amounts get a progress bar. **All habits** goes to `/habit`, where the
   Monday–Sunday grid lives. Empty: "No habits yet."; with habits but none today: "No habits
   scheduled today." (`HabitsTodayBlock.tsx`).
6. **Note for today** — one line that grows to four while focused or once it holds more. **Save
   note** (or Ctrl/⌘+Enter) writes today's journal note (`POST /journal` the first time, then
   `PATCH /entries/{id}`) and shows "Saved". **Earlier notes** opens `/journal`
   ([journal](journal.md#screens)) (`NoteBlock.tsx`).

Right, in order (`StatusBlocks.tsx`):

1. **This week so far** — "Sessions kept 5 of 7", "Habits kept 82%", "Sleep, average 6h 50m",
   "Screen score 61"; "—" where a number cannot be computed yet. **This week** goes to Stats →
   This week ([this week](this-week.md)).
2. **Main quests** — active goals in the order of Main quests (each ambition's goals, then
   independent ones), at most five, each with its progress ring, title (to its quest map), and
   "Next: …". **All quests** goes to `/quests`. Empty: "No goals yet." with **Add a goal**.
3. **Last night** — time asleep and bed → wake ("7h 59m · 00:05 → 08:22"). The heading links to
   Stats → Sleep. Empty: "No sleep data for last night." Display-only, like Sleep.
4. **Screen time today** — today's total, followed by "of 3h cap" only when an active daily cap
   on all screen time exists; the total turns red when it is over that cap. The heading links to
   Stats → Screen time. Empty: "No screen time data yet today."
5. **In progress** — library titles in progress: a count and up to three names. The heading
   links to the library. Empty: "Nothing in progress."

**Narrow screens: one column**, in this order: To confirm, Today, Due today, Habits, Up next,
Note for today, This week so far, Main quests, Last night, Screen time today, In progress. Each
column is `display: contents` below 1024px, so its blocks join one list and `order-*` sets the
sequence; from 1024px the columns are flex columns and the order classes are reset.

Every change made from Home (a session answered, a habit checked in, a note saved) reloads Home,
so the weekly numbers follow. Old addresses: `/today` redirects to `/`.

Route inventory with status: [navigation](../product/navigation.md).

## Tests

- `tests/services/test_week.py` — week so far: empty, sessions kept (done, didn't happen,
  unconfirmed, cancelled, later today, last week), a past *As of* day, habits kept leaving today
  open, sleep and screen from their own views
- `tests/domain/test_quests.py` — `sessions_kept`
- `tests/api/test_views.py` — `GET /views/week-so-far`
- `web/src/components/home/home.test.tsx` — the four weekly numbers and their "—", a block that
  fails alone, Main quests order and limit, the screen cap shown only for an active daily cap on
  all screen time, In progress, Note for today (first write, then amend; grows when focused),
  habit rows (a quit habit reads slips today and logs a slip in one tap; daily and weekly
  amounts)
- `web/src/components/quests/time/execution.test.tsx` — Home's sessions: time range and path,
  Session done never completes the task, Outcome achieved, To confirm answered as done or as
  didn't happen
- `web/src/lib/greeting.test.ts`

## Status

Implemented (redesign brief phase 3).
