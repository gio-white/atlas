# API conventions

Rules every endpoint follows. The endpoint tables live in each feature's doc under **API**;
`tests/test_docs_drift.py` checks that every route in the FastAPI app appears in exactly those
tables and that every documented route exists.

## Status, routers, and errors

Status is `implemented` only when the endpoint is merged with tests. Everything else is `planned`.

Routers parse the request, call a service, and serialize. Create/list bodies use slugs (`metric`, `category`) rather than integer foreign keys; entries are addressed by integer `id`. Quest entities (ambitions, goals, milestones, side quests, chapters, tasks, time blocks) have no slug: their paths and bodies use integer ids (`/goals/{id}`, `ambition_id`), and a task's parent is given as `parent_kind` (`ambition`, `goal`, `milestone`, `chapter`, `side_quest`) plus `parent_id`. `POST /entries` sets `source` to `api`. Service failures map to HTTP status: `NotFoundError` → 404, `AlreadyExistsError` → 409, `ValidationError` → 400. Pydantic request-shape errors remain 422. For quests the mapping is: an invalid or archived parent → 400, an unknown id → 404, deleting a container that still has children → 409 (`ConflictError`), and completing an item that is not eligible without `override: true` → 409 with the open children listed in the message.

## Query filters

Optional filters the services already support are query parameters: `metric` and `include_automatic` on entries, `metric` on habits, `ambition_id` and `include_archived` on goals, `parent_kind` + `parent_id`, `status`, `inbox`, `standalone`, `due_on`, and `include_archived` on tasks, `start` / `end` (UTC datetimes) and `task_id` on time blocks and `/views/calendar`, `include_archived` on metrics, screen categories/apps/devices, and entertainment topics/titles, `kind` / `status` / `topic` on entertainment titles, `as_of` on status/progress/views including `/screen/view`, `/screen/dashboard`, `/sleep/view`, `/entertainment/dashboard`, `/views/today`, `/views/habits`, and `/views/habits/calendar`, `period` on `/screen/dashboard`, `/entertainment/dashboard`, and `/views/habits/calendar`, `days` (1–366) on `/sleep/view`, and `replace` on import.

## Slugs

Slugs are normalized to lowercase and must match `[a-z0-9]+(?:-[a-z0-9]+)*`. An omitted `name` defaults to the slug with hyphens turned into spaces and title-cased.

## Hosting and tests

There is no authentication. The app binds to localhost only (`127.0.0.1`). CORS allows the Vite dev server origins so the SPA on `:5173` can call the API on `:8000`; production is same-origin and does not need CORS. Tests use FastAPI `TestClient` against `create_app(session_factory=...)` with in-memory SQLite; they never start a live server.

## Endpoint index

| Prefix | Doc |
| ------ | --- |
| `/entries`, `/metrics` | [trackers and entries](../domain/trackers-and-entries.md#api) |
| `/habits`, `/views/habits` | [habits](../domain/habits.md#api) |
| `/ambitions`, `/goals`, `/milestones`, `/side-quests`, `/chapters`, `/tasks`, `/views/main-quests`, `/views/ambitions`, `/views/goals`, `/views/side-quests`, `/views/inbox` | [quests](../domain/quests.md#api) |
| `/time-blocks`, `/views/today`, `/views/calendar` | [time blocks](../domain/time-blocks.md#api) |
| `/screen` | [screen time](../domain/screen-time.md#api) |
| `/sleep` | [sleep](../domain/sleep.md#api) |
| `/journal` | [journal](../domain/journal.md#api) |
| `/entertainment` | [entertainment](../domain/entertainment.md#api) |
| `/export`, `/import` | [cli and port](cli.md#api) |
