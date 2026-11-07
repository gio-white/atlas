# Sleep data source

Ingestion: `POST /sleep/sessions`. Display: [sleep](../domain/sleep.md). Principle and shared
rules: [overview](overview.md).

## Expected fields

| Field | Required | Notes |
| ----- | -------- | ----- |
| `started_at` | yes | UTC bedtime |
| `ended_at` | yes | UTC wake time; after `started_at` |
| `stages` | no | list of `{stage, started_at, ended_at}`; `stage` is `awake`, `rem`, `light`, or `deep`; inside the session, non-overlapping, gaps allowed |
| `note` | no | free text |

## Timezones

The night belongs to the **local wake date** in `ATLAS_TZ`: last night's sleep counts for
today. Send UTC; never pre-convert.

## De-duplication

Not handled yet (see [overview](overview.md#ingestion-contract)).

## Sources

To be decided (phone or watch export). Until then the demo seed provides synthetic nights.
