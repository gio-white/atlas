# Journal

## Purpose

Free-text daily notes stored as ordinary entries on a well-known metric.

## Concepts

- **Life catalog** — the well-known `life` area and `journal` metric, created on first use.
- **Journal entry** — a text entry on `journal`.

## Data model

### Life catalog

Journal (`/journal` page) uses well-known rows in the existing tables, created on first use like the `screen` area. Area `life`. Metric `journal` (`text`, `last`). Journal notes are ordinary entries; today's journal text is the latest `journal` entry on `as_of`. There is no shared check-in or slip counter: each quit habit has its own slip log. Databases created before the `remove-updates` cycle may still hold the old `checkin` metric and `checkin-daily` habit; they are ordinary rows now and can be archived from Catalog.

## Rules and calculations

Today's journal text is the latest `journal` entry on `as_of` (see Data model).

## API

Conventions shared by every endpoint (slugs, `as_of`, errors): [api-conventions](../architecture/api-conventions.md).

| Method   | Path                     | Purpose                                       | Status      |
| -------- | ------------------------ | --------------------------------------------- | ----------- |
| `GET`    | `/journal`               | Today's journal text (creates life catalog if missing)  | implemented |
| `POST`   | `/journal`               | Log a text entry on the `journal` metric                | implemented |

Service functions (in `src/atlas/services/`, each taking an explicit `Session` first; see [overview](../architecture/overview.md#services)):

| Function | Role |
| -------- | ---- |
| `log_journal` / `journal_day` | Journal text. Ensures metric `journal`, logs a non-empty string, and returns the latest text for `as_of`. |

## Screens

`/journal` (reached from a link on Home; it has no entry on the rail) shows today's journal text (`POST /journal` to write, `PATCH /entries/{id}` to edit), and the last 90 days of earlier journal entries from `GET /entries?metric=journal`.

Route inventory with status: [navigation](../product/navigation.md).

## Tests

- `tests/services/test_journal.py`
- `tests/api/test_journal.py`

## Status

Implemented.
