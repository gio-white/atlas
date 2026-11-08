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

All rules are pure functions in `src/atlas/domain/quests.py` (no session, no clock; `now` is
passed in). The services build a `QuestNode` tree from rows and ask the domain. This is the only
place progress, eligibility, chapter state, and next action are defined.

### Structure (`check_parent`)

| Item | Allowed parent | Parent required |
| ---- | -------------- | --------------- |
| Ambition, Side quest | none | — |
| Goal | ambition | no |
| Milestone | goal | yes |
| Chapter | milestone or side quest | yes |
| Task | ambition, goal, milestone, chapter, or side quest | no (Inbox or standalone) |

- A milestone moves only between goals; a chapter only between milestones and side quests; a
  task between any allowed parents (`POST /tasks/{id}/organize`).
- An archived parent accepts no new or moved children (checked on the direct parent).
- Nothing is created automatically; no level is required.

### Task status (`transition_task`)

- `todo`, `in_progress`, and `completed` may each go to any other (reopen included).
- `started_at` is stamped the first time a task leaves `todo` and never cleared.
- `completed_at` is set when the task becomes `completed` (kept if it already was) and cleared
  when it leaves `completed`.
- Only an explicit action completes a task: a time block never does, reaching 100 % never does.

### Chapter state (`chapter_state`)

Over the chapter's non-archived tasks, in this order:

1. `empty` — no tasks.
2. `completed` — every task is completed.
3. `in_progress` — some task is `in_progress` or `completed`.
4. `not_started` — otherwise.

An empty chapter is never completed (brief P2.4).

### Completion eligibility (`completion_check`, `check_can_complete`)

Children are the non-archived direct children: Ambition → goals and direct tasks; Goal →
milestones and direct tasks; Milestone and Side quest → chapters and direct tasks; Chapter →
tasks. A child is **done** when it is a completed task, a completed container (stored status,
manual or not), or a chapter whose state is `completed`.

- **Eligible** = at least one child and every child done. `open_children` lists the rest in
  tree order. The item's own status is ignored, so a completed item still reports its open
  children.
- Completing is always explicit (`POST …/complete`). An item that is not eligible needs
  `override: true`; without it the request is refused (409) with the open children named. An
  empty container also needs `override`.
- After an override the children keep their statuses and the item reads
  `completed_with_open_items: true` (completed and has open children); the UI shows it.
- Chapters are never completed by hand; archived items cannot be completed.
- Reopening clears `completed_at` and returns the status to `active`.

### Progress (`progress`)

```text
progress(task)      = 1 if completed else 0          (in_progress counts 0, plan D10)
progress(container) = 1     if its stored status is completed (manual or not)
                    = None  if it has no non-archived children      → "Not broken down yet"
                    = Σ wᵢ·pᵢ / Σ wᵢ over non-archived children,
                        wᵢ = child.weight or 1,  pᵢ = progress(child), None counted as 0
```

- A chapter has no stored status, so it is always computed from its tasks.
- Weights are relative among siblings (`> 0` when set) and shown normalized as percentages
  (`normalized_weights`, returned as `weight_share`). Side quests have no weight; their children
  do.
- `done_tasks` / `total_tasks` count the non-archived tasks under an item, skipping archived
  containers (`task_counts`).

### Tree order

Inside a container, child containers come first, then direct tasks; each group is ordered by
`position`, then id (`tree_order`). New items get `position` = last sibling + 1; reordering is a
`PATCH` of `position` (plan D16).

### Next action (`next_action`)

Over the open (not completed), non-archived tasks under the item:

1. The task with the earliest `scheduled` time block that has not ended yet (a session running
   now counts).
2. Otherwise the first `in_progress` task in tree order.
3. Otherwise the `todo` task with the nearest due date (undated last), then higher priority,
   then tree order.
4. Otherwise none; the UI shows an "Add a task" prompt.

Planned effort and unconfirmed sessions are defined in
[time blocks](time-blocks.md#rules-and-calculations).

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

- `tests/domain/test_quests.py` — every rule above, pure (acceptance criteria 14–21)
- `tests/db/test_quest_schema.py` — constraints, RESTRICT foreign keys, v10 → v11 migration
- `tests/services/test_port.py` — quest export/import, v10 exports

## Status

Q1 in progress: schema 11, export/import, and the domain rules done.
