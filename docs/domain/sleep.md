# Sleep

## Purpose

Nights of sleep with optional stages, shown as last night and a rolling range (week, month, or 90 days). Sleep is display-only: nights arrive from a data source, never from a form ([decision 0004](../decisions/0004-device-data-is-display-only.md)).

## Concepts

- **Sleep session** — one night or nap, keyed by its local wake date.
- **Stage** — `awake`, `rem`, `light`, or `deep`.
- **Sleep range** — the rolling window of `days` nights ending at `as_of` (7 by default; the Sleep page offers 7, 30, and 90).
- **Consistency** — how much bedtime and wake time vary across the range (a spread in minutes).
- **Freshness** — when the newest night arrived (`last_recorded_at`).

Where the data comes from: [data sources](../data-sources/sleep.md).

## Data model

### SleepSession

One stored night (or nap): when you went to bed and when you woke up. Sleep is a dedicated fact store like the library: it does not dual-write entries and has no metric or area. `occurred_on` is the **local wake date** in `ATLAS_TZ`, so last night's sleep belongs to today. Nights arrive through `POST /sleep/sessions`, the ingestion contract for a future pipeline ([data sources](../data-sources/sleep.md)); stages are optional. The web app has no form for it.

| Field         | Type        | Notes                                              |
| ------------- | ----------- | -------------------------------------------------- |
| `id`          | int         | primary key                                        |
| `started_at`  | datetime    | UTC; bedtime                                       |
| `ended_at`    | datetime    | UTC; wake time; must be after `started_at`         |
| `occurred_on` | date        | local date of `ended_at` in `ATLAS_TZ`; indexed    |
| `note`        | str \| None |                                                    |
| `source`      | enum        | `cli \| api \| import`                             |
| `created_at`  | datetime    | UTC                                                |

### SleepSessionStage

One contiguous sleep phase inside a session. Stages must fall inside the session interval, end after they start, and not overlap; gaps are allowed (untracked time).

| Field        | Type     | Notes                              |
| ------------ | -------- | ---------------------------------- |
| `id`         | int      | primary key                        |
| `session_id` | int      | FK to `SleepSession`; indexed      |
| `stage`      | enum     | `awake \| rem \| light \| deep`    |
| `started_at` | datetime | UTC                                |
| `ended_at`   | datetime | UTC                                |

## Rules and calculations

### Sleep week

`sleep_week_math` is a pure function of `SleepSessionView` rows, `as_of`, an explicit timezone, and `days` (default 7, at least 1). The window is the **rolling `days` days ending at `as_of`** (`range_start = as_of - (days - 1)`, `range_end = as_of`; not the ISO week), one row per local wake date. A day with no night has `night = null`; the Sleep page shows it as **No data**.

- **Night per day** — the session with the longest interval whose `occurred_on` is that day (naps lose to the main night). `night` is the `as_of` row (last night).
- **Offsets** — `bed_offset` / `wake_offset` and each stage segment's `start_offset` / `end_offset` are minutes relative to local midnight starting the wake date (`-50` is 23:10 the evening before, `425` is 07:05). The SPA plots and formats these; it never converts timezones.
- **In bed** — `ended_at - started_at` in minutes.
- **Asleep** — sum of `rem + light + deep` stage minutes when the night has stages, else the full in-bed interval.
- **Stage minutes** — summed per stage (`awake`, `rem`, `light`, `deep`).
- **Averages** — mean asleep minutes, bed offset, and wake offset over logged nights in the window (`null` with none); mean stage minutes over nights that have stages (`null` with none). `nights_logged` counts days with a night.
- **Spread** — `bed_spread` / `wake_spread` are the population standard deviation of the bed and wake offsets (minutes) over the nights in the window; `null` with fewer than two nights. The page labels a spread ≤ 30 min **Steady**, ≤ 60 min **Varies a little**, otherwise **Irregular**.
- **Last recorded** — `last_recorded_at` is the newest `created_at` over **every** stored session, not only the window, so it reports how fresh the data is (`null` with none).

## API

Conventions shared by every endpoint (slugs, `as_of`, errors): [api-conventions](../architecture/api-conventions.md).

| Method   | Path                     | Purpose                                       | Status      |
| -------- | ------------------------ | --------------------------------------------- | ----------- |
| `GET`    | `/sleep/view`            | Last night plus the rolling window (`as_of`, `days` 1–366, default 7; out of range → 422) | implemented |
| `GET`    | `/sleep/sessions`        | List sleep sessions (`occurred_on`)               | implemented |
| `POST`   | `/sleep/sessions`        | Ingest a night (`started_at`, `ended_at`, optional `stages`); the pipeline contract, no UI | implemented |
| `GET`    | `/sleep/sessions/{id}`   | Get one sleep session with stages                 | implemented |
| `DELETE` | `/sleep/sessions/{id}`   | Delete a sleep session and its stages (API only; no UI) | implemented |

Service functions (in `src/atlas/services/`, each taking an explicit `Session` first; see [overview](../architecture/overview.md#services)):

| Function | Role |
| -------- | ---- |
| `log_sleep_session` / `list_sleep_sessions` / `get_sleep_session` / `sleep_stages` / `delete_sleep_session` / `sleep_view` | Sleep. `log_sleep_session` validates the interval and stages through `resolve_sleep_session`, derives `occurred_on` from the wake time in `ATLAS_TZ`, and stores the session plus its stages. Delete removes the stages first. `sleep_view(as_of, days)` checks `1 ≤ days ≤ 366` (`ValidationError` otherwise) and is `sleep_week_math` over every stored session. |

## Screens

`/stats/sleep` (Stats → Sleep) is read-only and reads `GET /sleep/view?days=N` only:

- **Range** — Week / Month / 90 days (7 / 30 / 90 days), kept in the URL as `?range=month` or `?range=quarter` (week is the default and has no parameter).
- **Last updated** — from `last_recorded_at` ("Last updated today at 08:22").
- **Stat tiles** — average asleep, average bedtime and average wake each with the consistency label and spread ("Steady · ±30m"), and missing nights.
- **Time asleep** — one bar per day with the range average as a dashed line; a day without a night is a dashed **No data** column.
- **Bedtime and wake** — a bed → wake bar per day, coloured by stage, with dashed average lines in the muted colour; a night without stages is grey; the top time label is padded so it is never clipped.
- **Stage split** — average minutes and share per stage over nights with stages.
- **Nights** — read-only list, newest first; missing days appear as "No data" rows.
- **Empty state** — with no nights at all: "No sleep data yet. It will appear here once a data source is connected."

Colours are the shared chart tokens ([design system](../product/design-system.md#colour)): Asleep is the first series colour and the stages keep their fixed slots. There is no capture, edit, or delete control. Charts live in `web/src/components/sleep/SleepCharts.tsx`; range and consistency helpers in `web/src/lib/sleep.ts`; the "Last updated" wording in `web/src/lib/freshness.ts`. The Home Sleep card is described in [home](home.md).

Route inventory with status: [navigation](../product/navigation.md).

## Tests

- `tests/domain/test_sleep.py`
- `tests/services/test_sleep.py`
- `tests/api/test_sleep.py`
- `web/src/lib/sleep.test.ts`, `web/src/lib/freshness.test.ts`
- `web/src/pages/displayOnly.test.tsx` (no capture controls, No data gaps, range request, empty state)

## Status

Implemented and display-only (Track T3 phase 1, decision [0004](../decisions/0004-device-data-is-display-only.md)). The pipeline that feeds it is future work ([data sources](../data-sources/sleep.md)).
