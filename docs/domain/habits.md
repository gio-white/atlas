# Habits

## Purpose

Recurring commitments over a metric: a schedule plus a target, with check-ins, skips and pauses, streaks, and adherence computed on read.

## Concepts

- **Habit** — a schedule (`period`, optional `weekdays`) plus a target and comparator over a metric.
- **Kind** — `check`, `count`, `duration`, or `quit`; how it is checked in and shown.
- **Check-in** — an ordinary entry written through the habit.
- **Break** — a skip (one day) or pause (a range) that excuses buckets.
- **Satisfied / missed / excused** — the outcome of one scheduled bucket.

## Data model

### Habit

A recurring commitment over a metric: a schedule plus a target.

| Field          | Type            | Notes                                                                                   |
| -------------- | --------------- | --------------------------------------------------------------------------------------- |
| `id`           | int             | primary key                                                                             |
| `metric_id`    | int             | FK to `Metric`                                                                          |
| `slug`         | str             | unique                                                                                  |
| `name`         | str             |                                                                                         |
| `period`       | enum            | `day | week | month` — the bucket the target applies to                                 |
| `target_value` | float           |                                                                                         |
| `comparator`   | enum            | `at_least | at_most | exactly`                                                          |
| `weekdays`     | set[int] | None | ISO weekdays (Mon=1 … Sun=7); only valid when `period` is `day`, `None` means every day |
| `active_from`  | date            | inclusive                                                                               |
| `active_to`    | date | None     | inclusive; `None` means open-ended                                                      |
| `kind`         | enum            | `check | count | duration | quit` — how it is checked in and displayed                  |
| `time_of_day`  | enum            | `morning | afternoon | evening | anytime` — groups the Today checklist                   |
| `goal_id`      | int | None      | optional FK to `Goal` the habit supports                                                |
| `archived_at`  | datetime | None | UTC; archived habits leave every board but keep their history                          |

`at_most` is not an afterthought: "no more than one coffee a day" and "at least three runs a week" are the same machinery with a different comparator.

Habits are created habit-first: without an explicit metric, `create_habit` makes one — in the area given by `area_slug` when set (it must exist and not be archived), otherwise in the internal `habits` area (created on first use) — with slug = habit slug (`-2`… on collision) and name = the habit's name and picks its shape from `kind`: `check` → `bool`, `count` → `count` (user unit), `duration` → `duration` (`min`), `quit` → `count` (`slips`, `lower_is_better`). Every made metric aggregates with `sum`. A `quit` habit is always `period = day`, `at_most 0`: any slip fails the day, and its streak is the run of clean days. Passing a metric keeps the older metric-first path; `kind` then defaults from the metric's value type, and `area_slug` is rejected (the area only applies to a metric made for the habit). A habit's area is chosen on create only; moving it later would mean moving its metric, which `update_habit` does not do.

### HabitBreak

A skip or pause: a date range in which a habit is excused. A one-day break is a skip.

| Field        | Type        | Notes                        |
| ------------ | ----------- | ---------------------------- |
| `id`         | int         | primary key                  |
| `habit_id`   | int         | FK to `Habit`                |
| `start_on`   | date        | inclusive, local             |
| `end_on`     | date        | inclusive, `>= start_on`     |
| `note`       | str | None  | reason (travel, sick…)       |
| `created_at` | datetime    | UTC                          |

Overlapping breaks are allowed; coverage is their union.

## Rules and calculations

### Habit satisfaction

For a habit and a bucket, let `v` be the rollup of that bucket's entries.

- If `v` is not `None`, the bucket is **satisfied** when the comparator holds: `at_least` → `v >= target_value`, `at_most` → `v <= target_value`, `exactly` → `v == target_value`.
- If `v` is `None` (nothing recorded), the bucket is satisfied only when the comparator is `at_most`. Recording nothing cannot exceed a ceiling, so a coffee-free day satisfies "at most 1 coffee"; a run-free week fails "at least 3 runs".

A consequence worth knowing: `exactly 0` is never satisfied by an empty bucket. Express that commitment as `at_most 0`.

A bucket is **scheduled** when all of the following hold:

- its range intersects `[active_from, active_to]` (an edge bucket only partly inside the window still counts, once),
- for `period = day` with a `weekdays` mask, the day's ISO weekday is in the mask,
- its range intersects `[…, as_of]` — future buckets are not scheduled yet.

Unscheduled buckets are invisible to every habit computation: they do not break streaks and do not appear in adherence denominators. A weekday-masked habit is not failed by its off days.

