# Atlas architecture

This document is the living source of truth for Atlas, maintained alongside the code. A change in behavior and the matching edit here belong to the same cycle: code and this document disagreeing is a bug, not a stale doc.

## Purpose

Atlas is a single-user, local-first life-tracking backend. It records what actually happened, then layers commitments (habits) and outcomes (goals) on top of that record. Everything a review screen wants to show — streaks, adherence, goal progress, whether a goal is on pace — is computed on read from the recorded facts.

Consequences of that stance:

- Backfilling an entry for last Tuesday automatically corrects every streak, adherence ratio, and goal percentage that depends on it. There is no recalculation step and nothing to migrate.
- There is exactly one capture path. Habits and goals point at metrics; they never store their own observations.
- The HTTP API is the only consumer path. The CLI is an in-process adapter over the same service layer, so a future frontend has no privileged access and no behavior of its own to reimplement.



## Data model

Integer primary keys are internal. Slugs are the human key and are what the CLI and the API accept: unique per entity type, lowercase, `[a-z0-9-]`.

```mermaid
flowchart TD
  Area[Area: life aspect] -->|groups| Metric[Metric: what is measured]
  Area -->|groups| Goal[Goal: outcome by a date]
  Metric -->|has many| Entry[Entry: one observation]
  Habit[Habit: recurring commitment] -->|measured by| Metric
  Goal -->|measured by| Metric
  Goal -->|has many| Milestone[Milestone: manual checkpoint]
```





### Area

A life aspect that groups metrics and goals: Health, Career, Finance, Relationships.


| Field         | Type            | Notes                                                       |
| ------------- | --------------- | ----------------------------------------------------------- |
| `id`          | int             | primary key                                                 |
| `slug`        | str             | unique                                                      |
| `name`        | str             | display name                                                |
| `description` | str | None      |                                                             |
| `archived_at` | datetime | None | UTC; archived areas are hidden from views but never deleted |




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

`duration` values are stored in minutes. `bool` values are stored in `value_bool` and count as `1.0` / `0.0` wherever arithmetic is needed.

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

### Habit

A recurring commitment over a metric: a schedule plus a target.


| Field          | Type            | Notes                                                                                   |
| -------------- | --------------- | --------------------------------------------------------------------------------------- |
| `id`           | int             | primary key                                                                             |
| `metric_id`    | int             | FK to `Metric`                                                                          |
| `slug`         | str             | unique                                                                                  |
| `name`         | str             |                                                                                         |
| `period`       | enum            | `day | week | month` — the bucket the target applies to                                 |
| `target_value` | float           |                                                                                         |
| `comparator`   | enum            | `at_least | at_most | exactly`                                                          |
| `weekdays`     | set[int] | None | ISO weekdays (Mon=1 … Sun=7); only valid when `period` is `day`, `None` means every day |
| `active_from`  | date            | inclusive                                                                               |
| `active_to`    | date | None     | inclusive; `None` means open-ended                                                      |


`at_most` is not an afterthought: "no more than one coffee a day" and "at least three runs a week" are the same machinery with a different comparator.

### Goal

An outcome to reach by a date. Two kinds share one table because they share a lifecycle and a due date.


