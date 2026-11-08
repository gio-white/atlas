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

Conventions (integer ids, error codes, filters): [api-conventions](../architecture/api-conventions.md).
Every id is an integer; a task's parent is `parent_kind` (`ambition`, `goal`, `milestone`,
`chapter`, `side_quest`) plus `parent_id`. Errors: invalid or archived parent → 400; unknown id
→ 404; deleting a container with children, deleting a task outside the Inbox or with blocks, or
completing an ineligible item without `override` → 409. Bad shapes (an `estimate_minutes` or
`weight` ≤ 0, an unknown field) → 422.

| Method | Path | Purpose | Status |
| ------ | ---- | ------- | ------ |
| `GET` | `/ambitions` | List ambitions with computed state (`include_archived`) | implemented |
| `POST` | `/ambitions` | Create (`title`, `description`, `target_on`, `weight`, `position`) | implemented |
| `GET` | `/ambitions/{id}` | Read one ambition with computed state | implemented |
| `PATCH` | `/ambitions/{id}` | Edit title, description, `target_on`, weight, position; `archived` | implemented |
| `DELETE` | `/ambitions/{id}` | Delete when it has no children (else 409) | implemented |
| `POST` | `/ambitions/{id}/complete` / `/reopen` | Explicit completion (`{"override": true}` when not eligible); reopen | implemented |
| `GET` | `/goals` | List goals (`ambition_id`, `include_archived`) | implemented |
| `POST` | `/goals` | Create with optional `ambition_id`, `success_description`, `due_on`, `weight` | implemented |
| `GET` | `/goals/{id}` | Read one goal | implemented |
| `PATCH` | `/goals/{id}` | Edit, move to another ambition or none (`ambition_id: null`), archive | implemented |
| `DELETE` | `/goals/{id}` | Delete when empty | implemented |
| `POST` | `/goals/{id}/complete` / `/reopen` | As for ambitions | implemented |
| `POST` | `/milestones` | Create (`goal_id` required) | implemented |
| `GET` | `/milestones/{id}` | Read one milestone | implemented |
| `PATCH` | `/milestones/{id}` | Edit, move to another goal (`goal_id`), archive | implemented |
| `DELETE` | `/milestones/{id}` | Delete when empty | implemented |
| `POST` | `/milestones/{id}/complete` / `/reopen` | As for ambitions | implemented |
| `GET` | `/side-quests` | List side quests (`include_archived`) | implemented |
| `POST` | `/side-quests` | Create (`title`, `description`, `due_on`, `position`; no weight) | implemented |
| `GET` | `/side-quests/{id}` | Read one side quest | implemented |
| `PATCH` | `/side-quests/{id}` | Edit, archive | implemented |
| `DELETE` | `/side-quests/{id}` | Delete when empty | implemented |
| `POST` | `/side-quests/{id}/complete` / `/reopen` | As for ambitions | implemented |
| `POST` | `/chapters` | Create (`milestone_id` xor `side_quest_id`) | implemented |
| `GET` | `/chapters/{id}` | Read one chapter with its computed `state` | implemented |
| `PATCH` | `/chapters/{id}` | Edit, move (give `milestone_id` or `side_quest_id`), archive | implemented |
| `DELETE` | `/chapters/{id}` | Delete when empty | implemented |
| `GET` | `/tasks` | List (`parent_kind` + `parent_id`, `status`, `inbox`, `standalone`, `due_on`, `include_archived`) | implemented |
| `POST` | `/tasks` | Create; only `title` required. No parent → Inbox; `standalone: true` → standalone; `parent_kind` + `parent_id` → organized under it | implemented |
| `GET` | `/tasks/{id}` | Read with its time blocks and planned minutes | implemented |
| `PATCH` | `/tasks/{id}` | Edit title, description, `status`, `priority`, `estimate_minutes`, `due_on`, `weight`, `position`, `archived` | implemented |
| `DELETE` | `/tasks/{id}` | Delete an Inbox task without time blocks (else 409) | implemented |
| `POST` | `/tasks/{id}/organize` | `{parent_kind, parent_id}` or `{standalone: true}`; keeps id, status, blocks | implemented |
| `POST` | `/tasks/{id}/promote` | Inbox task → new `ambition`, `goal`, `side_quest`, `milestone`, or `chapter` (`kind`, `parent_kind`, `parent_id`); returns `{kind, id, title}` | implemented |
| `GET` | `/views/main-quests` | Ambitions (each with goal cards and direct tasks; ambitions without goals included), then independent goals | implemented |
| `GET` | `/views/ambitions/{id}` | One ambition: goals and direct tasks | implemented |
| `GET` | `/views/goals/{id}` | One goal's tree: milestones → chapters → tasks, and direct tasks, with state on every node | implemented |
| `GET` | `/views/side-quests` | Side quests and standalone tasks | implemented |
| `GET` | `/views/side-quests/{id}` | One side quest's tree: chapters → tasks, and direct tasks | implemented |
| `GET` | `/views/inbox` | Inbox tasks, newest first, and `count` | implemented |

