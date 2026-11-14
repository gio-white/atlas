# Habits rebuild: plan

The working plan for [habits-brief.md](habits-brief.md). It records what exists today, how each
habit migrates, which files each phase touches, and the questions that must be answered before
phase 1. Phase 1 (the model, schema 15, the API, and the demo data) is built; the rest is not.

## What exists today

- **Model.** A `habit` row points at a **metric** (`metric_id`) and stores `kind` (check, count,
  duration, quit), `period` (day / week / month), `weekdays`, `comparator` (at least / at most /
  exactly), `target_value`, `active_from` / `active_to`, `time_of_day`, and `archived_at`. Its
  facts are **entries** on that metric. A check habit is a yes/no metric; a quit habit gets its
  own `habit`-origin metric that counts slips.
- **Skips and pauses** are one table, `habit_break` (`start_on`, `end_on`, `note`); a skip is a
  one-day break. A break excuses a bucket and scales an at-least weekly or monthly target
  (`bucket_target`, already `ceil(N × open ÷ total)`).
- **Calculations** (`src/atlas/domain/habits.py`): bucket outcome from the summed entries,
  current and longest streak, adherence. "Habits kept" (`pooled_adherence_counts`) is satisfied
  over judged buckets, pooled.
- **API** (`src/atlas/api/routers/habits.py`, `views.py`): CRUD, archive, `status`, `detail`,
  `PUT /days/{day}` (yes/no only), `POST /checkins` and `DELETE /checkins/last` (Log value and
  undo), `breaks`, `supports`; `GET /views/habits` (board) and `GET /views/habits/grid`.
