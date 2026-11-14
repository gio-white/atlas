# 0008 — Areas are removed; a metric carries its origin

Status: accepted (2026-11-14, [redesign brief](../plans/redesign-brief.md) D17 and phase 2; the
table drop was confirmed by the owner before the work started).

## Context

Areas grouped metrics by part of life (Health, Career, Finance). They were only reachable through
Catalog, quests never used them, and the redesign removes both the Area pages and Catalog. Three
hidden areas did real work, though: `habits` marked metrics a habit had made for itself (so
deleting the habit could retire them), `screen` marked the per-app metrics that screen sessions
write to (so All entries could hide that automatic data), and `life` held the journal's metric.
Every metric also had to belong to an area. The brief left the choice open: keep an internal-only
grouping, or drop the table.

## Decision

- The `area` table, `metric.area_id`, the `/areas` and `/views/areas` endpoints, and every area
  parameter are removed. Nothing groups metrics.
- A metric carries an `origin` instead: `manual`, `habit`, `screen`, or `journal`. It records how
  the metric came to exist, which is the one thing the hidden areas were really used for. The API
  never accepts it; it follows from how the metric was created.
- Schema 12 converts an existing database in place and keeps every id, entry, and habit. Exports
  from before schema 12 still import: their areas are skipped with a note and their metrics get
  an origin by the same rule ([migrations](../architecture/migrations.md)).

## Consequences

- Settings → Metrics lists `manual` and `habit` metrics; screen app metrics and the journal's
  metric are Atlas's own and are not listed.
- "Hide automatic data" is `include_automatic=false` on `GET /entries`, defined by origin
  (`AUTOMATIC_METRIC_ORIGINS`), so future device sources only add an origin.
- A metric in an archived area used to count as archived; the migration and the import archive
  such metrics so nothing reappears.
- The user's own areas (Health, Career, …) are not kept anywhere. If grouping is wanted again it
  is a new feature, not a revival of this table ([open points](../plans/open-points.md), manual
  metrics).

See [trackers and entries](../domain/trackers-and-entries.md#data-model).
