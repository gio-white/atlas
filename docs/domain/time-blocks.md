# Time blocks

## Purpose

Keep scheduling separate from execution. A [task](quests.md) is what you want to achieve; a time
block is when you intend to work toward it. One task can have many blocks. Completing a block
records that a session happened; it never completes the task.

## Concepts

- **Time block** (shown as a session) — a planned interval for one task.
- **Session done** — the block is marked completed. A `todo` task moves to `in_progress`.
- **Outcome achieved** — completing the task itself, a separate explicit action.
- **Cancelled** — the session did not happen; the row is kept.
- **Unconfirmed** (derived) — a block still `scheduled` after its end time.
- **Planned time** (derived) — the sum of non-cancelled block durations; never called actual
  effort.

## Data model

### `time_block`

| Field               | Type          | Notes                                                    |
| ------------------- | ------------- | -------------------------------------------------------- |
| `id`                | int           | primary key                                              |
| `task_id`           | int           | FK `task`, RESTRICT, indexed                             |
| `start_at`          | datetime      | UTC, indexed                                             |
| `end_at`            | datetime      | UTC                                                      |
| `status`            | enum          | `scheduled \| completed \| cancelled`                    |
| `provider`          | enum          | `internal` (an external calendar later)                  |
| `external_event_id` | str \| None   | for a future calendar sync                               |
| `created_at`, `updated_at` | datetime |                                                   |

`CHECK ck_time_block_end_after_start`: `end_at > start_at`. Unique index
`ux_time_block_provider_external_event` on (`provider`, `external_event_id`) where
`external_event_id` is set. Overlapping blocks are allowed.

## Rules and calculations

Pure functions in `src/atlas/domain/quests.py`. Naive datetimes (as SQLite returns them) are
read as UTC (`as_utc`).

- **Window** (`check_block_window`): `end_at` must be after `start_at`.
- **Scheduling** (`check_can_schedule`): a completed task takes no new blocks until it is
  reopened; an archived task takes none.
- **Planned effort** (`planned_minutes`): Σ (`end_at` − `start_at`) in minutes over the
  non-cancelled blocks of the non-archived tasks under an item, summed up the tree. Shown beside
  the estimate and never called actual effort (brief P6.4).
- **Session done** (`complete_block`): the block becomes `completed`; a `todo` task moves to
  `in_progress` (stamping `started_at`). An `in_progress` or `completed` task is unchanged.
  Nothing else changes (plan D11).
- **Cancel**: the block becomes `cancelled`; the row is kept and the task is unchanged.
- **Unconfirmed** (`is_unconfirmed`): `status = scheduled` and `end_at ≤ now`. Computed, never
  stored (plan D12).
- **Overlap** (`overlapping_ids`): non-cancelled blocks whose intervals intersect another
  non-cancelled block. Allowed; the calendar marks them.
- **Next action** uses blocks: the open task with the earliest `scheduled` block that has not
  ended comes first ([quests](quests.md#next-action-next_action)).

## API

Times in requests may carry any offset and are stored as UTC; responses are UTC. Errors: unknown
block → 404; unknown, completed, or archived task, or `end_at ≤ start_at` → 400.

| Method | Path | Purpose | Status |
| ------ | ---- | ------- | ------ |
| `GET` | `/time-blocks` | List blocks overlapping [`start`, `end`) and/or for `task_id`, oldest first, with `overlaps` | implemented |
| `POST` | `/time-blocks` | Create (`task_id`, `start_at`, `end_at`) | implemented |
| `PATCH` | `/time-blocks/{id}` | Move or resize (`start_at`, `end_at`) | implemented |
| `DELETE` | `/time-blocks/{id}` | Delete a mistaken block (otherwise cancel it) | implemented |
| `POST` | `/time-blocks/{id}/complete` / `/cancel` | Session done (a `todo` task → `in_progress`; never completes the task) / session cancelled | implemented |
| `GET` | `/views/today` | Today's blocks with task and parent path, unconfirmed blocks, tasks due, and "Up next" (`as_of`) | implemented |
| `GET` | `/views/calendar` | Blocks overlapping [`start`, `end`) with task and parent path, overlaps marked | implemented |

A block reads `{id, task_id, start_at, end_at, status, provider, external_event_id, created_at,
updated_at, minutes, unconfirmed, overlaps}`.

**Today** (`today_view`) for the local date `as_of` (default today in `ATLAS_TZ`):

- `blocks` — non-cancelled blocks overlapping that local day, by start, each with its task
  (and the task's `path`).
- `unconfirmed` — every block still `scheduled` after its end, on any day, whose task is not
  archived, oldest first.
- `due_today` — open, non-archived tasks due on or before the date (overdue included), by due
  date.
- `up_next` — the next action of each active goal and side quest (in position order), without
  duplicates and without tasks already on today's timeline.

**Calendar** (`calendar_view`): every block (any status) overlapping [`start`, `end`), by start,
each with its task; `overlaps` marks non-cancelled blocks that intersect another.

Service functions (`src/atlas/services/time_blocks.py`):

| Function | Role |
| -------- | ---- |
| `list_time_blocks` / `get_time_block` / `create_time_block` / `update_time_block` / `delete_time_block` | CRUD. Datetimes are converted to UTC before they are stored or compared. |
| `complete_time_block` / `cancel_time_block` | Session outcome through `complete_block`; the task row changes only when it was `todo`. |
| `today_view` / `calendar_view` | Execution read models (`src/atlas/services/quest_views.py`). |

## Screens

`/today` and `/calendar` are placeholders in Q1. Q3 of the
[plan](../plans/quests-plan.md#6-screens) builds Today (timeline of today's blocks with
**Session done** and, separately, **Outcome achieved**; unconfirmed blocks; due today; up next),
Calendar (week view, click to create, edit, complete, or cancel), the time-block dialog, the task
drawer's blocks section, and Home's "Today's quests" card, under
`web/src/components/quests/time/`.

## Tests

- `tests/domain/test_quests.py` — planned effort, unconfirmed, session done (criterion 14), overlap
- `tests/services/test_time_blocks.py` — CRUD, UTC conversion, session done and cancel, overlaps, Today (local day, unconfirmed, due, up next), Calendar
- `tests/api/test_quests.py` — time block endpoints, Today, Calendar
- `tests/db/test_quest_schema.py` — `end_at > start_at`, unique external event per provider

## Status

Q1 done (backend, typed client, seed); Today and Calendar are placeholders until Q3.
