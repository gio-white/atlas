# Habits

## Purpose

Things you want to do (or stop doing) on a schedule. Each habit is either **ticked by you** or
**read from your data** (sleep, screen time, planned sessions). Day results, streaks, and
percentages are computed when a page loads, never stored. The full product brief is
[habits-brief.md](../plans/habits-brief.md); the working plan and the owner's decisions are in
[habits-plan.md](../plans/habits-plan.md).

## Concepts

- **Habit** — a name, a time of day, a first day, and a rule. It no longer points at a metric.
- **Rule** — how often (every day, specific days, N× a week, N× a month) and how it is checked
  (you tick it, or from your data: a source, a threshold, a value). A rule is stored as
  **versions**, each with a start date; every day is judged by the version in force that day.
- **Manual habit** — ticked by you. Anything a device or Atlas cannot measure (coffee, pushups)
  is manual (owner, 2026-11-14). A day without a tick is Not done.
- **Data habit** — read from a **source** in the registry (`src/atlas/domain/habit_sources.py`).
  An answer you set on a day ("Set by you") wins over the data.
- **Mark** — your answer for one day: `done` or `not_done`. On a manual habit only `done` is
  stored (a tick); on a data habit either is.
- **Freeze** — a date range in which one habit, or every habit, is not judged (holiday, illness).
  Replaces skips and pauses.
- **Archive / Restore / Delete** — archive hides a finished habit and keeps its history; restore
  brings it back; delete removes it with its history.
- **Supports** — a habit can support quest items at any level: an ambition, goal, milestone, side
  quest, chapter, or task. The link is informational and never changes a quest's progress.

## Data model

Schema 15 ([migrations](../architecture/migrations.md)). Enum columns store member names.

### Habit

| Field         | Type            | Notes                                                        |
| ------------- | --------------- | ------------------------------------------------------------ |
| `id`          | int             | primary key                                                  |
| `slug`        | str             | unique; from the name unless given                           |
| `name`        | str             | written by a person                                          |
| `time_of_day` | enum            | `morning \| afternoon \| evening \| anytime`; groups lists   |
| `first_day`   | date            | local; no day before it can be answered                      |
| `archived_at` | datetime \| None | UTC; set by Archive, cleared by Restore                     |
| `created_at`  | datetime        | UTC                                                          |

Name and time of day are not versioned: a change shows everywhere at once.

### HabitRule

Table `habit_rule`: one row per rule version.

| Field        | Type             | Notes                                                                    |
| ------------ | ---------------- | ------------------------------------------------------------------------ |
| `id`         | int              | primary key                                                              |
| `habit_id`   | int              | FK to `Habit`, RESTRICT, indexed                                         |
| `starts_on`  | date             | local; unique per habit (`ux_habit_rule_habit_starts_on`)                |
| `frequency`  | enum             | `every_day \| specific_days \| times_a_week \| times_a_month`            |
| `weekdays`   | list[int] \| None | ISO weekdays (Mon=1 … Sun=7), sorted; only for `specific_days`; JSON, NULL when empty |
| `times`      | int \| None       | 1–7 a week, 1–31 a month; only for `times_a_*`                           |
| `check`      | enum             | `manual \| data`                                                         |
| `source`     | enum \| None      | a data habit's source (below)                                            |
| `source_ref` | str \| None       | the screen category or app slug, for sources that need one              |
| `threshold`  | enum \| None      | `at_least \| at_most \| before \| after`                                 |
| `value`      | float \| None     | minutes, or minutes after midnight for a time of day                    |
| `created_at` | datetime         | UTC                                                                      |

CHECK constraints: `ck_habit_rule_check_fields` (a manual rule has no `source`, `source_ref`,
`threshold`, or `value`; a data rule has `source`, `threshold`, and `value`) and
`ck_habit_rule_frequency_fields` (`weekdays` only for specific days, `times` only for N× a week
or a month).

### HabitMark

Table `habit_mark`: `id`, `habit_id` (FK, RESTRICT, indexed), `day` (local date), `result`
(`done \| not_done`), `created_at` (UTC). One per habit and day (`ux_habit_mark_habit_day`).

