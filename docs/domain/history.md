# History

## Purpose

Every recorded entry, by day, with inline correction.

## Concepts

- **History** — the list of entries, newest first, filterable by metric and dates.
- **Automatic data** — entries written for you by a data source rather than typed: today, the minutes each Screen Time session writes onto its app's metric (a metric with origin `screen`).

## Data model

History stores nothing new; it lists `Entry` rows ([trackers and entries](trackers-and-entries.md#data-model)).

## Rules and calculations

Ordering and filters are those of `list_entries` ([trackers and entries](trackers-and-entries.md#api)). Hiding automatic data is `include_automatic=false`, which leaves out entries whose metric has the origin `screen`; with no screen data it changes nothing.

## API

Uses `GET /entries` (with `include_automatic`), `PATCH /entries/{id}`, and `DELETE /entries/{id}` ([trackers and entries](trackers-and-entries.md#api)).

## Screens

`/settings/entries` (Settings → All entries, formerly History at `/history`) lists entries from `GET /entries` grouped by day (last 30 days by default; `?metric=`, `?from=`, `?to=`) with inline edit of value, day, and note (`PATCH /entries/{id}`, only changed fields) and a confirmed delete.

A **Hide automatic data** switch is on by default and sends `include_automatic=false`, so Screen Time minutes don't flood the list. Turning it off is kept in the URL as `?automatic=show`. When one metric is picked in the filter, that metric is always shown and the switch is disabled.

Route inventory with status: [navigation](../product/navigation.md).

## Tests

- `tests/services/test_entries.py`, `tests/api/test_entries.py`
- `web/src/lib/entries.test.ts`
- `web/src/pages/displayOnly.test.tsx` (All entries sends `include_automatic: false` by default and drops it when the switch is off)

## Status

Implemented.
