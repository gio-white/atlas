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

The time block endpoints are added with the quest services.

## Screens

`/today` and `/calendar` are placeholders in Q1. Q3 of the
[plan](../plans/quests-plan.md#6-screens) builds Today (timeline of today's blocks with
**Session done** and, separately, **Outcome achieved**; unconfirmed blocks; due today; up next),
Calendar (week view, click to create, edit, complete, or cancel), the time-block dialog, the task
drawer's blocks section, and Home's "Today's quests" card, under
`web/src/components/quests/time/`.

## Tests

- `tests/domain/test_quests.py` — planned effort, unconfirmed, session done (criterion 14), overlap
- `tests/db/test_quest_schema.py` — `end_at > start_at`, unique external event per provider

## Status

Q1 in progress: table and rules done.
