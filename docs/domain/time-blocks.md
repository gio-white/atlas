# Time blocks

## Purpose

Keep scheduling separate from execution. A [task](quests.md) is what you want to achieve; a time
block is when you intend to work toward it. One task can have many blocks. Completing a block
records that a session happened; it never completes the task.

## Concepts

- **Time block** (shown as a session) — a planned interval for one task.
- **Session done** — the block is marked completed. A `todo` task moves to `in_progress`.
- **Outcome achieved** — completing the task itself, a separate explicit action.
- **Cancelled** — the session is called off ahead of time; the row is kept.
- **Didn't happen** (`missed`) — the session's time came and it was not held; the row is kept.
  Unlike a cancelled session it counts as not kept in "Sessions kept" ([home](home.md)).
- **Unconfirmed** (derived) — a block still `scheduled` after its end time.
- **Planned time** (derived) — the sum of the durations of blocks that were neither cancelled nor
  missed; never called actual effort.

## Data model

### `time_block`

| Field               | Type          | Notes                                                    |
| ------------------- | ------------- | -------------------------------------------------------- |
| `id`                | int           | primary key                                              |
| `task_id`           | int           | FK `task`, RESTRICT, indexed                             |
| `start_at`          | datetime      | UTC, indexed                                             |
| `end_at`            | datetime      | UTC                                                      |
| `status`            | enum          | `scheduled \| completed \| cancelled \| missed`          |
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
  blocks that hold time (not `cancelled` or `missed`, `TAKES_NO_TIME`) of the non-archived tasks
  under an item, summed up the tree. Shown beside
  the estimate and never called actual effort (brief P6.4).
- **Session done** (`complete_block`): the block becomes `completed`; a `todo` task moves to
  `in_progress` (stamping `started_at`). An `in_progress` or `completed` task is unchanged.
  Nothing else changes (plan D11).
- **Cancel**: the block becomes `cancelled`; the row is kept and the task is unchanged.
- **Didn't happen** (`check_can_miss`): only a `scheduled` block whose start has passed can be
  marked; it becomes `missed`, the row is kept, and the task is unchanged. A block that has not
  started is cancelled instead.
