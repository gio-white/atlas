# Sleep

## Purpose

Nights of sleep with optional stages, shown as last night and a rolling week.

## Concepts

- **Sleep session** — one night or nap, keyed by its local wake date.
- **Stage** — `awake`, `rem`, `light`, or `deep`.
- **Sleep week** — the rolling 7 nights ending at `as_of`.

Where the data comes from: [data sources](../data-sources/sleep.md).

## Data model

### SleepSession

One stored night (or nap): when you went to bed and when you woke up. Sleep is a dedicated fact store like entertainment: it does not dual-write entries and has no metric or area. `occurred_on` is the **local wake date** in `ATLAS_TZ`, so last night's sleep belongs to today. Capture is `POST /sleep/sessions` (stages are optional; a tracker import supplies them).

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

`sleep_week_math` is a pure function of `SleepSessionView` rows, `as_of`, and an explicit timezone. The window is the **rolling 7 days ending at `as_of`** (not the ISO week), one row per local wake date.

- **Night per day** — the session with the longest interval whose `occurred_on` is that day (naps lose to the main night). `night` is the `as_of` row (last night).
- **Offsets** — `bed_offset` / `wake_offset` and each stage segment's `start_offset` / `end_offset` are minutes relative to local midnight starting the wake date (`-50` is 23:10 the evening before, `425` is 07:05). The SPA plots and formats these; it never converts timezones.
- **In bed** — `ended_at - started_at` in minutes.
- **Asleep** — sum of `rem + light + deep` stage minutes when the night has stages, else the full in-bed interval.
- **Stage minutes** — summed per stage (`awake`, `rem`, `light`, `deep`).
- **Averages** — mean asleep minutes, bed offset, and wake offset over logged nights in the window (`null` with none); mean stage minutes over nights that have stages (`null` with none). `nights_logged` counts days with a night.

## API

Conventions shared by every endpoint (slugs, `as_of`, errors): [api-conventions](../architecture/api-conventions.md).

| Method   | Path                     | Purpose                                       | Status      |
| -------- | ------------------------ | --------------------------------------------- | ----------- |
| `GET`    | `/sleep/view`            | Last night plus the rolling 7-night window (`as_of`) | implemented |
| `GET`    | `/sleep/sessions`        | List sleep sessions (`occurred_on`)               | implemented |
| `POST`   | `/sleep/sessions`        | Log a night (`started_at`, `ended_at`, optional `stages`) | implemented |
| `GET`    | `/sleep/sessions/{id}`   | Get one sleep session with stages                 | implemented |
| `DELETE` | `/sleep/sessions/{id}`   | Delete a sleep session and its stages             | implemented |

Service functions (in `src/atlas/services/`, each taking an explicit `Session` first; see [overview](../architecture/overview.md#services)):

| Function | Role |
| -------- | ---- |
| `log_sleep_session` / `list_sleep_sessions` / `get_sleep_session` / `sleep_stages` / `delete_sleep_session` / `sleep_view` | Sleep. `log_sleep_session` validates the interval and stages through `resolve_sleep_session`, derives `occurred_on` from the wake time in `ATLAS_TZ`, and stores the session plus its stages. Delete removes the stages first. `sleep_view` is `sleep_week_math` over every stored session. |

## Screens

`/sleep` reuses the Home Sleep card and lists the last 60 nights from `GET /sleep/sessions` (bed → wake, time in bed, stage count, note) with a confirmed delete. The Home Sleep card is described in [home](home.md).

Route inventory with status: [navigation](../product/navigation.md).

## Tests

- `tests/domain/test_sleep.py`
- `tests/services/test_sleep.py`
- `tests/api/test_sleep.py`
- `web/src/lib/sleep.test.ts`

## Status

Implemented. Becoming display-only (Track T3, decision [0004](../decisions/0004-device-data-is-display-only.md)).