| Field            | Type            | Notes                                                                            |
| ---------------- | --------------- | -------------------------------------------------------------------------------- |
| `id`             | int             | primary key                                                                      |
| `area_id`        | int             | FK to `Area`                                                                     |
| `slug`           | str             | unique                                                                           |
| `name`           | str             |                                                                                  |
| `kind`           | enum            | `metric_target | milestone`                                                      |
| `metric_id`      | int | None      | required when `kind` is `metric_target`                                          |
| `target_value`   | float | None    | required when `kind` is `metric_target`                                          |
| `comparator`     | enum | None     | `at_least | at_most | exactly`; required when `kind` is `metric_target`          |
| `baseline_value` | float | None    | optional explicit starting point; see [goal progress](#goal-progress)            |
| `measure`        | enum | None     | `latest_value | cumulative_since_start`; required when `kind` is `metric_target` |
| `start_on`       | date            | inclusive                                                                        |
| `due_on`         | date            | inclusive                                                                        |
| `status`         | enum            | `active | achieved | paused | abandoned`                                         |
| `achieved_at`    | datetime | None | UTC                                                                              |


`measure` distinguishes the two shapes of numeric goal: `latest_value` for "weigh 75 kg" (the current reading is what matters), `cumulative_since_start` for "read 12 books this year" (the running total is what matters).

### Milestone

A manual checkpoint under a goal. Available to both goal kinds, so a `metric_target` goal can still carry qualitative steps.


| Field     | Type            | Notes                  |
| --------- | --------------- | ---------------------- |
| `id`      | int             | primary key            |
| `goal_id` | int             | FK to `Goal`           |
| `name`    | str             |                        |
| `due_on`  | date | None     |                        |
| `done_at` | datetime | None | UTC; `None` means open |




### Schema management

Tables are created with `SQLModel.metadata.create_all`. A single-row `schema_version` table records the version the file was created with (`CURRENT_SCHEMA_VERSION = 1`). `atlas init` creates the parent directory if needed, opens the SQLite file at `ATLAS_DB`, runs `create_all`, and inserts that row when missing; it is safe to run twice. There is no Alembic in the MVP; a schema change ships as an explicit migration step documented in the development log.

## Layering

```mermaid
flowchart LR
  CLI[Typer CLI] --> Services[services: use cases]
  API[FastAPI routers] --> Services
  Services --> Domain[domain: pure logic]
  Services --> DB[db: SQLModel + SQLite]
  DB --> Domain
```



Imports only flow downward:

```
cli, api → services → db, domain
db → domain
domain → (stdlib / typing only)
```

The package lives at `src/atlas/` (src layout), so tests import the installed package rather than the repo root and a packaging mistake fails loudly instead of passing by accident.


| Package             | Responsibility                                                                                                                                                                                             |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `atlas/settings.py` | Configuration resolved from the environment. Stdlib only, so every layer may import it.                                                                                                                    |
| `atlas/domain/`     | Enums, value objects (`EntryView`, `HabitSpec`, `GoalSpec`, `MilestoneView`, `Bucket`, `GoalProgress`), and the calculation functions: period bucketing, rollups, `current_streak`, `longest_streak`, `adherence`, `goal_progress`, `pace_status`. Implemented. Pure — no I/O, no session, no wall clock. |
| `atlas/db/`         | SQLModel tables (`Area`, `Metric`, `Entry`, `Habit`, `Goal`, `Milestone`, `SchemaVersion`), engine, session factory, schema creation. Implemented. Unique slugs; `Entry` indexed on `(metric_id, occurred_on)`. |
| `atlas/services/`   | Use cases, each taking an explicit `Session` as its first parameter. Loads rows, hands plain values to `domain`, writes results back. Implemented. |
| `atlas/api/`        | FastAPI routers: parse, call a service, serialize. Dedicated request/response schemas only where the wire shape must differ from the table (slugs instead of integer FKs). Implemented. Session comes from a factory dependency; `uv run uvicorn atlas.api.app:app --reload` and `python -m atlas.api` bind to `127.0.0.1` only. |
| `atlas/cli/`        | Typer commands calling the same services in-process (no HTTP hop), Rich for output. Implemented. Session comes from the factory; commands never query tables. `log` resolves metric slugs by unique prefix, substring, or close match. `seed` loads the demo dataset through `seed_demo`. Review `today` is a Rich dashboard: daily habits in a left panel, weekly/monthly habits in a right panel, then logged entries and goals. Capture commands stay one-line confirmations. |


Import rules, enforced by review and by the always-applied architecture rule:

- `atlas/domain/` must not import `atlas.db`, `atlas.api`, `atlas.cli`, or `atlas.services`.
- `atlas/api/` and `atlas/cli/` must not open a session, query tables, or call SQLModel/SQLAlchemy APIs. They obtain a session from the factory and pass it into a service.
- Shared behavior lives in `atlas/services/`, so the API and the CLI cannot diverge.

The first of these is machine-enforced. Ruff's `flake8-tidy-imports` bans `atlas.db`, `atlas.services`, `atlas.api`, and `atlas.cli` project-wide, and `[tool.ruff.lint.per-file-ignores]` lifts the ban everywhere except `atlas/domain/`. An import that breaks domain purity fails `uv run ruff check` rather than waiting for review.

## Derived computations

Nothing in this section is stored. Every definition below is a pure function of entries (plus habit/goal configuration) and an explicit `as_of` date, so results are reproducible and testable without a database.

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

### Habit satisfaction

For a habit and a bucket, let `v` be the rollup of that bucket's entries.

- If `v` is not `None`, the bucket is **satisfied** when the comparator holds: `at_least` → `v >= target_value`, `at_most` → `v <= target_value`, `exactly` → `v == target_value`.
- If `v` is `None` (nothing recorded), the bucket is satisfied only when the comparator is `at_most`. Recording nothing cannot exceed a ceiling, so a coffee-free day satisfies "at most 1 coffee"; a run-free week fails "at least 3 runs".

A consequence worth knowing: `exactly 0` is never satisfied by an empty bucket. Express that commitment as `at_most 0`.

A bucket is **scheduled** when all of the following hold:

- its range intersects `[active_from, active_to]` (an edge bucket only partly inside the window still counts, once),
- for `period = day` with a `weekdays` mask, the day's ISO weekday is in the mask,
- its range intersects `[…, as_of]` — future buckets are not scheduled yet.

Unscheduled buckets are invisible to every habit computation: they do not break streaks and do not appear in adherence denominators. A weekday-masked habit is not failed by its off days.

### Streaks

`current_streak(habit, as_of)` counts consecutive satisfied scheduled buckets walking backwards from `as_of`:

1. Start at the bucket containing `as_of`. If it is in progress and already satisfied, count it. If it is in progress and not yet satisfied, skip it without breaking the streak — the period is still open.
2. Continue to earlier scheduled buckets, adding one for each satisfied bucket.
3. Stop at the first complete scheduled bucket that is not satisfied, or when the buckets leave the active window.

So a "3 runs per week" habit satisfied for the past four weeks reports a streak of 4 on Monday morning, and 5 once the third run of the current week is logged.

`longest_streak(habit, as_of)` is the longest run of consecutive satisfied scheduled buckets anywhere in the active window up to `as_of`. The in-progress bucket participates only if it is already satisfied.

### Adherence

`adherence(habit, from_date, to_date)` is `satisfied / scheduled` over the scheduled buckets in the range, counting **complete** buckets only. The in-progress bucket is excluded from both numerator and denominator so that a fresh week cannot drag the ratio down. The result is a float in `0.0 … 1.0`, or `None` when the denominator is zero (nothing was scheduled in the range).

### Goal progress

`goal_progress(goal, as_of)` returns the current value, the baseline, a fraction in `0.0 … 1.0`, and whether the target is met.

For `kind = metric_target`, the current value depends on `measure`:

- `latest_value` — the value of the most recent entry with `occurred_on <= as_of`. `None` if there is no such entry.
- `cumulative_since_start` — the sum of `value_num` over entries with `start_on <= occurred_on <= as_of`.

The baseline is `baseline_value` when set. Otherwise it is:

- for `latest_value`, the value of the most recent entry with `occurred_on <= start_on`, falling back to the current value (a goal with no history starts at 0 % rather than dividing by nothing),
- for `cumulative_since_start`, `0.0`.

The fraction is

```
fraction = clamp((current - baseline) / (target_value - baseline), 0.0, 1.0)
```

Signed arithmetic handles both directions with one formula: for "lose weight to 75 kg" the numerator and denominator are both negative, so shedding kilos moves the fraction up. When `target_value == baseline`, the fraction is `1.0` if the target is met and `0.0` otherwise. When the current value is `None`, the fraction is `None`.

The target is met when the comparator holds against `target_value`, using the same three comparisons as habit satisfaction. Reaching it does not by itself change `status`; a service marks the goal `achieved` and stamps `achieved_at`.

For `kind = milestone`, the fraction is `done_milestones / total_milestones`, `None` when the goal has no milestones, and the target is met when every milestone is done.

### Pace status

`pace_status(goal, as_of)` answers "is this on track" by comparing progress against elapsed time.

```
elapsed = clamp((as_of - start_on) / (due_on - start_on), 0.0, 1.0)   # inclusive day counts
```


| Status     | Condition                                  |
| ---------- | ------------------------------------------ |
| `achieved` | the target is met                          |
| `overdue`  | `as_of > due_on` and the target is not met |
| `no_data`  | the progress fraction is `None`            |
| `ahead`    | `fraction > elapsed + 0.05`                |
| `on_track` | `fraction` within `0.05` of `elapsed`      |
| `behind`   | `fraction < elapsed - 0.05`                |


The `0.05` tolerance keeps a goal from flickering between `ahead` and `behind` on consecutive days. When `due_on == start_on`, `elapsed` is `1.0` from the start date onward.

## Services

Implemented. Every use case takes an explicit `Session` as its first parameter, loads table rows, hands `EntryView` / `HabitSpec` / `GoalSpec` values to `atlas.domain`, and commits its own transaction. Slugs are the lookup key except for entries (integer `id`) and milestone toggle (goal slug + milestone name). When `occurred_on` or `as_of` is omitted, the service uses `Settings.today()`.

Failures raise `ServiceError` subclasses the API and CLI will map: `NotFoundError`, `AlreadyExistsError` (duplicate slug), `ValidationError` (bad slug, archived target, missing goal fields, wrong value type).

| Function | Role |
| -------- | ---- |
| `create_area` / `list_areas` / `get_area` / `archive_area` | Areas. Archive stamps `archived_at` (UTC) and hides the row from default lists; areas are never deleted. |
| `create_metric` / `list_metrics` / `get_metric` / `archive_metric` | Metrics, keyed by slug, created under an area slug. `list_metrics` can filter by area and hides archived metrics and metrics whose area is archived. |
| `log_entry` / `amend_entry` / `delete_entry` | Capture and correction. `log_entry` accepts a metric slug and a single `value`; a bool metric with no value stores `true`. Multiple entries per day remain allowed. Logging to an archived metric is rejected; amend and delete still work. |
| `create_habit` / `list_habits` / `get_habit` / `habit_status` | Habits. `weekdays` is valid only for `period = day`. Text metrics cannot be habit targets. `habit_status` returns current/longest streak, adherence from `active_from` to `as_of`, the current bucket's rollup, and whether that bucket is scheduled and satisfied. |
| `create_goal` / `list_goals` / `get_goal` / `goal_progress` / `toggle_milestone` | Goals. `metric_target` requires metric, target, comparator, and measure, and the metric must belong to the goal's area. `milestone` kind forbids those fields. Optional `MilestoneInput` values can be created with the goal. `goal_progress` returns current/baseline/fraction/`target_met` plus `pace_status`. When the target is met and `status` is still `active`, the service sets `status = achieved` and stamps `achieved_at`; it does not reopen an achieved, paused, or abandoned goal. |
| `today_view` / `week_view` / `area_view` | Review. `today_view` is habits whose current bucket is scheduled, entries with `occurred_on = as_of`, and active goals with progress. `week_view` is the ISO week containing `as_of`, one cell per day per habit. `area_view` is one area's non-archived metrics (latest day's rollup), habits, and non-abandoned goals. |
| `export_all` / `import_all` | Port. Export is a JSON-serializable dict keyed by slugs, not integer ids. Import upserts areas, metrics, habits, goals, and milestones by slug (milestones by goal slug + name) and always inserts entries. `replace=True` deletes user rows first. `schema_version` must equal `CURRENT_SCHEMA_VERSION` (1). |
| `seed_demo` | Demo dataset. Builds a payload in the export shape dated relative to `as_of` (default `Settings.today()`) and loads it through `import_all`. Four areas (health, career, finance, relationships), metrics covering every `value_type`, daily/weekly/monthly habits including `at_most` and a weekday mask, both goal kinds, and enough entries for `today_view` / `week_view` / goal progress to be non-empty. Refuses when areas already exist unless `replace=True`. Entries are sourced as `import`. |

