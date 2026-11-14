# Journal

## Purpose

Free-text daily notes stored as ordinary entries on a well-known metric.

## Concepts

- **Journal metric** — the well-known `journal` metric (origin `journal`), created on first use.
- **Journal entry** — a text entry on `journal`.

## Data model

### Journal metric

Journal (`/journal` page) uses one well-known row in the existing tables, created on first use: the metric `journal` (`text`, `last`, origin `journal`). It belongs to no area (areas are gone, [decision 0008](../decisions/0008-areas-removed-metrics-carry-an-origin.md)) and is not listed in Settings → Metrics. Journal notes are ordinary entries; today's journal text is the latest `journal` entry on `as_of`. There is no shared check-in or slip counter: each quit habit has its own slip log. Databases created before the `remove-updates` cycle may still hold the old `checkin` metric and `checkin-daily` habit; they are ordinary rows now and can be archived in Settings → Metrics.

## Rules and calculations

Today's journal text is the latest `journal` entry on `as_of` (see Data model).

## API

Conventions shared by every endpoint (slugs, `as_of`, errors): [api-conventions](../architecture/api-conventions.md).

| Method   | Path                     | Purpose                                       | Status      |
| -------- | ------------------------ | --------------------------------------------- | ----------- |
| `GET`    | `/journal`               | Today's journal text (creates the journal metric if missing)  | implemented |
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
