# Life areas

## Purpose

Areas group metrics by part of life (Health, Career, Finance, Relationships) and tag goals.

## Concepts

- **Area** — a life aspect that groups metrics. Goals carry an optional area tag; they are not owned by an area.
- **Area view** — one area's metrics, habits, and tagged goals.
- Well-known system areas created on first use: `screen` ([screen time](screen-time.md)), `life` ([journal](journal.md)), `habits` ([habits](habits.md)).

## Data model

### Area

A life aspect that groups metrics: Health, Career, Finance, Relationships. Goals may carry an optional area tag; they are not owned by an area.

| Field         | Type            | Notes                                                       |
| ------------- | --------------- | ----------------------------------------------------------- |
| `id`          | int             | primary key                                                 |
| `slug`        | str             | unique                                                      |
| `name`        | str             | display name                                                |
| `description` | str | None      |                                                             |
| `archived_at` | datetime | None | UTC; archived areas are hidden from views but never deleted |

## Rules and calculations

Archived areas are hidden from views but never deleted. `area_view` is described in the review row of [habits](habits.md#api).

## API

Conventions shared by every endpoint (slugs, `as_of`, errors): [api-conventions](../architecture/api-conventions.md).

| Method   | Path                     | Purpose                                       | Status      |
| -------- | ------------------------ | --------------------------------------------- | ----------- |
| `GET`    | `/areas`                 | List areas                                    | implemented |
| `POST`   | `/areas`                 | Create an area                                | implemented |
| `GET`    | `/areas/{slug}`          | Get one area                                  | implemented |
| `PATCH`  | `/areas/{slug}`          | Update name and description                   | implemented |
| `POST`   | `/areas/{slug}/archive`  | Archive an area                               | implemented |
| `GET`    | `/views/areas/{slug}`    | One area's metrics, habits, and goals         | implemented |

Service functions (in `src/atlas/services/`, each taking an explicit `Session` first; see [overview](../architecture/overview.md#services)):

| Function | Role |
| -------- | ---- |
| `create_area` / `list_areas` / `get_area` / `update_area` / `archive_area` | Areas. Archive stamps `archived_at` (UTC) and hides the row from default lists; areas are never deleted. `update_area` may change name and description. |

## Screens

`/area/:slug` is the area dashboard; areas are created and edited in Catalog. Route inventory with status: [navigation](../product/navigation.md).

## Tests

- `tests/services/test_areas.py`, `tests/services/test_views.py`
- `tests/api/test_areas.py`, `tests/api/test_views.py`

## Status

Implemented. Redesign pending the navigation discussion (`docs/plans/discussions/navigation-and-organization.md`).