Export shape:

```json
{
  "schema_version": 1,
  "areas": [{"slug": "health", "name": "Health", "description": null, "archived_at": null}],
  "metrics": [{"slug": "pushups", "area": "health", "name": "Pushups", "value_type": "count", "unit": "reps", "aggregation": "sum", "direction": "higher_is_better", "archived_at": null}],
  "habits": [{"slug": "pushups-daily", "metric": "pushups", "name": "Pushups Daily", "period": "day", "target_value": 1.0, "comparator": "at_least", "weekdays": null, "active_from": "2026-08-01", "active_to": null}],
  "goals": [{"slug": "bodyweight-75", "area": "health", "name": "Bodyweight 75kg", "kind": "metric_target", "metric": "weight", "target_value": 75.0, "comparator": "at_most", "baseline_value": null, "measure": "latest_value", "start_on": "2026-01-01", "due_on": "2026-12-01", "status": "active", "achieved_at": null}],
  "milestones": [{"goal": "bodyweight-75", "name": "Hit 78kg", "due_on": null, "done_at": null}],
  "entries": [{"metric": "pushups", "occurred_on": "2026-08-10", "occurred_at": null, "value_num": 40.0, "value_bool": null, "value_text": null, "note": "post-travel", "source": "cli", "created_at": "2026-08-10T12:00:00+00:00"}]
}
```

