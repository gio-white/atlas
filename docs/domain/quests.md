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

The **Quests** destination has four tabs: Main quests, Side quests, Inbox, and Plan (route
inventory: [navigation](../product/navigation.md)). This section covers the screens Q2 of the
[plan](../plans/quests-plan.md#6-screens) builds; Today, Plan (the week of sessions), and the
sessions section of the task drawer are in [time blocks](time-blocks.md#screens).

**The browser computes nothing.** Progress, `weight_share`, chapter state, eligibility, open
children, and next action are shown exactly as the API returns them. `web/src/lib/quests.ts`
only labels (status, priority, chapter state, level names), formats dates ("7 Nov 2026") and
percentages, links items to their page, orders siblings for up/down moves, and searches the
organize picker. Every screen reloads its view after a change.

**Visual language** (`web/src/components/quests/QuestVisuals.tsx`). One quest accent, the
theme's `iris`, on neutral surfaces; light and dark come from the theme tokens. Levels are told
apart by icon and shape, never by colour alone: Ambition = compass, Goal = flag, Milestone =
diamond node, Chapter = bookmark, Task = round checkbox, Side quest = scroll (lucide-react).
Cards carry a progress ring (a dashed empty ring and "Not broken down yet" when `progress` is
null); rows carry a thin bar. Completed items turn `good` green. No tables.

| Screen | Route | What it shows and does |
| ------ | ----- | ---------------------- |
| Main quests | `/quests` | One section per ambition: title, goal count, done-task count, target date, a thin bar, then its **goal cards** and an "Add a goal" tile, then a strip of the ambition's direct tasks. An ambition with no goals stays visible with "No goals yet" and **Add a goal**. Then **Independent goals**. Header buttons: **New ambition**, **New goal**. No trees here |
| Ambition | `/quests/ambitions/:id` | Breadcrumb, ring, status, counts, target date, **Edit** (title, description, target date, archive). Completion control. Goal cards with up/down; **Add a goal** (pre-set to this ambition). Its direct tasks with add and reorder |
| Goal (quest map) | `/quests/goals/:id` | Breadcrumb **Main quests › Ambition › Goal**; ring, status, due date, counts, **Edit** (including moving to another ambition or none, weight, archive); **What success looks like**; completion control. **Quest map**: a vertical dashed path of diamond milestone nodes. Each node shows its title, done count, due date, chapter count, its share of the goal, a thin bar, edit, and up/down, and expands into its chapters and its direct tasks plus a compact completion control. Completed milestones start folded. The path ends with **Add a milestone**. Then **Tasks directly on this goal**. A line under the heading says how tasks fill chapters, milestones, and the goal, and that the percentage beside an item is how much it counts toward the level above |
| Side quests | `/quests/side-quests` | **New side quest**; compact side quest cards (ring, status, due date, chapter count, done count, next action); **Standalone tasks** with add (created with `standalone: true`) |
| Side quest | `/quests/side-quests/:id` | Breadcrumb, ring, status, counts, **Edit**, completion control, and the same tree component as a milestone |
| Inbox | `/quests/inbox` | See below |
| Task drawer | from any task row | See below |

**Shared pieces** (`web/src/components/quests/`):

- **Goal and side quest cards** (`QuestCard.tsx`): title (links to the page), description,
  ring, status chip (including **Completed with open items**), date, milestone or chapter
  count, "3 of 7 tasks done", and the **Next** action from the API (opens the task drawer). With
  no next action an open item shows **Add a task** (links to its page).
- **Tree** (`QuestTree.tsx`): the inside of a milestone or side quest. Each chapter shows its
  bookmark, title, state chip (**Empty** dashed, Not started, In progress, Completed), share,
  bar, done count, edit, up/down, its tasks, and **Add a task**; an empty chapter says it never
  counts as done. Then the direct tasks ("Tasks directly on this milestone" when there are
  chapters too) and **Add a chapter**.
- **Task rows** (`TaskList.tsx`): a round checkbox (open, half-filled for in progress, checked
  when done). Clicking it is the explicit completion; clicking a done task reopens it to To do.
  The title opens the drawer; the meta line shows In progress, High priority, due date, and
  estimate; the chip on the right is the task's share of its parent. Up/down arrows reorder
  (hidden on phones for tasks). **Add a task** opens an inline field: Enter adds and keeps the
  field open for the next one, Escape closes it.
- **Reorder** sends `position` for each sibling whose place changed after renumbering 0…n-1
  in the new order (`reorder` in `lib/quests.ts`), so ties never block a move (plan D16).
- **Create and edit** (`QuestFormDialog.tsx`): title, description, and per level: target date
  (ambition), due date (goal, milestone, side quest), success description and ambition
  (goal), weight (goal, milestone, chapter). The weight hint gives the current share ("It now
  counts for 40% of …"). Edit also offers **Archive** / **Restore**.
- **Completion control** (`CompletionControl.tsx`): shows the API's verdict. Eligible:
  "Everything here is done" and **Complete …**. Not eligible: "N items still open" and
  **Complete anyway…**, which opens a confirmation listing every open child with its level
  icon, says they keep their status and that the item will show "Completed with open items",
  and sends `override: true` only on **Complete anyway**. Completed: the status, the open-items
  note when it applies, and **Reopen**. Nothing ever completes automatically.
- **Organize picker** (`OrganizePicker.tsx`): a search field over every ambition, goal,
  milestone, chapter, and side quest, read from `GET /views/main-quests`,
  `GET /views/side-quests`, and each goal and side quest tree. Every typed word must match the
  title, the ancestor path, or the level name. Arrow keys move the highlight; Enter picks. The
  current parent is marked "Here now" and cannot be picked.

**Inbox** (`/quests/inbox`, `InboxPage.tsx`, `InboxItem.tsx`):

- The capture field is focused on arrival and again after each capture or sort. Enter adds the
  title alone (`POST /tasks` with only `title`); the newest item is first.
- Each item: title, description, date added, **Edit** (title and description inline), a
  details button (task drawer), **Organize…** (picker → `POST /tasks/{id}/organize` with the
  same task id, so its identity, status, and sessions are kept), **Make standalone**
  (`{standalone: true}`), **Turn into…**, and **Archive**.
- **Turn into…** (`PromoteDialog.tsx`) offers Ambition, Goal, Side quest, Milestone, and
  Chapter. A goal may go under an ambition; a milestone needs a goal and a chapter needs a
  milestone or side quest (picked with the organize picker). A task with sessions is refused
  before sending: "This task already has sessions planned, so it can't become something else.
  Organize it instead: it keeps its sessions." The server's refusal (400) shows the same text.
- After each change a line confirms it ("Sorted into …", "Now a standalone task.", "Turned
  into a side quest: …" with a link). Empty: "Inbox zero".
- **Inbox count:** every screen calls `notifyInboxChanged()` after a change that can touch the
  Inbox; `Layout` listens for the `atlas:inbox-changed` window event and refetches
  `GET /views/inbox`, besides refreshing on navigation. The count shows on the Quests item of
  the rail and on the Inbox tab ([navigation](../product/navigation.md#shell)).
- **Add → Task** in the header (`components/shell/QuickTaskDialog.tsx`) captures a title from
  any page with the same `POST /tasks` call. The Inbox page listens for the same event, so a
  task added that way appears in the list at once.

**Task drawer** (`TaskDrawer.tsx`) slides in from the right on any screen that renders tasks
(each page wraps its content in `TaskDrawerProvider`, and rows call `useOpenTask()`):

- **Status**: To do / In progress / Done, applied at once; Done is only ever this explicit
  choice (or the row checkbox).
- **Title, description, priority, due date, estimate (minutes), weight**, saved together with
  **Save changes**. The weight hint shows the task's share of its parent; weight is disabled
  while the task has no parent.
- **Belongs to**: the parent with its level and path (links to its page) and **Move…** (the
  organize picker), plus **Make it a standalone side quest**.
- **Sessions**: a `data-slot="task-sessions"` section between Belongs to and Archive shows the
  task's sessions with planned time against the estimate, and Schedule
  ([time blocks](time-blocks.md#screens)). It is `TaskDrawerProvider`'s default `extraSection`
  (`sessionsSection`, rendering `TaskTimeBlocks`); a provider may pass its own. Inbox tasks have
  no sessions section: they are scheduled once organized.
- **Archive task** / **Restore task**.

## Tests

- `tests/domain/test_quests.py` — every rule above, pure (acceptance criteria 14–21)
- `tests/db/test_quest_schema.py` — constraints, RESTRICT foreign keys, v10 → v11 migration
- `tests/services/test_quests.py` — acceptance criteria 1–21 through the services (in-memory SQLite), structure and delete rules, promote, organize, filters
- `tests/api/test_quests.py` — every endpoint group through `TestClient`, error mapping
- `tests/services/test_port.py` — quest export/import, v10 exports
- `tests/services/test_seed.py` — the demo seed covers every quest shape
- `web/src/lib/quests.test.ts` — labels, links, sibling reorder, organize targets and search
- `web/src/components/quests/QuestTree.test.tsx` — tree with mixed children and an empty chapter; completing only through the checkbox
- `web/src/components/quests/InboxItem.test.tsx` — Inbox capture with only a title, organize keeps the task id, make standalone, Inbox count event
- `web/src/components/quests/PromoteDialog.test.tsx` — promote refused when the task has sessions (before sending and on a 400), promote with and without a parent
- `web/src/components/quests/CompletionControl.test.tsx` — the override confirmation lists open items and sends `override` only on confirm; eligible completion; reopen

## Status

Q1 done (backend, typed client, seed). Q2 done: Main quests, Ambition, the goal quest map, Side quests, Side quest, Inbox, and the task drawer. Today, Calendar, and the drawer's sessions section come with Q3 ([time blocks](time-blocks.md)).
