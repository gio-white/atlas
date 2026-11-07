# Tasks

## Purpose

A one-off work queue (today / upcoming / someday), optionally linked to a goal.

## Concepts

- **Task** — a work-queue item, not an observation.
- **Bucket** — `today`, `upcoming`, or `someday`.

## Data model

### Task

A one-off work-queue item, not an observation. Completing a task stamps `done_at`; it does not write an entry. Addressed by integer id, like entries.

| Field        | Type             | Notes                                              |
| ------------ | ---------------- | -------------------------------------------------- |
| `id`         | int              | primary key                                        |
| `title`      | str              |                                                    |
| `bucket`     | enum             | `today \| upcoming \| someday`                     |
| `due_on`     | date \| None     | optional local date                                |
| `due_at`     | datetime \| None | optional precise time (UTC)                        |
| `priority`   | enum             | `high \| normal \| low`                            |
| `goal_id`    | int \| None      | optional FK to `Goal`; wire key is the goal slug |
| `done_at`    | datetime \| None | UTC; `None` means open                             |
| `created_at` | datetime         | UTC                                                |

Completing a task never changes goal progress. A task may point at any horizon; the goals board weekly column uses linked tasks for this ISO week.

## Rules and calculations

Completing a task stamps `done_at` and never changes goal progress (see Data model).

## API

Conventions shared by every endpoint (slugs, `as_of`, errors): [api-conventions](../architecture/api-conventions.md).

| Method   | Path                     | Purpose                                       | Status      |
| -------- | ------------------------ | --------------------------------------------- | ----------- |
| `GET`    | `/tasks`                 | List tasks (`bucket`, `include_done`, `goal`)           | implemented |
| `POST`   | `/tasks`                 | Create a task                                           | implemented |
| `PATCH`  | `/tasks/{id}`            | Update title, bucket, due, priority, `done`, or `goal`  | implemented |

Service functions (in `src/atlas/services/`, each taking an explicit `Session` first; see [overview](../architecture/overview.md#services)):

| Function | Role |
| -------- | ---- |
| `create_task` / `list_tasks` / `update_task` | Task queue. Optional `goal` slug links a task to a goal. `list_tasks` can filter by bucket and goal. `update_task(done=True)` stamps `done_at`. |

## Screens

`/tasks` is the three-column work queue from `GET /tasks` (today / upcoming / someday, optional goal link, create / complete / move). The page description reads "Things to get done. Check them off as you go." and the button "New task". Each task card has a compact "Move to… ▾" button opening a menu with the other two lists (`PATCH /tasks/{id}` with the new bucket); it closes on Escape or an outside click. Completing a task never writes an entry. The Goals week column and goal detail also link to `/tasks` (goal detail can preselect `?goal=`).

Route inventory with status: [navigation](../product/navigation.md).

## Tests

- `tests/services/test_tasks.py`
- `tests/api/test_tasks.py`
- `web/src/lib/tasks.test.ts`

## Status

Implemented.