Slugs are normalized to lowercase and must match `[a-z0-9]+(?:-[a-z0-9]+)*`. An omitted `name` defaults to the slug with hyphens turned into spaces and title-cased.

## HTTP API

Status is `implemented` only when the endpoint is merged with tests. Everything else is `planned`.

Routers parse the request, call a service, and serialize. Create/list bodies use slugs (`area`, `metric`) rather than integer foreign keys; entries are addressed by integer `id`. `POST /entries` sets `source` to `api`. Service failures map to HTTP status: `NotFoundError` → 404, `AlreadyExistsError` → 409, `ValidationError` → 400. Pydantic request-shape errors remain 422.

Optional filters the services already support are query parameters: `area` on metrics and goals, `metric` on habits, `status` on goals, `include_archived` on areas and metrics, `as_of` on status/progress/views, and `replace` on import.


| Method   | Path                     | Purpose                                       | Status      |
| -------- | ------------------------ | --------------------------------------------- | ----------- |
| `POST`   | `/entries`               | Record an observation (accepts a metric slug) | implemented |
| `PATCH`  | `/entries/{id}`          | Amend an entry                                | implemented |
| `DELETE` | `/entries/{id}`          | Delete an entry                               | implemented |
| `GET`    | `/areas`                 | List areas                                    | implemented |
| `POST`   | `/areas`                 | Create an area                                | implemented |
| `GET`    | `/metrics`               | List metrics, filterable by area              | implemented |
| `POST`   | `/metrics`               | Create a metric                               | implemented |
| `GET`    | `/habits`                | List habits                                   | implemented |
| `POST`   | `/habits`                | Create a habit                                | implemented |
| `GET`    | `/habits/{slug}/status`  | Streaks and adherence for a habit             | implemented |
| `GET`    | `/goals`                 | List goals                                    | implemented |
| `POST`   | `/goals`                 | Create a goal                                 | implemented |
| `GET`    | `/goals/{slug}/progress` | Progress and pace for a goal                  | implemented |
| `GET`    | `/views/today`           | What is due today and what is logged          | implemented |
| `GET`    | `/views/week`            | The current week across habits                | implemented |
| `GET`    | `/views/areas/{slug}`    | One area's metrics, habits, and goals         | implemented |
| `GET`    | `/export`                | Full JSON export                              | implemented |
| `POST`   | `/import`                | Full JSON import                              | implemented |


