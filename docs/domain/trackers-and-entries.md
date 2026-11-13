# Trackers and entries

## Purpose

Metrics define what is measured; entries are the recorded facts every habit and review screen is computed from. (The UI may call a metric a tracker and an entry a record once the navigation discussion settles names; until then the UI uses the API words.)

## Concepts

- **Metric** — the definition of a measurable thing, with a value type, an aggregation, and a direction.
- **Entry** — one observation of a metric on a local date.
- **Bucket** — a day, ISO week, or month derived from `occurred_on`.
- **Rollup** — a bucket's entries combined by the metric's aggregation.

## Data model

### Metric

The definition of a measurable thing. A metric says what a value means and how same-period values roll up; it stores no values itself.

| Field         | Type            | Notes                                                                    |
| ------------- | --------------- | ------------------------------------------------------------------------ |
| `id`          | int             | primary key                                                              |
| `area_id`     | int             | FK to `Area`                                                             |
| `slug`        | str             | unique                                                                   |
| `name`        | str             |                                                                          |
| `value_type`  | enum            | `bool | count | quantity | duration | rating | text`                     |
| `unit`        | str | None      | free text, for display only (`reps`, `kg`, `min`)                        |
| `aggregation` | enum            | `sum | last | mean | max | min` — how entries in the same period combine |
| `direction`   | enum            | `higher_is_better | lower_is_better | neutral`                           |
| `archived_at` | datetime | None | UTC                                                                      |

`aggregation` is the field that makes one entry table serve everything: pushups sum across a day, bodyweight takes the last reading, mood averages.

`duration` values are stored in minutes (including fractional minutes). `bool` values are stored in `value_bool` and count as `1.0` / `0.0` wherever arithmetic is needed.

### Entry

One observation of a metric. Entries are the only stored facts in Atlas and are treated as immutable in spirit: they are corrected through amend and delete, never silently rewritten by derived logic.

| Field         | Type            | Notes                                                                       |
| ------------- | --------------- | --------------------------------------------------------------------------- |
| `id`          | int             | primary key                                                                 |
| `metric_id`   | int             | FK to `Metric`                                                              |
| `occurred_on` | date            | **local** date in `ATLAS_TZ`; the answer to "which day does this count for" |
| `occurred_at` | datetime | None | UTC; optional precise time, used to order entries within a day              |
| `value_num`   | float | None    | for `count`, `quantity`, `duration`, `rating`                               |
| `value_bool`  | bool | None     | for `bool`                                                                  |
| `value_text`  | str | None      | for `text`                                                                  |
| `note`        | str | None      | free text                                                                   |
| `source`      | enum            | `cli | api | import`                                                        |
| `created_at`  | datetime        | UTC, set on insert                                                          |

Multiple entries per metric per day are always allowed; the metric's `aggregation` resolves them. There is no uniqueness constraint on `(metric_id, occurred_on)`.

## Rules and calculations

### Period bucketing

A bucket is derived from an entry's local `occurred_on`:

| Period  | Bucket key             | Range                               |
| ------- | ---------------------- | ----------------------------------- |
| `day`   | the date itself        | one day                             |
| `week`  | `(iso_year, iso_week)` | Monday through Sunday (ISO 8601)    |
| `month` | `(year, month)`        | first through last day of the month |

A bucket is **complete** when its last day is strictly before `as_of`, and **in progress** when it contains `as_of`. The distinction matters: an in-progress bucket has not failed yet, it is merely unfinished.

### Rollup

The value of a bucket is its entries combined by the metric's `aggregation`:

| Aggregation   | Value                                                                                               |
| ------------- | --------------------------------------------------------------------------------------------------- |
| `sum`         | sum of numeric values                                                                               |
| `mean`        | arithmetic mean of numeric values                                                                   |
| `max` / `min` | extreme numeric value                                                                               |
| `last`        | value of the most recent entry, ordered by `occurred_at` when present, then `created_at`, then `id` |

A bucket with no entries rolls up to `None`, not `0`. Conflating them would make a `last`-aggregated metric like bodyweight read as zero on days it was not measured.

## API

Conventions shared by every endpoint (slugs, `as_of`, errors): [api-conventions](../architecture/api-conventions.md).

| Method   | Path                     | Purpose                                       | Status      |
| -------- | ------------------------ | --------------------------------------------- | ----------- |
| `GET`    | `/entries`               | List entries newest first (`metric`, `area`, `exclude_area`, `start_on`, `end_on`, `limit` 1–1000, default 200) | implemented |
| `POST`   | `/entries`               | Record an observation (accepts a metric slug) | implemented |
| `PATCH`  | `/entries/{id}`          | Amend an entry                                | implemented |
| `DELETE` | `/entries/{id}`          | Delete an entry                               | implemented |
| `GET`    | `/metrics`               | List metrics, filterable by area              | implemented |
| `POST`   | `/metrics`               | Create a metric                               | implemented |
| `GET`    | `/metrics/{slug}`        | Get one metric                                | implemented |
| `PATCH`  | `/metrics/{slug}`        | Update name, unit, and direction              | implemented |
| `POST`   | `/metrics/{slug}/archive`| Archive a metric                              | implemented |

Service functions (in `src/atlas/services/`, each taking an explicit `Session` first; see [overview](../architecture/overview.md#services)):

| Function | Role |
| -------- | ---- |
| `create_metric` / `list_metrics` / `get_metric` / `update_metric` / `archive_metric` | Metrics, keyed by slug, created under an area slug. `list_metrics` can filter by area and hides archived metrics and metrics whose area is archived. `update_metric` may change name, unit, and direction, not `value_type` or `aggregation`. |
| `log_entry` / `list_entries` / `amend_entry` / `delete_entry` | Capture, history, and correction. `list_entries` returns `(entry, metric slug)` pairs newest first (`occurred_on`, then `created_at`, then `id`), optionally filtered by metric slug, area slug, an excluded area slug (`exclude_area_slug` drops entries whose metric is in that area; an unknown area excludes nothing rather than 404), and an inclusive `start_on` / `end_on` range, capped by `limit` (at least 1). `log_entry` accepts a metric slug and a single `value`; a bool metric with no value stores `true`. Multiple entries per day remain allowed. Logging to an archived metric is rejected; amend and delete still work. Logging to a screen-app metric also inserts a duration-only `screen_session`. |

## Screens

Capture is the **New entry** dialog (`LogDialog`), opened from **Add → Entry** in the header, wrapping the log form (`LogForm`, `POST /entries`). Its description is "Log a value for today." (or "for <date>" when *As of* is set). No metric is preselected: the select starts on "Choose…", except when only one metric is offered (the Home habit grid), which is picked automatically. The value field is empty with a placeholder per value type ("How many?", "Amount", "Minutes", "1 to 10", "Write something") and shows the metric's unit beside it ("min" for a duration without a unit). Yes/no values read "Yes" / "No"; the note is "Optional"; the button is "Save".

History of entries: [history](history.md). Route inventory with status: [navigation](../product/navigation.md).

## Tests

- `tests/domain/test_buckets.py`, `tests/domain/test_rollup.py`
- `tests/services/test_metrics.py`, `tests/services/test_entries.py`
- `tests/api/test_metrics.py`, `tests/api/test_entries.py`
- `web/src/lib/value.test.ts`, `web/src/lib/entries.test.ts`
- `web/src/components/LogForm.test.tsx`

## Status

Implemented.