### HabitFreeze

Table `habit_freeze`: `id`, `habit_id` (FK, RESTRICT, indexed; **NULL means every habit**),
`start_on` and `end_on` (local, inclusive; `ck_habit_freeze_end_after_start`), `reason`
(optional text), `created_at` (UTC). Overlapping freezes are allowed.

### HabitSupport

Table `habit_support` (schema 14): one row per quest item a habit supports
([decision 0009](../decisions/0009-habits-support-quest-items-at-any-level.md)). Each row points at
exactly one quest item through its own foreign key, so every link is a real reference.

| Field           | Type          | Notes                                                       |
| --------------- | ------------- | ----------------------------------------------------------- |
| `id`            | int           | primary key                                                 |
| `habit_id`      | int           | FK to `Habit`, RESTRICT, indexed                            |
| `ambition_id`   | int \| None   | FK to `Ambition`, RESTRICT, indexed                         |
| `goal_id`       | int \| None   | FK to `Goal`, RESTRICT, indexed                             |
| `milestone_id`  | int \| None   | FK to `Milestone`, RESTRICT, indexed                        |
| `side_quest_id` | int \| None   | FK to `SideQuest`, RESTRICT, indexed                        |
| `chapter_id`    | int \| None   | FK to `Chapter`, RESTRICT, indexed                          |
| `task_id`       | int \| None   | FK to `Task`, RESTRICT, indexed                             |
| `created_at`    | datetime      | UTC                                                         |

`ck_habit_support_one_item`: exactly one of the six item columns is set. A partial unique index
per column (`ux_habit_support_<column>` on `habit_id` and that column, where it is not null) makes
a habit support an item at most once.

## Rules and calculations

### Sources

`SOURCES` in `src/atlas/domain/habit_sources.py`, one entry per source. Each has a picker label,
the subject of its rule line, the fact store it reads (`feed`: sleep, screen, or sessions), its
measure (minutes, or a time of day), the thresholds it allows, and a default threshold and value.

| Source             | Rule line                              | Thresholds        | Default         |
| ------------------ | -------------------------------------- | ----------------- | --------------- |
| `wake_time`        | Wake time before 07:00                 | before, after     | before 07:00    |
| `bedtime`          | Bedtime before 23:00                   | before, after     | before 23:00    |
| `time_asleep`      | Time asleep at least 7h                | at least, at most | at least 7h     |
| `screen_bad_apps`  | Bad apps at most 1h 30m                | at least, at most | at most 1h 30m  |
| `screen_category`  | Screen time in Social at most 1h       | at least, at most | at most 1h      |
| `screen_app`       | Screen time in Instagram at most 30m   | at least, at most | at most 30m     |
| `screen_total`     | Screen time at most 3h                 | at least, at most | at most 3h      |
| `sessions_planned` | A session planned before 12:00         | before            | before 12:00    |

Bedtime is compared on an evening-to-morning scale that starts at 18:00
(`EVENING_SCALE_START`), so 00:40 is later than 23:30. `screen_category` and `screen_app` need
`source_ref`, an active category or app. Adding a source means a `HabitSource` member, an entry
here, and (phase 2) a reader that returns the day's value and whether the day is complete.

### Validating a rule

`validate_rule` (in `services/habits.py`) refuses, with a 400:

- specific days with no day, or a day outside 1–7; days on any other frequency;
- `times` outside 1–7 (a week) or 1–31 (a month), or `times` on a daily frequency;
- a manual rule with any data field;
- a data rule without a source, with a threshold the source does not allow, a time outside
  00:00–23:59, minutes outside (0, 24h], a missing, unknown, or archived category or app, or a
  `source_ref` on a source that takes none.

A data rule without a threshold or value takes the source's default. Weekdays are deduplicated
and sorted.

### Rule versions

- **Create** stores one version starting on `first_day` (today when not given).
- **The version for a day** (`rule_on`) is the latest with `starts_on <= day`; a day before the
  first version uses the first.