There is no authentication. The app binds to localhost only (`127.0.0.1`). Tests use FastAPI `TestClient` against `create_app(session_factory=...)` with in-memory SQLite; they never start a live server.

## CLI

Four verbs, deliberately unequal in weight: capture is one line, everything else may cost a few keystrokes. Review commands print Rich tables; `atlas today` is a two-column dashboard (daily habits left, weekly/monthly habits right, then logged entries and goals).


| Command                                        | Purpose                                                                                                                            | Status      |
| ---------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| `atlas init`                                   | Create the SQLite file and schema at `ATLAS_DB`                                                                                    | implemented |
| `atlas seed`                                   | Load a demo dataset dated relative to today (or `--on`). Refuses if the database already has areas unless `--replace`.             | implemented |
| `atlas log <metric> [value]`                   | Capture, the hot path: `atlas log pushups 40`, `atlas log meditated`, `atlas log weight 78.4 --on 2026-08-10 --note "post-travel"`. Metric slugs accept a unique prefix (`push` → `pushups`). | implemented |
| `atlas area add <slug>`                        | Define an area                                                                                                                     | implemented |
| `atlas metric add <slug> --area --type --agg`  | Define a metric                                                                                                                    | implemented |
| `atlas habit add --metric --period --at-least` | Define a habit. Slug is optional and defaults to `{metric}-{period}`. Comparator is exactly one of `--at-least`, `--at-most`, `--exactly`. | implemented |
| `atlas goal add <name> --metric --target --by` | Define a goal. Area is inferred from the metric when `--area` is omitted; slug is derived from the name. `--at-most` / `--at-least` / `--exactly` are flags; `--cumulative` selects `cumulative_since_start`. | implemented |
| `atlas today`                                  | Review dashboard: daily habits (left) and weekly/monthly habits (right) when the terminal is wide enough, otherwise stacked; then logged entries and active goals. `--on` selects the local date. | implemented |
| `atlas week`                                   | Review: the week across habits                                                                                                     | implemented |
| `atlas area <slug>`                            | Review: one area                                                                                                                   | implemented |
| `atlas habit <slug>`                           | Review: one habit's streak and adherence                                                                                           | implemented |
| `atlas goals`                                  | Review: goals with progress and pace                                                                                               | implemented |
| `atlas entry amend <id>`                       | Correct an entry                                                                                                                   | implemented |
| `atlas entry rm <id>`                          | Delete an entry                                                                                                                    | implemented |
| `atlas export`                                 | Write a JSON export to stdout                                                                                                      | implemented |
| `atlas import <file>`                          | Load a JSON export. `--replace` clears user rows first.                                                                            | implemented |




