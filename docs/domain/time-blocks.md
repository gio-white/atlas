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

The rules are pure functions in `src/atlas/domain/quests.py`; see the next commits of this
branch for their definitions.

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

- `tests/db/test_quest_schema.py` — `end_at > start_at`, unique external event per provider

## Status

Q1 in progress: table done.
