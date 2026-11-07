# History

## Purpose

Every recorded entry, by day, with inline correction.

## Concepts

- **History** — the list of entries, newest first, filterable by metric and dates.

## Data model

History stores nothing new; it lists `Entry` rows ([trackers and entries](trackers-and-entries.md#data-model)).

## Rules and calculations

Ordering and filters are those of `list_entries` ([trackers and entries](trackers-and-entries.md#api)).

## API

Uses `GET /entries`, `PATCH /entries/{id}`, and `DELETE /entries/{id}` ([trackers and entries](trackers-and-entries.md#api)).

## Screens

`/history` lists entries from `GET /entries` grouped by day (last 30 days by default; `?metric=`, `?from=`, `?to=`) with inline edit of value, day, and note (`PATCH /entries/{id}`, only changed fields) and a confirmed delete.

Route inventory with status: [navigation](../product/navigation.md).

## Tests

- `tests/services/test_entries.py`, `tests/api/test_entries.py`
- `web/src/lib/entries.test.ts`

## Status

Implemented.
