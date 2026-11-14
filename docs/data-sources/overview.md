# Data sources

Some data in Atlas is not typed in by you; it comes from devices. Today that is **Sleep** and
**Screen Time**.

## Display-only principle

Sleep and Screen Time are **display-only** in the web app. Their pages show data; they do not
offer a way to type, edit, or delete nights or app sessions. The data will arrive through a
pipeline built later. Until then the demo seed (`uv run atlas seed`) fills both with synthetic
data. The reasoning is recorded in [decision 0004](../decisions/0004-device-data-is-display-only.md).

What is *configuration* rather than data — which category an app belongs to, whether a
category counts as good or bad, daily caps, device names — stays editable. It lives in Settings, apart from the display:
**Screen time setup** (`web/src/components/settings/ScreenTimeSettings.tsx`) and **Devices**
(`DataSourcesSettings.tsx`). The Screen time page only links there.

The web app has no client function that writes a night or a session. Each page shows
**Last updated** from the newest record's `created_at`, and an empty state ("… will appear here
once a data source is connected") when nothing has arrived yet.

## Ingestion contract

These two endpoints are the contract a future pipeline will call. They stay in the API even
though the UI no longer uses them to write:

| Endpoint | Accepts | Details |
| -------- | ------- | ------- |
| `POST /sleep/sessions` | One night: `started_at`, `ended_at` (UTC), optional non-overlapping `stages` | [sleep source](sleep.md) |
| `POST /screen/sessions` | One app session: an interval (`started_at`, `ended_at`) or a duration (`minutes`, `occurred_on`) | [screen time source](screen-time.md) |

Rules shared by both:

- Timestamps are UTC; Atlas derives the local `occurred_on` date in `ATLAS_TZ`.
- `source` records where a row came from (`cli`, `api`, `import`).
- **De-duplication is future work.** There is no external id yet, so sending the same night or
  session twice stores it twice. A pipeline should add an external id (and Atlas a unique
  constraint on it) before it runs unattended. No schema change is made for this now.

Field-level rules and validation are in the feature docs:
[sleep](../domain/sleep.md) and [screen time](../domain/screen-time.md).