Breaks change the target a scheduled bucket is judged against (`bucket_target`). Let `total` be the bucket's days and `available` the days not covered by any break:

- `available = 0` → the bucket is **excused**. Like an unscheduled bucket it neither breaks nor extends a streak and is left out of adherence, but it is still shown (as skipped).
- `0 < available < total` and comparator `at_least` → the target scales to `ceil(target_value × available / total)`. Three runs a week with three days away (4 of 7 left) needs `ceil(3 × 4/7) = 2`.
- Otherwise (`at_most`, `exactly`, or no break) the target is unchanged: a ceiling is not loosened by being away.

Each scheduled bucket therefore has one outcome: **satisfied**, **missed**, or **excused** (`bucket_outcome`).

### Streaks

`current_streak(habit, as_of)` counts consecutive satisfied scheduled buckets walking backwards from `as_of`:

1. Start at the bucket containing `as_of`. If it is in progress and already satisfied, count it. If it is in progress and not yet satisfied, skip it without breaking the streak — the period is still open — unless the comparator is `at_most`: a ceiling already crossed cannot recover, so it ends the streak now (a slip today puts a quit habit at 0 clean days).
2. Continue to earlier scheduled buckets, adding one for each satisfied bucket and stepping over excused ones.
3. Stop at the first complete scheduled bucket that is missed, or when the buckets leave the active window.

So a "3 runs per week" habit satisfied for the past four weeks reports a streak of 4 on Monday morning, and 5 once the third run of the current week is logged.

`longest_streak(habit, as_of)` is the longest run of consecutive satisfied scheduled buckets anywhere in the active window up to `as_of`, stepping over excused buckets. The in-progress bucket participates only if it is already satisfied (or, for `at_most`, ends the run once crossed).

### Adherence

`adherence(habit, from_date, to_date)` is `satisfied / judged` over the scheduled, non-excused buckets in the range (`adherence_counts` returns both numbers), counting **complete** buckets only. The in-progress bucket is excluded from both numerator and denominator so that a fresh week cannot drag the ratio down. The result is a float in `0.0 … 1.0`, or `None` when the denominator is zero (nothing was scheduled in the range).

## API

Conventions shared by every endpoint (slugs, `as_of`, errors): [api-conventions](../architecture/api-conventions.md).

| Method   | Path                     | Purpose                                       | Status      |
| -------- | ------------------------ | --------------------------------------------- | ----------- |
| `GET`    | `/habits`                | List habits                                   | implemented |
| `POST`   | `/habits`                | Create a habit (habit-first `name` + `kind` with optional `area`, or over a `metric`); unknown `area` → 404, archived → 400, `area` with `metric` → 400 | implemented |
| `GET`    | `/habits/{slug}`         | Get one habit                                 | implemented |
| `PATCH`  | `/habits/{slug}`         | Update name, target, comparator, weekdays, `active_to`, `time_of_day`, `goal`, `unit` | implemented |
| `DELETE` | `/habits/{slug}`         | Delete a habit and its breaks (entries stay)  | implemented |
| `POST`   | `/habits/{slug}/archive` / `/unarchive` | Retire or restore a habit       | implemented |
| `GET`    | `/habits/{slug}/detail`  | Habit, status, breaks, and recent check-ins   | implemented |
| `POST`   | `/habits/{slug}/checkins` | Check in (`amount`, `on`, `note`; optional `as_of`) | implemented |
| `DELETE` | `/habits/{slug}/checkins/last` | Undo the day's latest check-in (`on`, `as_of`) | implemented |
| `GET`    | `/habits/{slug}/breaks`  | List skips and pauses                         | implemented |
| `POST`   | `/habits/{slug}/breaks`  | Skip a day or pause a range (`start_on`, `end_on`, `note`) | implemented |
| `DELETE` | `/habits/{slug}/breaks/{break_id}` | Remove a skip or pause              | implemented |
| `GET`    | `/habits/{slug}/status`  | Streaks and adherence for a habit             | implemented |
| `PUT`    | `/habits/{slug}/days/{day}` | Confirm or clear a bool habit on a day (`{done}`, optional `as_of`) | implemented |
| `GET`    | `/views/habits`          | Frequency-grouped statuses, scheduled/satisfied counts, 7/30-day completion | implemented |
| `GET`    | `/views/habits/calendar` | Day / week / month history grid (`period`, `as_of`) | implemented |

