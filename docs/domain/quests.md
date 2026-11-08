# Quests

## Purpose

Turn what you want to achieve into concrete work: ambitions, goals, milestones, chapters, and
tasks, plus side quests and an Inbox for quick capture. Levels are optional, structure is never
forced, and every number shown (progress, completion eligibility, chapter state, next action) is
computed on read from stored decisions. Replaces the old goals, milestones, and tasks
([decision 0006](../decisions/0006-quest-model-replaces-goals-and-tasks.md)). Product spec:
[quests brief](../plans/quests-brief.md); how it lands in Atlas: [quests plan](../plans/quests-plan.md).
Scheduling (time blocks) is in [time blocks](time-blocks.md).

## Concepts

- **Ambition** — a broad direction ("Become a better software engineer"). May have no goals and
  may never be completed. Contains goals and direct tasks.
- **Goal** — a concrete outcome ("Move to Copenhagen"), optionally under one ambition. Contains
  milestones and direct tasks. Has an optional due date and a success description.
- **Milestone** — an important intermediate result inside exactly one goal. Contains chapters
  and direct tasks at the same time.
- **Side quest** — independent work not tied to a goal ("Tax declaration"). Same shape as a
  milestone: chapters and direct tasks. Has no weight (plan D14).
- **Chapter** — a coherent batch of tasks (about a week of work), in exactly one milestone **or**
  side quest. Its state comes from its tasks; it is never completed by hand.
- **Task** — one outcome to achieve ("Understand Rust ownership"), never a time commitment. Has
  at most one parent: an ambition, goal, milestone, chapter, or side quest.
- **Main quest** (derived) — a goal and everything under it. An ambition alone is not a main
  quest.
- **Side quests view** (derived) — side quests plus **standalone tasks** (no parent, organized).
- **Inbox** (derived) — tasks with no parent and no `organized_at`. Organizing a task stamps
  `organized_at` and, unless it is made standalone, sets its one parent; the task keeps its id,
  status, history, and time blocks.
- A task directly under an ambition shows under that ambition; it is neither a main quest nor a
  side quest (plan D7).

Supported shapes (brief Part 4): Ambition → Goal → Milestone → Chapter → Task, and every shape
with levels left out (Ambition → Task, Goal → Task, Goal → Milestone → Task, Side quest →
Chapter → Task, Side quest → Task, standalone task). Nothing is created automatically.

## Data model

Tables since schema 11 ([migrations](../architecture/migrations.md)). Times are UTC; `*_on`
columns are local dates in `ATLAS_TZ`. Every foreign key is `ON DELETE RESTRICT` and indexed.
Enum columns store member names (`ACTIVE`, `IN_PROGRESS`, …); the API speaks lowercase values.

### Containers: `ambition`, `goal`, `milestone`, `side_quest`

Common fields:

| Field          | Type             | Notes                                                       |
| -------------- | ---------------- | ----------------------------------------------------------- |
| `id`           | int              | primary key; the wire key                                   |
| `title`        | str              |                                                             |
| `description`  | str \| None      |                                                             |
| `weight`       | float \| None    | relative to siblings; `None` counts as 1 (not on side quests) |
| `position`     | int              | order among siblings; new rows go last                      |
| `status`       | enum             | `active \| completed \| archived`                           |
| `completed_at` | datetime \| None | set by an explicit complete, cleared by reopen              |
| `archived_at`  | datetime \| None | set with status `archived`                                  |
| `created_at`, `updated_at` | datetime |                                                    |

Extra fields: `ambition.target_on` (date); `goal.ambition_id` (optional FK), `goal.due_on`,
`goal.success_description`; `milestone.goal_id` (required FK), `milestone.due_on`;
`side_quest.due_on`.

Archiving keeps `completed_at`: unarchiving returns the item to `completed` if it has one,
else `active`.

### `chapter`

| Field           | Type             | Notes                                                    |
| --------------- | ---------------- | -------------------------------------------------------- |
| `id`            | int              | primary key                                              |
| `milestone_id`  | int \| None      | FK `milestone`                                           |
| `side_quest_id` | int \| None      | FK `side_quest`                                          |
| `title`, `description`, `weight`, `position` | |                                       |
| `archived_at`   | datetime \| None |                                                          |
| `created_at`, `updated_at` | datetime |                                               |

`CHECK ck_chapter_one_parent`: exactly one of `milestone_id` / `side_quest_id` is set. A
chapter has no stored status.

### `task`

| Field              | Type             | Notes                                                      |
| ------------------ | ---------------- | ---------------------------------------------------------- |
| `id`               | int              | primary key                                                |
| `title`            | str              | the only required field (Inbox capture)                    |
| `description`      | str \| None      |                                                            |
| `status`           | enum             | `todo \| in_progress \| completed`                         |
| `priority`         | enum             | `low \| normal \| high` (plan D17)                         |
| `estimate_minutes` | int \| None      | estimated effort, > 0                                      |
| `due_on`           | date \| None     |                                                            |
| `weight`           | float \| None    | relative to siblings; `None` counts as 1                   |
| `position`         | int              | order among siblings                                       |
| `ambition_id`, `goal_id`, `milestone_id`, `chapter_id`, `side_quest_id` | int \| None | at most one is set |
| `organized_at`     | datetime \| None | indexed; empty with no parent = Inbox                      |
| `started_at`       | datetime \| None | first time the task left `todo`                            |
| `completed_at`     | datetime \| None |                                                            |
| `archived_at`      | datetime \| None |                                                            |
| `created_at`, `updated_at` | datetime |                                                     |

CHECK constraints: `ck_task_at_most_one_parent`; `ck_task_parent_is_organized` (a parent implies
`organized_at`); `ck_task_completed_at` (`status = completed` ⇔ `completed_at` set);
`ck_task_estimate_positive`.

Time blocks belong to tasks: [time blocks](time-blocks.md#data-model).

**Deleting:** a container only when it has no children at all (archive it otherwise); a task
only from the Inbox and only without time blocks. The RESTRICT foreign keys back this up.

## Rules and calculations

The rules are pure functions in `src/atlas/domain/quests.py`; see the next commits of this
branch for their definitions.

## API

The quest endpoints are added with the quest services.

## Screens

The sidebar's **Quests** group links Today, Inbox, Main quests, Side quests, and Calendar. In Q1
every quest route is a placeholder page ("Coming soon" plus one line on what will show). Q2 of
the [plan](../plans/quests-plan.md#6-screens) builds Main quests (`/quests`), Ambition
(`/quests/ambitions/:id`), the goal quest map (`/quests/goals/:id`), Side quests
(`/side-quests`), Side quest (`/side-quests/:id`), Inbox (`/inbox`), and the task drawer, with
shared components in `web/src/components/quests/`. Route inventory:
[navigation](../product/navigation.md).

## Tests

- `tests/db/test_quest_schema.py` — constraints, RESTRICT foreign keys, v10 → v11 migration
- `tests/services/test_port.py` — quest export/import, v10 exports

## Status

Q1 in progress: schema 11 and export/import done.