- **Change from today** (`apply: from_today`, the default) adds a version starting on
  `max(today, first_day)`. A second change on the same day replaces that day's version. A rule
  equal to the one in force stores nothing.
- **Change to all days** (`apply: all_days`) replaces every version with one starting on
  `first_day`.
- Marks and freezes are never changed by a rule change. How each change re-judges past days is
  the "Rule changes" table in [habits-plan.md](../plans/habits-plan.md#rule-changes) (phase 2
  computes it).

### Answering a day

- `set_habit_day(slug, day, result)` refuses a future day and a day before `first_day`.
- On a manual habit (by the version in force that day), `done` stores a tick and `not_done`
  removes it: a day without a tick is Not done, so nothing is stored for it.
- On a data habit, either answer is stored and wins over the data.
- `clear_habit_day` removes the answer for a day (untick, or "Use data again"); nothing to remove
  is fine.

### Freezes, archive, restore, delete

- `add_freeze` covers one habit (`habit_slug`) or every habit (none); one day when no end is
  given, today when neither date is. The end may not be before the start.
- `list_freezes` is newest first; for a habit, its own freezes and those for every habit.
- **Archive** sets `archived_at`; archiving twice is a 400. **Restore** clears it and freezes the
  days it was archived: a freeze from the archived local date (not before `first_day`) to
  yesterday, reason "Archived" (`ARCHIVED_REASON`), so a restored habit does not come back with
  broken streaks. Restoring on the day it was archived adds none.
- **Delete** removes the habit's rule versions, marks, own freezes, and quest links. Freezes for
  every habit stay.

### Day results, streaks, and Habits kept

Not computed yet: brief phase 2 adds the day result (Done, Not done, Frozen, waiting for data),
the period figure, streaks, "Kept, last 4 weeks", and Habits kept. Until then Habits kept on Home
and Stats → This week reads "—" (`habits_judged` is 0).

Screen-time caps still use the old bucket functions in `src/atlas/domain/habits.py`
(`HabitSpec`, `current_streak`, `adherence`) through `ScreenBudgetSpec.as_habit()`
([screen time](screen-time.md)); no habit uses them.

### Converting a schema 14 habit

`convert_legacy_habit` (`src/atlas/domain/habit_migration.py`, pure) is shared by the schema 15
migration and by importing an export written before schema 15:

- A **daily** habit on a screen app's minutes, at least or at most (not quit), becomes a data
  habit on `screen_app` with the same threshold and value, and keeps no marks.
- Every other habit becomes **manual**. Daily habits keep their days (`specific_days` or
  `every_day`; a quit habit is every day). Weekly or monthly "at least N" becomes N× a week or a
  month (rounded up, 1–7 or 1–31). Weekly or monthly "at most" or "exactly" becomes every day.
- Its past becomes one **Done mark** per scheduled day, outside breaks, up to today (or its end
  date) that the old rule met: a check habit, a day with a yes; quit, a day without a slip (not
  today); a daily amount, a day that met the target (an "at most" day with nothing logged is Done,
  not today); weekly or monthly "at least", a day with anything logged; weekly or monthly "at
  most" or "exactly", a day on which the period's running total was still within the target (not
  today).
- Skips and pauses become freezes for that habit, with the note as the reason. A habit whose end
  date has passed is archived. The metric it read is archived (entries stay) unless it backs a
  screen app.

### Quest links

`src/atlas/services/habit_supports.py`. A link says "this habit supports that quest item". It is
informational: no quest rule reads `habit_support` (`QuestIndex` never loads it), so progress,
completion and eligibility, weights and weight shares, chapter state, and Next action are the same
with or without links.

- **Any level.** The item is an ambition, goal, milestone, side quest, chapter, or task (`kind` +
  `id`, the same `QuestKind` values as the quest API). A habit may support several items, at
  several levels, and an item may be supported by several habits.
- **Adding** (`add_habit_support`) refuses an unknown habit or item (404), an archived habit or an
  archived item (400: "restore it first"), and a link that already exists (409). Completed items
  can be linked.
