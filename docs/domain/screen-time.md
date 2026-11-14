# Screen Time

## Purpose

App usage sessions classified by category and judgment, with caps and a period dashboard.

## Concepts

- **Category** — a bucket of apps carrying the judgment (`useful`, `waste`, `neutral`).
- **App** — what you used; one category and one backing duration metric.
- **Budget (cap)** — a threshold over all screen time, a judgment, or a category.
- **Device** — where a session happened; optional.
- **Session** — the stored fact: an interval or a duration.

Where the data comes from: [data sources](../data-sources/screen-time.md).

## Data model

### ScreenCategory

A named bucket for screen apps, such as entertainment or learning. The **judgment** (`useful | waste | neutral`) lives here, not on the app. Reclassifying entertainment from waste to useful moves every member app's minutes into a different judgment total on the next read.

Screen taxonomy is a dedicated slice of Atlas. Each app gets a backing duration metric with the origin `screen` ([trackers and entries](trackers-and-entries.md#data-model)) so sessions stay ordinary entries. Those metrics are not listed in Settings → Metrics, and their entries are the automatic data All entries hides by default.

| Field         | Type            | Notes                                      |
| ------------- | --------------- | ------------------------------------------ |
| `id`          | int             | primary key                                |
| `slug`        | str             | unique (`entertainment`)                   |
| `name`        | str             |                                            |
| `judgment`    | enum            | `useful \| waste \| neutral`               |
| `archived_at` | datetime \| None | UTC                                       |

### ScreenApp

What you used: Instagram, YouTube, a code editor. One category. One backing duration metric (`sum`, unit `min`). `metric.direction` mirrors the category's current judgment (`useful` → `higher_is_better`, `waste` → `lower_is_better`, `neutral` → `neutral`). Changing a category's judgment updates member metrics. Grouping on the screen view always uses category → judgment, not a copy on the app.

| Field         | Type            | Notes                                         |
| ------------- | --------------- | --------------------------------------------- |
| `id`          | int             | primary key                                   |
| `slug`        | str             | unique (`instagram`); same slug as the metric |
| `name`        | str             |                                               |
| `category_id` | int             | FK to `ScreenCategory`                        |
| `metric_id`   | int             | unique FK to `Metric`                         |
| `archived_at` | datetime \| None | UTC                                          |

### ScreenBudget

A threshold over **all screen time**, a **judgment**, or a **category**, not over a single metric. "At most 3 hours of screen time a day" is `target_kind=total` (its `target_slug` is always `all`); Home shows today's total against an active daily cap of this kind ([home](home.md)). "Keep waste under 90 minutes a day" is `target_kind=judgment`, `target_slug=waste`, `comparator=at_most`. An entertainment cap uses `target_kind=category`. App-level caps stay ordinary habits on the app's metric.

`screen_view` and `screen_dashboard` read `screen_session` on read. Capture still dual-writes a backing entry so habits on the app metric keep working. Totals, score, heatmap, and insights are never stored.

| Field          | Type            | Notes                                      |
| -------------- | --------------- | ------------------------------------------ |
| `id`           | int             | primary key                                |
| `slug`         | str             | unique                                     |
| `name`         | str             | e.g. Waste cap                             |
| `target_kind`  | enum            | `total \| judgment \| category`            |
| `target_slug`  | str             | `all`, `waste`, or `entertainment`         |
| `period`       | enum            | `day \| week \| month`                     |
| `target_value` | float           | minutes                                    |
| `comparator`   | enum            | `at_least \| at_most \| exactly`           |
| `active_from`  | date            | inclusive                                  |
| `active_to`    | date \| None    | inclusive; `None` means open-ended         |

### ScreenDevice

A device that can host a session: iPhone, MacBook. Optional on each session. Null device is shown as Unknown on the dashboard.

| Field         | Type             | Notes                |
| ------------- | ---------------- | -------------------- |
| `id`          | int              | primary key          |
| `slug`        | str              | unique (`iphone`)    |
| `name`        | str              |                      |
| `archived_at` | datetime \| None | UTC                  |

### ScreenSession

The stored screen-time fact. Two valid shapes: an **interval** (`started_at` and `ended_at` both set, UTC, `ended_at > started_at`) or **duration-only** (both timestamps null, `minutes > 0`, `occurred_on` set). When the interval is present it is the source: `minutes` is derived as `(ended_at - started_at)` in fractional minutes. Duration-only sessions count toward totals; they do not contribute to hour heatmaps or time-based insights.

Capture (`POST /screen/sessions`) writes the session and a matching backing `entry` on the app metric. Logging to that metric via `POST /entries` also inserts a duration-only session. Amend and delete keep the pair in sync through optional unique `entry_id`.

| Field         | Type             | Notes                                                                 |
| ------------- | ---------------- | --------------------------------------------------------------------- |
| `id`          | int              | primary key                                                           |
| `app_id`      | int              | FK to `ScreenApp`                                                     |
| `device_id`   | int \| None      | optional FK to `ScreenDevice`                                         |
| `started_at`  | datetime \| None | UTC; both null or both set                                            |
| `ended_at`    | datetime \| None | UTC; must be after `started_at`                                       |
| `minutes`     | float            | always stored, always `> 0`; derived from the interval when present   |
| `occurred_on` | date             | local date in `ATLAS_TZ`; from `started_at` when interval is present  |
| `note`        | str \| None      |                                                                       |
| `source`      | enum             | `cli \| api \| import`                                                |
| `created_at`  | datetime         | UTC                                                                   |
| `entry_id`    | int \| None      | unique FK to the dual-written `Entry`                                 |

## Rules and calculations

### Screen dashboard

`screen_dashboard_math` is a pure function of `ScreenSessionView` rows, `as_of`, `period`, and an explicit timezone (no wall clock). Interval sessions are the source of truth for when minutes happened: hour buckets and local-day attribution **clip** `started_at`–`ended_at` into each local hour and day in `ATLAS_TZ` (a 23:30–00:45 session contributes 30m to hour 23 on day D and 45m to hour 0 on day D+1). Duration-only sessions add `minutes` on `occurred_on` and are omitted from the heatmap, late-night share, and sequences.

The current range is `bucket_for(as_of, period)` clipped so an in-progress week or month ends at `as_of`. The previous range is like-for-like elapsed days, not a full previous bucket against a partial current one: previous calendar day; previous ISO week Monday through the same weekday; previous calendar month day 1 through the same elapsed day-of-month (capped at the previous month's last day).

- **Total** — sum of attributed minutes in range (`None` if no sessions).
- **Daily average** — total / elapsed days in the clipped range (zeros included).
- **Longest day** — `{ date, minutes }` of the max daily sum.
- **Delta** — `current - previous` minutes, and `(current - previous) / previous` when previous `> 0`, else `null`.
- **Score** — `round(100 * (useful + 0.5 * neutral) / total)` when total `> 0`, else `null`. Band: `>= 70` good, `>= 40` ok, else poor.
- **Apps / categories / devices** — ranked by minutes with share of total. Null device is slug `unknown`, name `Unknown`.
- **Daily series** — one bar per day: useful / waste / neutral / total.
- **Comparison series** — aligned day index `{ current, previous }`.
- **Hours** — interval sessions only. Grid: 1×24 (day), 7×24 Monday–Sunday (week), weekday-average × 24 (month).
- **Trend** — last 8 ISO weeks of daily average ending at `as_of`.
- **Last recorded** — `last_recorded_at` is the newest `created_at` over **every** screen session (`latest_screen_recorded_at`), not only the range, so it reports how fresh the data is (`null` with none).
- **Insights** — derived, not stored. Totals-based: weekend spike (weekend daily avg `>` weekday avg × 1.25), waste share `> 0.4`, improving (`delta_fraction <= -0.1`). Time-based (interval sessions only): late-night minutes overlapping 22:00–05:00 local `> 20%` of interval-attributed minutes; sequences where B starts within 15 minutes of A ending, surfacing the top `(app_a, app_b)` pair. Each insight includes one prescription. Missing or broken waste caps add a budget insight in the service.

`screen_view` (today) and budget status use the same session attribution. Budget member minutes are interval-clipped to the local day, or `occurred_on` for duration-only.

## API

Conventions shared by every endpoint (slugs, `as_of`, errors): [api-conventions](../architecture/api-conventions.md).

| Method   | Path                     | Purpose                                       | Status      |
| -------- | ------------------------ | --------------------------------------------- | ----------- |
| `GET`    | `/screen/view`           | Screen totals, sessions, and budget status    | implemented |
| `GET`    | `/screen/dashboard`      | Period dashboard (`period`, `as_of`); includes `last_recorded_at` | implemented |
| `GET`    | `/screen/categories`     | List screen categories                        | implemented |
| `POST`   | `/screen/categories`     | Create a screen category                      | implemented |
| `GET`    | `/screen/categories/{slug}` | Get one screen category                    | implemented |
| `PATCH`  | `/screen/categories/{slug}` | Update name and judgment                   | implemented |
| `GET`    | `/screen/apps`           | List screen apps                              | implemented |
| `POST`   | `/screen/apps`           | Create a screen app and backing metric        | implemented |
| `GET`    | `/screen/apps/{slug}`    | Get one screen app                            | implemented |
| `PATCH`  | `/screen/apps/{slug}`    | Update name and category                      | implemented |
| `GET`    | `/screen/budgets`        | List screen budgets                           | implemented |
| `POST`   | `/screen/budgets`        | Create a screen budget                        | implemented |
| `GET`    | `/screen/budgets/{slug}` | Get one screen budget                         | implemented |
| `PATCH`  | `/screen/budgets/{slug}` | Update name, target, value, comparator, `active_to` | implemented |
| `GET`    | `/screen/devices`        | List screen devices                               | implemented |
| `POST`   | `/screen/devices`        | Create a screen device                            | implemented |
| `GET`    | `/screen/devices/{slug}` | Get one screen device                             | implemented |
| `PATCH`  | `/screen/devices/{slug}` | Update name                                       | implemented |
| `GET`    | `/screen/sessions`       | List screen sessions (`occurred_on`)              | implemented |
| `POST`   | `/screen/sessions`       | Ingest a session (interval or duration); the pipeline contract, no UI | implemented |
| `GET`    | `/screen/sessions/{id}`  | Get one screen session                            | implemented |
| `PATCH`  | `/screen/sessions/{id}`  | Amend a screen session (API only; no UI)          | implemented |
| `DELETE` | `/screen/sessions/{id}`  | Delete a screen session and paired entry (API only; no UI) | implemented |

Service functions (in `src/atlas/services/`, each taking an explicit `Session` first; see [overview](../architecture/overview.md#services)):

| Function | Role |
| -------- | ---- |
| `create_screen_category` / `list_screen_categories` / `get_screen_category` / `update_screen_category` | Screen categories. `update_screen_category` may change name and judgment; a judgment change updates member metrics' `direction`. `archived_at` is honored on list (`include_archived`) and import; there is no archive endpoint. |
| `create_screen_app` / `list_screen_apps` / `get_screen_app` / `update_screen_app` | Screen apps. Create inserts a duration/`sum`/`min` metric with origin `screen` and the same slug and a direction from the category judgment. `update_screen_app` may change name (synced onto the metric) and category (direction follows the new category). `archived_at` is honored on list (`include_archived`) and import; there is no archive endpoint. |
| `create_screen_budget` / `list_screen_budgets` / `get_screen_budget` / `update_screen_budget` | Screen budgets targeting all screen time (`total`, every app counts; `target_slug` is set to `all`, defaulting there when left out), a judgment, or a category. Judgment `target_slug` must be `useful`, `waste`, or `neutral`; category targets must name an existing category. |
| `create_screen_device` / `list_screen_devices` / `get_screen_device` / `update_screen_device` | Screen devices. `update_screen_device` may change name. `archived_at` is honored on list (`include_archived`) and import; there is no archive endpoint. |
| `log_screen_session` / `list_screen_sessions` / `get_screen_session` / `update_screen_session` / `delete_screen_session` | Screen sessions. Provide `started_at`+`ended_at` or `minutes`. Interval minutes are derived; a client `minutes` must match within `0.01`. Dual-writes a backing entry. Amend/delete keep the pair in sync. |
| `screen_view` | Review for `as_of`: minutes per app and category that day from sessions (interval-clipped), judgment totals, today's sessions, and each budget's current rollup, satisfaction, streak, and adherence over merged member-app session minutes. |
| `screen_dashboard` | Period dashboard (`day` / `week` / `month`) from sessions: totals, score, apps, categories, devices, daily and comparison series, hour heatmap, 8-week trend, insights/prescriptions, budgets, and `last_recorded_at`. |

## Screens

`/stats/screen-time` (Stats → Screen time) is the read-only period dashboard from `GET /screen/dashboard` (Day / Week / Month in the query string). Sessions arrive from a data source ([decision 0004](../decisions/0004-device-data-is-display-only.md)); there is no form to log, edit, or delete a session.

- **Last updated** — from `last_recorded_at`.
- **Totals** — total, daily average, longest day, and the score. The score is explained in plain words: "How much of your screen time went to apps you count as Good. Neutral time counts for half." Judgments are labelled Good / Bad / Neutral on screen (`useful` / `waste` / `neutral` in the API).
- **Each day** — daily bars with a minutes y-axis, day labels, and a Good / Neutral / Bad legend when split; a toggle switches between the total and the split.
- **Categories** — each category has its own colour (`CATEGORY_PALETTE` in `web/src/components/screen/Charts.tsx`, assigned by alphabetical slug and never a good/bad/warn colour, so a colour does not read as a judgment); the legend shows minutes and the judgment.
- **Apps, devices, hours heatmap, comparison, 8-week trend, insights** — as computed above.
- **Caps** — read-only status of each cap (`current / target`); with none: "No caps set. Add one in Settings."
- **Empty state** — with no sessions at all: "No screen time data yet. It will appear here once a data source is connected."
- **Setup link** — at the bottom, "Set up apps, categories and caps" goes to Settings → Screen time setup. The Screen time page itself has no configuration controls.

Configuration lives in Settings, apart from the data:

- **Settings → Screen time setup** (`/settings/screen-time`, `ScreenTimeSetupPage`) renders `ScreenTimeSettings` (`web/src/components/settings/ScreenTimeSettings.tsx`: Good / Bad / Neutral per category, each app's category, and caps — add, edit name / rule / minutes, End sets `active_to` to as-of and Resume clears it; an end date is inclusive).
- **Settings → Devices** (`/settings/devices`, `DevicesPage`) renders `DataSourcesSettings` (`web/src/components/settings/DataSourcesSettings.tsx`: device names).
- New categories, apps, and devices are added by name; the slug is generated and never shown. Both components load their own data.

Home's **Screen time today** block is described in [home](home.md#screens).

Route inventory with status: [navigation](../product/navigation.md).

## Tests

- `tests/domain/test_screen.py`
- `tests/services/test_screen.py` (including a cap on all screen time)
- `tests/api/test_screen.py`
- `web/src/lib/screenManage.test.ts`, `web/src/components/screen/Charts.test.ts`, `web/src/lib/freshness.test.ts`
- `web/src/pages/displayOnly.test.tsx` (no capture controls or setup controls on the Screen time page, the link to Settings, empty state, distinct category colours; the Screen time setup and Devices pages hold the configuration)

## Status

Implemented and display-only (Track T3 phase 1, decision [0004](../decisions/0004-device-data-is-display-only.md)). Configuration is in Settings → Screen time setup and Settings → Devices (redesign brief, phase 2). The cap form offers **All screen time**, **Apps that count as…** (Good, Bad, Neutral), or **One category**, for each **Day**, **Week**, or **Month**. The insight text in `src/atlas/domain/screen.py` still says "waste" where the UI says Bad (handed to the polish sweep, T6).