## Configuration


| Variable   | Default                         | Meaning                                                                      |
| ---------- | ------------------------------- | ---------------------------------------------------------------------------- |
| `ATLAS_DB` | `~/.local/share/atlas/atlas.db` | SQLite database file; the parent directory is created if missing             |
| `ATLAS_TZ` | system local timezone           | IANA name (`Europe/Berlin`) used to resolve "today" into `Entry.occurred_on` |


`atlas/settings.py` reads both into a frozen `Settings` value object via `load_settings(env=None)`, which defaults to `os.environ` and accepts an explicit mapping so tests never mutate the real environment. `~` in `ATLAS_DB` is expanded; a blank or unset value falls back to the default. An `ATLAS_TZ` that is not a known IANA zone raises `SettingsError` at load time instead of silently drifting to UTC. `Settings.today()` is the single place the wall clock is read for occurrence dates.

Resolving the path is deliberately side-effect free: the database file and its parent directory are created by the engine module, not by reading configuration.

The API is served with `uv run uvicorn atlas.api.app:app --reload`, bound to `127.0.0.1`. Single user, no auth, no remote exposure.

## Development

Python 3.12, managed entirely with `uv`. Every command goes through it: `uv add`, `uv sync`, `uv run pytest`, `uv run ruff check`. Never bare `pip`, `python`, `pytest`, or `ruff`.

Dependencies are declared in `pyproject.toml` and pinned in `uv.lock`; `uv_build` is the build backend. Ruff and pytest are configured in the same `pyproject.toml`: ruff at line length 100 targeting `py312` with `E`, `F`, `I`, `UP`, `B`, `SIM`, and `TID` selected, pytest with `testpaths = ["tests"]` and `--strict-markers --strict-config`.

Tests by layer:


| Layer      | How it is tested                                         |
| ---------- | -------------------------------------------------------- |
| `domain`   | Plain lists and dataclasses, no database                 |
| `services` | In-memory SQLite session                                 |
| `api`      | FastAPI `TestClient`, no live server                     |
| `cli`      | Typer's runner where it adds value; prefer service tests |


One todo, one commit. Each cycle implements a single todo, gets `uv run ruff check` and `uv run pytest` clean, updates this document, and lands one focused commit.

## Development log

Append-only, one entry per cycle. Newest last.