Service functions (in `src/atlas/services/`, each taking an explicit `Session` first; see [overview](../architecture/overview.md#services)):

| Function | Role |
| -------- | ---- |
| `create_habit` / `list_habits` / `get_habit` / `update_habit` / `archive_habit` / `unarchive_habit` / `delete_habit` / `habit_status` / `habit_detail` / `habit_statuses` / `habits_board` / `set_habit_day` | Habits. `create_habit` is habit-first (see Habit, optional `area_slug`) or takes an existing metric; slug defaults from the name. `update_habit` may change name, target, comparator, weekdays, `active_to`, time of day, goal, and (for its own metric) unit; a quit habit's target and comparator are fixed. `archive_habit` hides a habit from boards; `delete_habit` removes it and its breaks, keeps its entries, and archives a metric it made in the `habits` area (a metric in a user-chosen area stays active, so that area keeps its data). `set_habit_day(slug, day, done)` is the Home confirm toggle for **bool** metrics only. `habit_status` returns the habit's `kind` and `weekdays`, current/longest streak, adherence from `active_from` to `as_of`, the current bucket's rollup and range, `days_left`, `effective_target` (scaled, or `None` when excused), `excused`, `skipped_today`, `today_value`, and `last_entry_on`. `habit_detail` adds the breaks and the 30 latest check-ins. `habit_statuses` is every non-archived habit whose metric and area are active. `habits_board` groups those by frequency, counts non-excused scheduled/satisfied current buckets, and pools `adherence_counts` over the last 7 and 30 days (`completion_7d` / `completion_30d`). |
| `check_in` / `undo_check_in` | Habit check-ins. `check_in(slug, amount, on, note)` marks a `check` habit done (idempotent per day), adds `amount` to a count or duration (count and quit default to 1), or logs a slip on a quit habit; future days are rejected. `undo_check_in` deletes the day's latest entry (every entry for a bool habit). Both write ordinary entries and return the habit status. |
| `add_habit_break` / `list_habit_breaks` / `delete_habit_break` | Skips and pauses. `add_habit_break(slug, start_on=today, end_on=start_on, note)`. |
| `habit_calendar` / `area_view` / `goals_board` / `habits_board` | Review. `habit_calendar` is one row per active habit (carrying its `kind` and sorted `weekdays`) with one cell per local date in `bucket_for(as_of, period)` (day / week / month), using the same scheduled / value / satisfied rules as the week grid; a day inside a break is `excused` (shown as skipped, never missed). `area_view` is one area's non-archived metrics (latest day's rollup), habits, and non-abandoned goals **tagged** with that area. `goals_board` is the north-star board: three horizon columns plus this week's linked tasks. `habits_board` is summary counts plus statuses grouped by habit frequency. |

## Screens

`/habit` is the time-window habit board: Day / Week / Month selects the calendar from `GET /views/habits/calendar` (default week, `?period=` / `?on=` like Screen). Every habit stays listed with a frequency tag from `frequencyLabel` (`web/src/lib/habits.ts`): a daily habit reads "Every day", "Weekdays" (Mon–Fri), "Weekends" (Sat–Sun), or its days ("Mon, Wed"); a weekly or monthly check habit reads "3× a week" / "2× a month"; a quit habit reads "Every day". The same tag appears on the board cards, the overview grid, habit detail, and the Home grid, streak / adherence / this-bucket stats from `GET /views/habits`, and a log control (bool Mark done, otherwise Log value). `/week` redirects to `/habit?period=week`. Habit detail uses the same period selector on that habit's calendar row.

The **New habit** dialog has an optional **Area** select listing active areas by name, leaving out the internal `habits`, `screen`, and `life` areas (`habitAreaOptions`); it is hidden when there are no such areas, and no choice sends `area: null`. Names are written by people: the form sends the typed name, and the demo seed uses written names ("Morning pushups", "Meditate", "At most one coffee", "Run three times a week", "Deep work on weekdays", "Call family", "No doomscrolling"), not names built from slugs.

Route inventory with status: [navigation](../product/navigation.md).

## Tests

- `tests/domain/test_habits.py`
- `tests/services/test_habits.py`, `tests/services/test_habit_tracker.py`, `tests/services/test_views.py`
- `tests/api/test_habits.py`, `tests/api/test_habit_tracker.py`, `tests/api/test_views.py`
- `tests/services/test_seed.py` (habit names are written, not derived)
- `web/src/lib/habits.test.ts`, `web/src/lib/habitsSummary.test.ts`
- `web/src/components/habits/HabitFormDialog.test.tsx` (Area select lists only user areas; typed name and area are sent)

## Status

Implemented.