The views take `include_archived` (default false). Time blocks, Today, and Calendar are in
[time blocks](time-blocks.md#api).

**Response shapes.** Every container carries its stored fields plus the computed state:
`progress` (0–1 or null), `done_tasks`, `total_tasks`, `planned_minutes`, `eligible`,
`open_children` (`[{kind, id, title}]`), `next_action` (a task or null), `path` (ancestors from
the root), and child counts (`goal_count`, `milestone_count`, `chapter_count`, `task_count`).
Ambitions, goals, milestones, and side quests add `status`, `completed_at`, and
`completed_with_open_items`; goals, milestones, and chapters add `weight_share` (the normalized
weight among siblings); chapters add `state`. A task carries its fields plus `parent`, `path`,
`inbox`, `standalone`, `weight_share`, `planned_minutes`, and `block_count`; `GET /tasks/{id}`
and task writes also return `blocks`.

**Promote rule** (plan D6): only an Inbox task can be turned into something else; title and
description are carried over and the task is deleted. A task with time blocks is refused (400)
with a hint to organize it instead. A goal may name an ambition; a milestone needs a goal; a
chapter needs a milestone or side quest.

Service functions (each takes an explicit `Session` first, and an optional `now` for tests):

| Function | Role |
| -------- | ---- |
| `QuestIndex` | Loads every quest row once, links parents to children, builds `QuestNode` trees, and renders `ContainerView` / `TaskView` with the domain's computed state (`src/atlas/services/quests.py`). |
| `list_containers` / `get_container` / `create_container` / `update_container` / `delete_container` | Container CRUD for any `QuestKind`. Parent columns are validated with `check_parent`; new items go last among their siblings. `archived` sets status and `archived_at`; unarchiving restores `completed` or `active`. |
| `complete_container` / `reopen_container` | Explicit completion through `check_can_complete` (`NeedsOverrideError` → `ConflictError`, 409); reopen clears `completed_at`. |
| `list_tasks` / `get_task` / `create_task` / `update_task` / `delete_task` | Task CRUD. Status changes go through `transition_task`. |
| `organize_task` / `promote_task` | Organize keeps the task's identity and its first `organized_at`; promote replaces an Inbox task with a new container. |
| `main_quests_view` / `ambition_view` / `goal_view` / `side_quests_view` / `side_quest_view` / `inbox_view` | Screen read models (`src/atlas/services/quest_views.py`). |

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
- `tests/services/test_quests.py` — acceptance criteria 1–21 through the services (in-memory SQLite), structure and delete rules, promote, organize, filters
- `tests/api/test_quests.py` — every endpoint group through `TestClient`, error mapping
- `tests/services/test_port.py` — quest export/import, v10 exports
- `tests/services/test_seed.py` — the demo seed covers every quest shape

## Status

Q1 done (backend, typed client, seed); the quest screens are placeholders until Q2 and Q3.