- **Sessions kept** (`sessions_kept`): of the blocks starting in a window that are due an answer
  (done, missed, or unconfirmed), how many are done; cancelled blocks and planned blocks that have
  not ended are left out ([home](home.md#rules-and-calculations)).
- **Unconfirmed** (`is_unconfirmed`): `status = scheduled` and `end_at ≤ now`. Computed, never
  stored (plan D12).
- **Overlap** (`overlapping_ids`): blocks that hold time whose intervals intersect another such
  block. Allowed; the calendar marks them.
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
| `POST` | `/time-blocks/{id}/miss` | Didn't happen: only for a scheduled block that has started (otherwise 400); the task is unchanged | implemented |
| `GET` | `/views/today` | Today's blocks with task and parent path, unconfirmed blocks, tasks due, and "Up next" (`as_of`) | implemented |
| `GET` | `/views/plan` | Blocks overlapping [`start`, `end`) with task and parent path, overlaps marked; `not_scheduled`, the next actions with no upcoming session | implemented |

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

**Plan** (`plan_view`):

- `blocks` — every block (any status) overlapping [`start`, `end`), by start, each with its
  task; `overlaps` marks non-cancelled blocks that intersect another.
- `not_scheduled` — the same next actions as `up_next` (active goals first, then active side
  quests, each in position order, without duplicates) that have no **upcoming session**: no
  block that is still `scheduled` and ends after now. A session in progress counts as upcoming;
  a past one waiting to be confirmed, a done, cancelled, or didn't-happen one does not. It does
  not depend on [`start`, `end`), so it is the same whichever week is shown.

Service functions (`src/atlas/services/time_blocks.py`):

| Function | Role |
| -------- | ---- |
| `list_time_blocks` / `get_time_block` / `create_time_block` / `update_time_block` / `delete_time_block` | CRUD. Datetimes are converted to UTC before they are stored or compared. |
| `complete_time_block` / `cancel_time_block` / `miss_time_block` | Session outcome through `complete_block`; the task row changes only when it was `todo`. |
| `today_view` / `plan_view` | Execution read models (`src/atlas/services/quest_views.py`). |

## Screens

Shown to people as **sessions**. Every screen shows what the API returns: unconfirmed, overlaps,
and planned time are never worked out in the browser. Local ↔ UTC conversion happens in one
place, `localToUtc` / `utcToLocal` in `web/src/lib/timeBlocks.ts`; times read as "09:05"
(24-hour, browser-local). The app's one accent (the theme's `accent`, [design system](../product/design-system.md#colour)) is used for borders, icons, the now line, and today's date pill; the rest
stays neutral, and Unconfirmed keeps the warning colour. A task is drawn as
a round checkbox (empty for To do, dashed for In progress, checked for Done); a side quest path
starts with a scroll icon, a goal path with a flag, an ambition path with a compass.

**Today** is part of Home ([home](home.md#screens)); the quest Today page is gone and `/today`
redirects to `/`. Home reads `GET /views/today?as_of=` for the shell date (`?on=`), and its
session blocks are `web/src/components/home/QuestBlocks.tsx`.

- **To confirm** (only when there are any): every block from `unconfirmed`, with its day and
  time, task, and parent path. Each has **Session done** and **Didn't happen**
  (`POST /time-blocks/{id}/miss`). There is no Outcome achieved here.
- **Today**: the `blocks` timeline. Each row shows start and end time, task title,
  the parent path ("Ambition › Goal › Milestone › Chapter", ancestors only), and the planned
  length. Two control groups, set apart by a divider:
  - **Session done** (`POST /time-blocks/{id}/complete`), with **Edit** and, beside it, **Cancel**
    for a session that has not started or **Didn't happen** for one that has (`hasStarted` in
    `web/src/lib/timeBlocks.ts`).
    The status line says the task stays open. It never calls the task endpoint.
  - **Outcome achieved** (`PATCH /tasks/{id}` with `status: completed`). The first time, a
    dialog ("Complete the task?") explains the difference; confirming stores
    `atlas.quests.outcomeConfirmed` in `localStorage`, and later presses act at once. It never
    calls the block endpoint.

  Once the session is done, its row shows "Session done" as text; once marked, "Didn't happen". Once the task is done, it
  shows "Outcome achieved". On the current day a **Now** line sits before the first block that
  has not started.
- **Due today** (`due_today`, overdue marked "Overdue · 5 Nov") and **Up next** (`up_next`):
  each task has a **Schedule** button that opens the time-block dialog for it.
- **Plan a session** opens the dialog with the task picker.

**Plan** (`/quests/plan`: `PlanPage.tsx` + `components/quests/time/PlanGrid.tsx`) reads
`GET /views/plan` for the local Monday 00:00 to the next Monday 00:00, converted to UTC.

- The week is the one containing the shell date, so it lives in the URL as `?on=`. **Previous**
  and **Next** move `on` by seven days; **This week** removes it.
- Monday–Sunday columns × 24 hour rows (48 px per hour) in a scrolling panel. It opens scrolled
  to the hour before now, and on narrow screens sideways so today's column is in view. Today's
  column is tinted and shows a now line.
- Blocks are drawn at their local start, clipped to the day; a block across midnight shows in
  both days.
  - Scheduled: accent left border.
  - Unconfirmed: warning colour.
  - Completed: subdued.
  - Didn't happen: dashed warning border, subdued, always shown (it is in the legend).
  - Cancelled: dashed and struck through, hidden unless **Show cancelled (n)** is ticked.
  - Overlapping (`overlaps` from the API): a warning ring and a layers icon, set side by side in
    lanes so both stay readable. The lanes are layout only.
- Each empty hour is a button: clicking it opens the dialog at that hour (:30 for a click in its
  lower half) with the task picker. Clicking a block opens the dialog to edit it. No dragging in
  V1 (plan D15).
- **Not scheduled yet** (`not_scheduled`): beside the week from 1280px, below it on smaller
  screens. Each task shows its title and parent path, with a **Schedule** button that opens the
  time-block dialog with that task already chosen. Empty: "Everything next has a session."

**Time-block dialog** (`components/quests/time/TimeBlockDialog.tsx`), shared by Home, Plan, and
the task's sessions:

- Inputs: **Date**, **From**, and **To**, as local inputs.
- A session sits within one local day. A new one defaults to the next half hour for 60 minutes,
  capped at 23:59.
- Shows "Duration: 1h 30m". Shows "The end time must be after the start time." (and does not
  save) when To ≤ From.
- **New session:** search over organized, open tasks from `GET /tasks`, leaving out Inbox,
  completed, and archived tasks, or use the fixed task it was opened for. Saves with
  `POST /time-blocks`.
- **Edit:** **Save time** (`PATCH`). For a scheduled block, also **Session done** and **Cancel
  session** (**Didn't happen** once it has started). **Delete** asks again ("Delete for good"), since cancelling keeps a record.
- API errors show inside the dialog.

**Task sessions** (`components/quests/time/TaskTimeBlocks.tsx`, props
`{ taskId, onChanged? }`): reads `GET /tasks/{id}`.

- Shows "2h 30m planned · estimate 3h" from `planned_minutes` and `estimate_minutes`.
- Lists the task's blocks (day, time range, status or Unconfirmed, length) with Done, Cancel
  (or Didn't happen once it has started), and Edit.
- **Schedule** opens the dialog for the task. It is disabled for a completed task ("Reopen the
  task to plan more sessions.").
- Shown in the task drawer for every organized task: it is the drawer's default sessions
  section (`sessionsSection` in `web/src/components/quests/TaskDrawer.tsx`); Inbox tasks show no
  sessions section.

## Tests

- `tests/domain/test_quests.py` — planned effort, unconfirmed, session done (criterion 14), overlap, missed blocks hold no time, only a started planned session can be missed, sessions kept
- `tests/services/test_time_blocks.py` — CRUD, UTC conversion, session done, cancel, and didn't happen (kept apart from cancel), overlaps, Today (local day, unconfirmed, due, up next), Plan, Not scheduled yet (a past, cancelled, or missing session leaves a task on it; a session in progress takes it off)
- `tests/api/test_quests.py` — time block endpoints (including `/miss`), Today, Plan
- `tests/db/test_quest_schema.py` — `end_at > start_at`, unique external event per provider
- `web/src/lib/timeBlocks.test.ts` — local ↔ UTC (pinned to Europe/Copenhagen, both offsets), window validation, Monday weeks and their UTC range, day placement and midnight clipping, lanes, defaults, path label, the Outcome achieved memory
- `web/src/components/quests/time/execution.test.tsx` (jsdom):
  - Home's sessions: time range and path; Session done calls only the block endpoint; Outcome achieved confirms the first time, then calls only the task update; a session to confirm resolves as done or as didn't happen (never cancel).
  - Plan grid: a block in the right day column at the right hour; cancelled hidden by the toggle; overlaps marked; an empty slot opens with its date and hour.
  - Dialog: validation; create and edit in UTC; the picker leaves out Inbox and completed tasks.
  - Task sessions: planned versus estimate, Session done, no scheduling for a completed task.
- `web/src/pages/quests/PlanPage.test.tsx` (jsdom) — Not scheduled yet lists the tasks and opens the dialog with the chosen task; its empty state

## Status

Implemented: backend, typed client, and seed (Q1); the time-block dialog, Plan, and the task
sessions section (Q3). Today moved into Home and "Didn't happen" became its own status with the
redesign brief's phase 3; phase 5 renamed Calendar to Plan in the API and code and added Not scheduled yet. `TaskTimeBlocks` is the task drawer's sessions section.