- **Screens.** `/habit` (`HabitsPage`: today's cards plus a week or month grid), `/habit/:slug`
  (`HabitPage`), `HabitCard`, `HabitFormDialog`, `BreakDialog`, `WeekGrid`, the Home block
  `HabitsTodayBlock`, and the habit rows on Stats → This week.
- **Already in place for the brief.** Sleep `occurred_on` is the local wake date, so "a night
  belongs to the day you wake up" holds. Sessions (`time_block`) have stored `created_at` since
  the table was made, so Sessions planned needs no new field. Screen devices exist but have no
  "complete up to" time.

## Demo habits and how each migrates

Real data does not matter (owner, 2026-11-14): the demo database (`atlas seed`) is the reference,
and the new seed shows every kind of rule. Habits that no device or Atlas feature can measure
(coffee, pushups) are **ticked by you**; only automatic sources (sleep, screen time, sessions)
make a data habit. There is no "Your entries" source.

| Habit | Today | Becomes |
| ----- | ----- | ------- |
| Morning pushups | count, at least 40 a day, Mon–Fri | Ticked by you, Mon–Fri. A past day is Done when 40 or more were logged |
| Meditate | check, every day; 1 skip ("Travel day") | Ticked by you, every day. A day with a yes is Done; the skip becomes a one-day freeze, reason "Travel day" |
| At most one coffee | count, at most 1 a day | Ticked by you, every day. A past day is Done when 1 or fewer were logged; nothing logged counts as 0, so Done |
| Run three times a week | count, at least 3 a week | Ticked by you, 3× a week. A day with a run is Done (two runs on one day count once) |
| Deep work on weekdays | duration, at least 1h 30m a day, Mon–Fri | Ticked by you, Mon–Fri. A past day is Done when 1h 30m or more was logged |
| Call family | check, 2× a month | Ticked by you, 2× a month. A day with a yes is Done |
| No doomscrolling | quit, no slips | Ticked by you, every day. A past day with no slip is Done; today stays open |

The schedule becomes the first rule version, starting on the habit's first day. Pauses become
freezes over the same range. The metrics these habits used are **archived**: they leave the New
entry list, their entries stay readable in All entries, and they can be restored. Quest links
stay.

The new demo adds the brief's data habits: Wake up before 07:00 (sleep), Bad apps at most
1h 30m (screen time), and Plan the day (a session planned before 12:00).

## Decisions so far

| # | Question | Decision |
| - | -------- | -------- |
| 1 | Real data | Use generated demo data; the real database is not migrated by hand |
| 2 | Nothing recorded | Habits that cannot be measured automatically are ticked by you. For data habits, see the open question below |
| 3 | Weekly and monthly habits on single days | A day without a tick is blank, never a cross; the period figure ("2 of 4 this week") carries the judgment. The habit counts in "x of y done" every day of its period |
| 4 | Finished habits | Archive hides a habit and keeps its history; Restore brings it back from the Archived list. Delete stays for removing a habit with its history |
| 5 | Logging amounts | Moot: no habit asks for a number, so nothing needs Add → Entry |
| 6 | The app between phases | Phase 1 swaps the old Habits screens and Home block for a temporary read-only list, so the app runs and nothing writes the old shape |
| 7 | Screen-time "complete up to" | Set by whatever brings screen-time data in (the import file, the screen-time API the future pipeline will call) and by the demo data. No new command |
| 8 | Rule changes | See "Rule changes" below |
| 9 | Addresses | `/habits` (Day), `/habits/week` (Week), `/habit/:slug`; `/habit` and `/week` redirect |

## The new model (schema 15)

| Table | Holds |
| ----- | ----- |
| `habit` | `slug`, `name`, `time_of_day`, `first_day`, `archived_at`. Loses `metric_id`, `kind`, `period`, `comparator`, `target_value`, `weekdays`, `active_to` |
| `habit_rule` | One version per edit: `habit_id`, `starts_on`, `frequency` (every day / specific days / times a week / times a month), `weekdays`, `times`, `check` (you tick it / from your data), `source`, `source_ref` (the category or app slug), `threshold` (at least / at most / before / after), `value` (minutes, or minutes after midnight for a time), `created_at` |
| `habit_mark` | `habit_id`, `day`, `result` (done / not done), `created_at`; one per habit and day. A tick on a manual habit; "Set by you" on a data habit |
| `habit_freeze` | `habit_id` (empty = all habits), `start_on`, `end_on`, `reason`, `created_at` |
| `screen_device` | gains `complete_through` (UTC): the time this device's data is complete up to |

`habit_break` is dropped once its rows are freezes. Nothing derived is stored: day results,
streaks, and percentages are computed when a page loads.

Sources live in one registry (`src/atlas/domain/habit_sources.py`): each has a name, its unit
(minutes or time of day), the thresholds it allows, and a reader in the service layer that
returns the day's value plus whether the day is complete. Adding workouts or steps later means
adding one entry and one reader.

## Brief → files

| Brief | Phase | Files |
| ----- | ----- | ----- |
| §1 What a habit is, §2 two checks, §5 rule history and freezes | 1 | `src/atlas/db/models.py`, `src/atlas/db/engine.py` (schema 15 and the data migration), `src/atlas/domain/enums.py`, new `src/atlas/domain/habit_sources.py`, `src/atlas/services/habits.py` (rewritten), `src/atlas/services/port.py` (export and import, older exports converted), `src/atlas/services/seed.py` (demo habits as in the brief's mockup), `src/atlas/services/screen.py` and `src/atlas/api/routers/screen.py` (`complete_through`) |
| §2 sources, §3 missing data, §4 the running day, §6 calculations | 2 | `src/atlas/domain/habits.py` (rewritten: day result, period kept, streaks, kept last 4 weeks, habits kept), new `src/atlas/services/habit_data.py` (reads sleep, screen sessions, and sessions; never writes), `src/atlas/services/week.py` (Habits kept), `tests/domain/test_habits.py` (rewritten with every case in §6), `tests/services/test_habits.py` |
| API for §7–§9 | 2–5 | `src/atlas/api/routers/habits.py`, `src/atlas/api/routers/views.py`, `src/atlas/api/schemas.py`, `src/atlas/api/serialize.py`, `tests/api/` |
| §7 Day tab | 3 | new `web/src/pages/habits/HabitsDayPage.tsx`, `web/src/components/habits/` (WeekStrip, HabitRow, StatusIcon, Streak, RowMenu), `web/src/lib/habits.ts`, `web/src/lib/api.ts`, `web/src/App.tsx`, `web/src/lib/nav.ts` |
| §8 Week tab and habit page | 4 | new `web/src/pages/habits/HabitsWeekPage.tsx`, `web/src/pages/HabitPage.tsx` (rewritten), `web/src/components/habits/HistoryGrid.tsx` |
| §9 New habit, Edit, Freeze | 5 | new `web/src/components/habits/HabitSheet.tsx` and `FreezeSheet.tsx` |
| §10 Home | 6 | `web/src/components/home/HabitsTodayBlock.tsx`, `web/src/components/home/StatusBlocks.tsx`, `web/src/pages/ThisWeekPage.tsx`, `web/src/lib/thisWeek.ts` |
| §11 Remove | 7 | delete `HabitCard.tsx`, `HabitFormDialog.tsx`, `BreakDialog.tsx`, `WeekGrid.tsx`, `web/src/lib/habitsSummary.ts`, `web/src/pages/WeekPage.tsx` (redirect only), the old routes and schemas; then a link check |
| Docs, every phase | 1–7 | `docs/domain/habits.md` (rewritten), `docs/domain/home.md`, `docs/domain/this-week.md`, `docs/domain/screen-time.md`, `docs/domain/sleep.md`, `docs/domain/time-blocks.md`, `docs/domain/trackers-and-entries.md`, `docs/product/navigation.md`, `docs/product/glossary.md`, `docs/product/ux-writing.md`, `docs/architecture/data-model.md`, `docs/architecture/migrations.md`, the code → doc map, decision 0010 (D21–D40), the changelog |

**API after the rebuild.** `GET`/`POST /habits`, `GET`/`PATCH`/`DELETE /habits/{slug}` (`PATCH`
takes `apply`: `from_today` or `all_days`), archive and restore,
`PUT /habits/{slug}/days/{day}` (body `{"result": "done"}` or `"not_done"`), `DELETE /habits/{slug}/days/{day}`
(untick, or Use data again), `GET`/`POST /freezes` and `DELETE /freezes/{id}`,
`GET /habits/sources` (the picker: sources, categories, apps), and the views
`GET /views/habits/day`, `GET /views/habits/week`, `GET /views/habits/{slug}`. Removed:
`status`, `detail`, `checkins`, `breaks`, `GET /views/habits`, `GET /views/habits/grid`.

**Addresses.** Day tab `/habits`, Week tab `/habits/week`, a habit `/habit/:slug`. The old
`/habit` and `/week` redirect to `/habits`. (Keeping `/habit` for the tabs would make a habit
called "week" unreachable.) `GET /habits/{slug}` also matches `/habits/week`, so phase 4 adds
it to `SPA_PATHS_SHADOWED_BY_API` (`src/atlas/api/spa.py`), as phase 1 did for `/habits`.

## Assumptions I will make unless you say otherwise

- **As of.** A past As of date shows that day as "today" at its end: running rules are judged
  as if the day had just ended, with the data stored now.
- **Waiting for data** applies to data habits only. A manual habit left unticked is Not done
  from midnight.
- **Before / After today**: the row is listed with an empty icon and no reason until the value
  arrives.
- **Sessions planned** counts any session on D created before the cut-off, including one created
  the day before. Cancelled sessions do not count; done and "didn't happen" ones do.
- **Screen time completeness** looks at active (not archived) devices only. With no active device
  the day is "No data received". Sessions without a device still add to the totals.
- **Rule versions** cover everything under "How often?" and "How is it checked?" (manual or
  data, source, threshold, value). Two edits on the same day leave one version for that day.
- **Kept, last 4 weeks** counts periods that end inside the last 28 days.
- **Habits kept** for a running week counts finished days plus today once it is Done (so the
  morning does not drag the figure down), and a weekly or monthly habit's target is its whole
  target for that period. The previous week is compared like for like, as on This week today.
- **A freeze for all habits** also covers habits created later that fall inside its dates.
- **Delete** removes the habit's rule versions, marks, own freezes, and quest links.
- **Restore** after archiving: the days the habit was archived are frozen (a freeze with reason
  "Archived" is stored when you restore), so a restored habit does not come back with a broken
  streak.

## Rule changes

A habit's rule is everything under "How often?" and "How is it checked?". Name and time of day
are not versioned and change everywhere at once. Each day is judged by the rule in force that
day; marks (your ticks and "Set by you" answers) are never changed by an edit unless a row below
says so.

| Change | From today | To all past days too |
| ------ | ---------- | -------------------- |
| A new value or threshold (07:00 → 07:30) | Days before today keep their results | Every day is re-judged with 07:30; days set by you keep your answer |
| Another source (wake time → time asleep) | As above | As above |
| How often, daily (every day → Mon–Fri) | Today onward uses the new days | Every day is re-judged; days no longer scheduled drop out |
| How often, a count (3× → 4× a week) | The week that contains today uses 4× | Every week uses 4× |
| Daily ↔ weekly or monthly (every day → 3× a week) | The new rule starts today. The week it starts in is a first, partial period: the days before the change count as not open, so the target is `ceil(3 × open days ÷ 7)` | Every period uses the new rule |
| Ticked by you → from your data | Past ticks stay; from today the data decides, and an answer you set today or later is "Set by you" | The data decides every past day. Ticks stay as "Set by you" and still win; "Use data again" clears one day. The sheet says how many days that is |
| From your data → ticked by you | Past days keep their data results | Past days with an answer you set keep it as a tick; every other past day becomes Not done. The sheet warns before saving |
| Two edits on the same day | The second replaces the first: one version starts today | Replaces every version, as always |
| "From today", later "To all past days too" | | One version from the first day; the earlier versions are gone |

What stays true through any change: streaks and "Kept, last 4 weeks" are computed across versions,
each period with its own rule; freezes are untouched; future days cannot be marked.

## Questions

See the reply in the session; answers are folded in above.
