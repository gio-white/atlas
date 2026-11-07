# Screen Time data source

Ingestion: `POST /screen/sessions`. Display: [screen time](../domain/screen-time.md).
Principle and shared rules: [overview](overview.md).

## Expected fields

| Field | Required | Notes |
| ----- | -------- | ----- |
| `app` | yes | slug of an existing screen app |
| `device` | no | slug of a screen device; missing is shown as Unknown |
| `started_at`, `ended_at` | interval shape | UTC; both set, end after start; minutes are derived |
| `minutes`, `occurred_on` | duration shape | when there is no interval; `minutes > 0` |
| `note` | no | free text |

Interval sessions feed the hour heatmap and time-based insights; duration-only sessions count
toward totals only. Each session also writes a backing entry on the app's metric so habits on
that metric keep working.

## Timezones

Interval sessions are attributed to local hours and days in `ATLAS_TZ`, clipped at midnight.
Send UTC.

## De-duplication

Not handled yet (see [overview](overview.md#ingestion-contract)).

## Sources

To be decided (phone and computer usage exports). Until then the demo seed provides synthetic
sessions.