- **2026-08-12 —** `rules-first` — Added the four Cursor rules under `.cursor/rules/`: `architecture.mdc` (layering and import bans, data principles), `tooling.mdc` (uv-only commands, pre-commit gates, one todo per commit), `documentation.mdc` (this file is updated in the same cycle as the behavior it describes), and `python-conventions.mdc` (type hints, explicit `Session` first parameter, domain purity, per-layer test conventions).
- **2026-08-12 —** `docs-living` — Created `docs/architecture.md` as the living source of truth: purpose, field-level data model for `Area`, `Metric`, `Entry`, `Habit`, `Goal`, and `Milestone`, layering with the import rules, precise definitions of bucketing, rollup, habit satisfaction, streaks, adherence, goal progress, and pace status, the planned API and CLI surface with per-item status, and configuration. No code yet; every endpoint and command is `planned`.
- **2026-08-12 —** `scaffold` — Scaffolded the project with `uv init --lib` (src layout at `src/atlas/`), added `fastapi`, `uvicorn`, `sqlmodel`, `typer`, `rich` and dev `pytest`, `ruff`, created the empty `domain`, `db`, `services`, `api`, and `cli` packages, configured ruff and pytest in `pyproject.toml`, and added `atlas/settings.py` reading `ATLAS_DB` and `ATLAS_TZ` into a frozen `Settings` (six tests). The domain import ban is now enforced by ruff's banned-api rule rather than by review alone. No tables, endpoints, or commands yet.
- **2026-08-13 —** `domain` — Implemented `atlas/domain/`: enums (`ValueType`, `Aggregation`, `Direction`, `Period`, `Comparator`, `GoalKind`, `GoalStatus`, plus `Measure`, `Source`, `PaceStatus`), value objects (`EntryView`, `HabitSpec`, `GoalSpec`, `MilestoneView`, `Bucket`, `GoalProgress`), and the pure calculation functions for period bucketing, rollups, habit satisfaction, `current_streak`, `longest_streak`, `adherence`, `goal_progress`, and `pace_status`. Unit tests cover the definitions in this document over plain lists; no database.
- **2026-08-13 —** `persistence` — Implemented `atlas/db/`: SQLModel tables for `Area`, `Metric`, `Entry`, `Habit`, `Goal`, `Milestone`, and `schema_version`; unique slugs; index on `Entry(metric_id, occurred_on)`; engine, in-memory engine, and session factory; `create_all` with `CURRENT_SCHEMA_VERSION = 1`. `atlas init` creates the database file (and parent directory) at `ATLAS_DB` and is idempotent.
- **2026-08-13 —** `services` — Implemented `atlas/services/`: `log_entry` / `amend_entry` / `delete_entry`, create/list/archive for areas and metrics, `create_habit` + `habit_status`, `create_goal` + `goal_progress` + `toggle_milestone`, `today_view` / `week_view` / `area_view`, and `export_all` / `import_all`. Services take an explicit session, look up by slug, call domain for derived values, and stamp `achieved` when a goal's target is met. Tests use in-memory SQLite.
- **2026-08-13 —** `api` — Implemented `atlas/api/`: FastAPI app with Pydantic request/response schemas and routers for entries, areas, metrics, habits, goals, views, and export/import. Session dependency yields from a factory; service errors map to 404/409/400; uvicorn entrypoint binds `127.0.0.1`. Endpoint tests use `TestClient` over in-memory SQLite.
- **2026-08-13 —** `cli` — Implemented `atlas/cli/`: Typer app over the same services in-process. Commands: `log` (fuzzy metric slug), `area add` / `area <slug>`, `metric add`, `habit add` / `habit <slug>`, `goal add`, `goals`, `today`, `week`, `entry amend` / `entry rm`, `export`, `import`. Rich tables for review; service errors exit 1. Tests use Typer's `CliRunner` against a temp SQLite file.
- **2026-08-13 —** `docs-seed` — Added `seed_demo` and `atlas seed` (demo dataset dated relative to today, `--replace` to overwrite). README covers install and run for uv, the CLI, and the localhost API, and links to this document rather than duplicating it. Final pass: every planned endpoint and command is `implemented`.
- **2026-08-13 —** `cli-dashboard` — Restyled `atlas today` as a Rich dashboard: shared panel/column helpers in `format.py`, daily habits as a left checklist, weekly/monthly habits (e.g. family calls) on the right, logged entries and goals below. Console width follows the terminal. Capture output unchanged.

