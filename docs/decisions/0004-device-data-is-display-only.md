# 0004 — Device data is display-only

Status: accepted (2026-11-08, restructure plan decision 1 and §4).

## Context

Sleep and Screen Time data should come from devices, not from typing. Manual capture forms on
those pages invited fake precision and cluttered History.

## Decision

Sleep and Screen Time pages only show data. `POST /sleep/sessions` and `POST /screen/sessions`
stay as the ingestion contract for a future pipeline. Configuration (categories, judgments,
caps, devices) stays editable, separate from the display.

## Consequences

- Manual capture controls are removed from the UI (Track T3).
- Until a pipeline exists, the demo seed provides synthetic data.
- De-duplication with an external id is future work.

See [data sources](../data-sources/overview.md).