- **Removing** (`remove_habit_support`) deletes one link (404 if there is none). An archived habit
  keeps its links and can still remove them.
- **From the habit** (`list_habit_supports`): every item it supports, ambitions first, then goals,
  milestones, side quests, chapters, and tasks, each by title, with the item's `path` (its
  ancestors from the root, as on tasks) and `archived`.
- **From the item** (`habits_supporting`): the habits linked to the item itself (`direct: true`)
  and to every item under it, at any depth (`direct: false`), each with its `check` (manual or
  data, by today's rule). One row per link, each naming the item it is on (`linked_to`), direct
  links first, then by habit name.
- **Deleting** a habit deletes its links; deleting a quest item (only possible while it is empty,
  or an Inbox task) deletes the links to it. **Promoting** an Inbox task moves its links to the
  item it becomes. Archiving either side keeps the links.

## API

Conventions shared by every endpoint (slugs, errors): [api-conventions](../architecture/api-conventions.md).
A rule is `{frequency, check, weekdays, times, source, source_ref, threshold, value}`; the
response adds `starts_on` and `source_ref_name` (the category's or app's name).

| Method   | Path                     | Purpose                                       | Status      |
| -------- | ------------------------ | --------------------------------------------- | ----------- |
| `GET`    | `/habits`                | List habits by name, each with today's rule (`include_archived`, default true) | implemented |
| `POST`   | `/habits`                | Create (`name`, `rule`, optional `slug`, `time_of_day`, `first_day`); 400 when the rule does not fit | implemented |
| `GET`    | `/habits/{slug}`         | One habit with today's rule                   | implemented |
| `PATCH`  | `/habits/{slug}`         | Rename, move to another time of day, or change the rule (`rule`, `apply`: `from_today` or `all_days`) | implemented |
| `DELETE` | `/habits/{slug}`         | Delete a habit with its rule versions, marks, own freezes, and quest links | implemented |
| `POST`   | `/habits/{slug}/archive` | Archive (400 if already archived)             | implemented |
| `POST`   | `/habits/{slug}/restore` | Restore, freezing the archived days (400 if not archived) | implemented |
| `PUT`    | `/habits/{slug}/days/{day}` | Answer a day (`{result: done \| not_done}`); returns `{day, result}`, `result` null when nothing is stored | implemented |
| `DELETE` | `/habits/{slug}/days/{day}` | Remove the day's answer (untick, or Use data again) | implemented |
| `GET`    | `/freezes`               | Freezes newest first; `habit` narrows to its own and every-habit ones | implemented |
| `POST`   | `/freezes`               | Freeze one habit (`habit`) or every habit, `start_on`, `end_on`, `reason` | implemented |
| `DELETE` | `/freezes/{freeze_id}`   | Remove a freeze (404 if there is none)        | implemented |
| `GET`    | `/habits/{slug}/supports` | The quest items the habit supports: `kind`, `id`, `title`, `path` (`[{kind, id, title}]`), `archived`, `created_at` | implemented |
| `POST`   | `/habits/{slug}/supports` | Link the habit to a quest item (`{kind, id}`; `kind` is `ambition`, `goal`, `milestone`, `side_quest`, `chapter`, or `task`); 201 with the item; 400 archived, 404 unknown, 409 already linked | implemented |
| `DELETE` | `/habits/{slug}/supports/{kind}/{item_id}` | Remove one link (404 if there is none) | implemented |

Removed in schema 15: `/habits/{slug}/status`, `/detail`, `/checkins`, `/checkins/last`,
`/breaks`, `/unarchive`, `GET /views/habits`, and `GET /views/habits/grid`.

Service functions (in `src/atlas/services/`, each taking an explicit `Session` first; see [overview](../architecture/overview.md#services)):

| Function | Role |
| -------- | ---- |
| `create_habit` / `list_habits` / `get_habit` / `update_habit` / `archive_habit` / `restore_habit` / `delete_habit` | Habits (`services/habits.py`). `create_habit(name, rule, slug, time_of_day, first_day)`; `update_habit(slug, name, time_of_day, rule, apply, today)`. |
| `habit_rules` / `rule_on` / `habit_view` / `validate_rule` / `rule_input` | Rule versions oldest first, the version for a day, a habit with today's rule and its category or app name, the rule check with source defaults, a stored version as a `RuleInput`. |
| `set_habit_day` / `clear_habit_day` / `habit_marks` | Answers for a day. |
| `add_freeze` / `list_freezes` / `delete_freeze` / `freeze_habit_slug` | Freezes. |
| `list_habit_supports` / `add_habit_support` / `remove_habit_support` / `habits_supporting` | Quest links (`src/atlas/services/habit_supports.py`), see [Quest links](#quest-links). |

## Screens

**Temporary, until brief phases 3–5.** `/habits` (`web/src/pages/HabitsPage.tsx`) is a read-only
list: active habits grouped Morning, Afternoon, Evening, Anytime, each with its name and one line
from `ruleSummary` (`web/src/lib/habits.ts`), then the Archived ones. The line is how often ·
how it is checked · time of day (left out for Anytime): "Every day · From your data: wake time
before 07:00 · Morning", "Weekdays · You tick it", "3× a week · You tick it". How often reads
"Every day", "Weekdays", "Weekends", the days ("Mon, Wed, Fri"), "3× a week", or "2× a month". A
data rule's line uses minutes as "1h 30m" and times as "07:00", and keeps Bad, Good, and Neutral capitalised
("From your data: Bad apps at most 1h 30m").

Nothing can be ticked, created, or edited in the app until the Day screen and the habit sheet
arrive; the API above already supports it. `/habit`, `/habit/:slug`, and `/week` redirect to
`/habits`. Home's Habits block lists today's habits the same way ([home](home.md#screens)), and
Stats → This week lists active habits by name.

The demo seed (`atlas seed`) shows every kind of rule: ticked every day (Meditate, One coffee at
most, No doomscrolling), on weekdays (Morning pushups, Deep work), 3× a week (Run, changed from
2× eleven days ago), 2× a month (Call family), and from data (Wake up early: wake time before
07:00; Plan the day: a session planned before 12:00 on weekdays; Keep Bad apps short: Bad apps at
most 1h 30m; Instagram under half an hour: Instagram at most 30m), plus one archived habit (Read
before bed), a three-day Holiday freeze for every habit, and a one-day Travel day freeze on
Meditate. Manual habits carry Done marks on the days the demo person did them.

Route inventory with status: [navigation](../product/navigation.md).

## Tests

- `tests/domain/test_habit_migration.py` — every conversion case for a schema 14 habit
- `tests/db/test_habit_migration.py` — the schema 15 migration of a schema 14 database, once
- `tests/db/test_schema.py`, `tests/db/test_quest_schema.py` — rule constraints, JSON weekdays,
  older databases reaching schema 15
- `tests/services/test_habits.py` — create, validate, rule versions, answers, archive / restore,
  delete, freezes
- `tests/services/test_port.py` — v15 round trip (rules, marks, freezes) and older exports
  converted like the migration
- `tests/services/test_seed.py` — every kind of rule, late-planned sessions
- `tests/api/test_habits.py` — the endpoints above
- `tests/services/test_habit_supports.py` — links at every level, the path from the habit, habits on an item and under it, no progress / weight / Next action change, refusals, removal, deletes and promote, export round trip and replace
- `tests/api/test_habit_supports.py` — read, add, remove at every level; error codes; each item's `/habits`
- `web/src/lib/habits.test.ts`, `web/src/pages/HabitsPage.test.tsx`

## Status

Brief phase 1 of 7: the model, schema 15, the API, and the demo data. Phase 2 computes day results,
streaks, and Habits kept from data; phases 3–5 build the Day and Week screens, the habit page,
and the New habit, Edit, and Freeze sheets; phase 6 Home; phase 7 removes what is left of the
old shape. Quest links have no screen yet.
