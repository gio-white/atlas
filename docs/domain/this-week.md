# This week

## Purpose

Stats → This week, at `/stats/week`: one Monday–Sunday week in five blocks (Quests, Habits,
Sleep, Screen time, Library), each compared with the week before. It replaces a weekly review
ritual: the numbers do the reviewing ([redesign brief](../plans/redesign-brief.md) §8, decision
D5). Home's **This week so far** is four of these numbers ([home](home.md)).

## Concepts

- **Week** — the local Monday–Sunday week holding the *As of* day, counted from Monday up to
  the end of that day. Once the *As of* day is the Sunday, the whole week is counted
  (`complete`).
- **Last week** — the same weekdays one week earlier: Monday up to the *As of* day minus seven
  days. A week in progress is compared like for like ("Thursday so far" against last Monday to
  Thursday); a whole week against the whole week before.
- Everything is computed when the page loads, from the existing data, by each section's own
  calculation. Nothing is stored.

## Data model

None of its own. It reads sessions (`time_block`), tasks, milestones, habits,
sleep sessions, screen sessions, and library titles.

## Rules and calculations

`src/atlas/services/week.py`:

- `week_numbers(session, as_of, now)` computes one window, Monday of `as_of`'s week to `as_of`
  (local dates; UTC bounds from `local_day_bounds`). Looking back at a past day, "now" is the
  end of that day, so a session answered later still counts by what it is now, but a session
  that had not ended by then is not yet due an answer.
- `this_week(session, as_of, now)` returns the window for `as_of` (`current`), the window for
  `as_of − 7 days` (`previous`), `week_start` / `week_end` (Monday and Sunday), `complete`
  (`as_of` is the Sunday), and each active habit's part of Habits kept (`habits`).
- `week_so_far` is Home's subset of `week_numbers`.

Each number, per window:

| Block | Number | Rule |
| ----- | ------ | ---- |
| Quests | Sessions kept | `sessions_kept` ([home](home.md#rules-and-calculations)): done out of sessions due an answer (done, didn't happen, or unconfirmed); cancelled ones and ones not yet ended are left out |
| Quests | Tasks completed | tasks whose status is completed and whose `completed_at` falls in the window; a task reopened since does not count |
| Quests | Milestones completed | milestones whose status is completed and whose `completed_at` falls in the window |
| Habits | Habits kept | `habits_kept`: min(Done, target) over the target across active habits; finished days count, and today once Done; a weekly or monthly habit's whole target. The previous window's last day is judged as its "today", like for like ([habits](habits.md#day-results-streaks-and-habits-kept)) |
| Habits | One row per habit | `habits_kept_by_habit`: each active habit's `done` and `target` for the window; the rows add up to Habits kept |
| Sleep | Time asleep, average; bedtime, average; wake time, average | `average_asleep`, `average_bed_offset`, `average_wake_offset` of the sleep view over the window's days ([sleep](sleep.md)); bedtime and wake time are minutes from local midnight, negative before midnight |
| Sleep | Missing nights | days in the window without a night |
| Screen time | Total, daily average, score, and the Good / Neutral / Bad split | the week dashboard for `as_of` (`screen_dashboard`, period week, which is clipped to Monday–`as_of`) ([screen time](screen-time.md)); the split is the `useful` / `neutral` / `waste` minutes |
| Library | Titles finished | `finished_in_range` of the library dashboard, period week ([library](library.md)) |

## API

| Method | Path | Purpose | Status |
| ------ | ---- | ------- | ------ |
| `GET` | `/views/this-week` | `as_of`, `week_start`, `week_end`, `complete`, `current` and `previous` (each: `sessions_kept` / `sessions_total`, `tasks_completed`, `milestones_completed`, `habits_kept` / `habits_judged` / `habits_kept_share`, `sleep_average_minutes`, `sleep_average_bedtime`, `sleep_average_wake`, `sleep_nights`, `sleep_missing_nights`, `screen_total`, `screen_daily_average`, `screen_score`, `screen_good` / `screen_neutral` / `screen_bad`, `titles_finished`, plus `as_of` / `week_start`), and `habits` (`slug`, `name`, `done`, `target`) (`as_of`) | implemented |

## Screens

`web/src/pages/ThisWeekPage.tsx`, wording in `web/src/lib/thisWeek.ts`. It is the first Stats
tab; `/stats` opens it.

- **Title**: "This week" for the week holding today, otherwise "Week of 2 Nov 2026". Under it,
  the range ("9–15 Nov 2026"), followed by "· up to Thu 12 Nov" while the week is counted only in
  part, and then the line "Compared with the same days last week."
- **Previous week** and **Next week** move by whole weeks: they set `?on=` to that week's Sunday,
  and remove it for the week holding today. Next week is off on the week holding today. Like
  everywhere, `?on=` is the *As of* date, so the header shows it.
- **Five blocks**. From 1024px, two columns that stack on their own: Quests, Sleep, Library on
  the left; Habits and Screen time on the right. Below, one column in the order Quests, Habits,
  Sleep, Screen time, Library (`order-*`, as on Home). Each heading links to its section, keeping
  `?on=`.
  - **Quests** (to Main quests): Sessions kept "5 of 7" with "Last week 4 of 6"; Tasks completed;
    Milestones completed.
  - **Habits** (to Habits): Habits kept "84%", then one row per active habit with its name
    only *until habits phase 6* (the API already sends each row's `done` / `target`). Empty: "No
    habits yet."
  - **Sleep** (to Stats → Sleep): Time asleep, average; Bedtime, average; Wake time, average;
    Missing nights. Empty: "No sleep data this week."
  - **Screen time** (to Stats → Screen time): Total, Daily average, Score, and a Good / Neutral /
    Bad bar with minutes. Empty: "No screen time data this week."
  - **Library** (to Library): Titles finished.
- **Changes from last week**, under a number, in muted text: "+35m vs last week", "+2 vs last
  week", "+5 points vs last week" (a share), "20m later than last week" (a time of day), or "Same
  as last week". None when either week has no number. Missing nights shows no change.

Home's **This week so far** has the link **This week** to this page.

## Tests

- `tests/services/test_week.py` — the same weekdays a week earlier, a past Sunday as a complete
  week, tasks / milestones / titles finished in the window (a reopened task left out), the
  each habit's part adding up to Habits kept (today counted once Done), the screen split and sleep times; and Home's week so
  far
- `tests/api/test_views.py` — `GET /views/this-week`
- `web/src/lib/thisWeek.test.ts` — titles, range line, week steps, the wording of changes
- `web/src/pages/ThisWeekPage.test.tsx` — the five blocks with their changes and links, empty
  states

## Status

Implemented (redesign brief phase 4). What comes next (a month view, other comparisons) is open
([open points](../plans/open-points.md) §11).
