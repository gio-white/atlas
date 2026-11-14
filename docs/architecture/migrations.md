# Migrations, export, and import

Schema versions, what each one changed, and how export / import stays compatible across them.
Code: `src/atlas/db/engine.py`, `src/atlas/services/port.py`.

## Schema management

Tables are created with `SQLModel.metadata.create_all`. A single-row `schema_version` table records the version (`CURRENT_SCHEMA_VERSION = 14`). `atlas init` creates the parent directory if needed, opens the SQLite file at `ATLAS_DB`, runs `create_all`, and inserts that row when missing. If the row exists with a lower version, `init_schema` runs an explicit migrate then bumps the version (schema 11 drops old tables *before* `create_all`, so the new quest tables are created fresh under the same names). It is safe to run twice. There is no Alembic in the MVP; a schema change ships as an explicit migration step documented in the development log. Schema 2 adds `screen_category`, `screen_app`, and `screen_budget`. Schema 3 adds the old `task`. Schema 4 added goal horizons and parents (the old goal tables are gone since schema 11, so its migration step was removed). Schema 5 adds `screen_device` and `screen_session`, then backfills duration-only sessions from existing entries on screen-app metrics. Schema 6 made the old `Goal.area_id` nullable (step removed with schema 11). Schema 7 adds `entertainment_topic`, `entertainment_title`, and `entertainment_title_topic` (named `library_*` since schema 13) (`create_all` on existing files). Schema 8 adds `sleep_session` and `sleep_session_stage` (`create_all` on existing files). Schema 9 adds `rating` and `link` to the title table (ALTER on existing files). Schema 10 adds `Habit.kind` (backfilled from the metric's value type: bool → check, duration → duration, else count), `Habit.time_of_day`, `Habit.archived_at`, and the `habit_break` table (it also added `Habit.goal_id`, which schema 11 removes). Schema 11 replaces goals and tasks with quests ([decision 0006](../decisions/0006-quest-model-replaces-goals-and-tasks.md)), with no data migration:

1. Before `create_all`, drop the old `task`, `milestone`, and `goal` tables. Each is recognised by a column only its old shape has (`task.bucket`, `milestone.name`, `goal.slug`), so a rerun never drops a new quest table.
2. `create_all` creates `ambition`, `goal`, `milestone`, `side_quest`, `chapter`, `task`, and `time_block` with their RESTRICT foreign keys, indexes, and CHECK constraints ([quests](../domain/quests.md#data-model), [time blocks](../domain/time-blocks.md#data-model)).
3. Rebuild `habit` without `goal_id` (an FK column SQLite cannot drop in place): create `habit__new` from the model's DDL, copy the kept columns, drop `habit`, rename, and recreate its unique slug index. `habit_break` rows keep pointing at the same ids.

Drops and the rebuild run in one transaction with `PRAGMA foreign_keys=OFF` switched on an autocommit connection before `BEGIN` and back on after (`_without_foreign_keys`), the recipe the schema 6 rebuild used. Running `init_schema` twice is a no-op.

Schema 12 removes areas ([decision 0008](../decisions/0008-areas-removed-metrics-carry-an-origin.md)) and gives each metric an `origin` (`_replace_areas_with_metric_origin`):

1. Rebuild `metric` without `area_id` and with `origin` (the same `metric__new` recipe as the `habit` rebuild, in one transaction with foreign keys off). Ids, slugs, and every other column are copied unchanged, so entries, habits, and screen apps keep pointing at the same metrics.
2. Each metric's origin comes from what its area used to say: a metric that backs a screen app, or sat in the internal `screen` area, becomes `screen`; the metric with slug `journal` becomes `journal`; one in the internal `habits` area becomes `habit`; every other metric is `manual`.
3. A metric in an archived area was treated as archived, so it takes that area's `archived_at` when it has none of its own.
4. Drop the `area` table.

The step only runs when `metric.area_id` still exists, so a rerun does nothing. Back up first with `atlas export`; the export from before the change still imports afterwards.

Schema 13 renames Entertainment to Library ([redesign brief](../plans/redesign-brief.md) phase 5; `_rename_entertainment_to_library`), before `create_all` so it never creates empty `library_*` tables beside the old ones. In one transaction with foreign keys off, `ALTER TABLE … RENAME TO` turns `entertainment_topic`, `entertainment_title`, and `entertainment_title_topic` into `library_topic`, `library_title`, and `library_title_topic`; SQLite rewrites the foreign keys that point at them. Each `ix_entertainment_*` index is dropped and recreated as `ix_library_*`. Rows, ids, and every column are kept. A table is only renamed while the old name exists and the new one does not, so a rerun does nothing. Back up first with `atlas export`.

Schema 14 adds `habit_support`, the optional link from a habit to quest items at any level ([habits](../domain/habits.md#habitsupport)). It is a new table, so `create_all` makes it on existing files and nothing else changes.

Import accepts schema versions `1` through `14`; payloads before version 14 have no `habit_supports` and import no habit links; payloads before version 13 carry the library as `entertainment_topics` and `entertainment_titles`, which import as the library; habits without `kind` take it from their metric, without `breaks` have none; missing `rating` and `link` import as null; payloads without `sleep_sessions` import no sleep; older payloads have empty screen, device, session, and/or library collections. Payloads before version 11 never import quests: their `goals`, `milestones`, and `tasks` sections (and a habit's `goal`) are ignored, and the import summary names the skipped sections. Payloads before version 12 carry an `areas` section and an `area` on each metric instead of an `origin`: the areas are not imported (the summary says so), each metric gets its origin by the same rule as the schema 12 migration, and a metric of an archived area is imported archived. Schema 5 payloads that include `screen_sessions` skip importing backing entries for screen-app metrics (sessions dual-write those entries). Payloads without that key backfill sessions from screen-app entries.

## Export and import

| Function | Role |
| -------- | ---- |
| `export_all` / `import_all` | Port. Export is a JSON-serializable dict keyed by slugs where entities have them. Import upserts metrics (with their `origin`), habits, screen categories, screen apps, screen budgets, screen devices, library topics, and library titles by slug, inserts entries, habit links (`habit_supports`, after the quests, their `id` remapped like every quest reference; an existing link is skipped), screen sessions, and sleep sessions (with their nested `stages`). Habits import with their nested `breaks`. `replace=True` deletes user rows first (habit links, time blocks, tasks, chapters, milestones, goals, side quests, ambitions; sleep stages before sleep sessions, library tag links before titles before topics; sessions before entries). `schema_version` must be `1` through `CURRENT_SCHEMA_VERSION` (14). A screen app's metric is always imported as `screen`, whatever the file says. Returns an `ImportSummary` (`schema_version`, `ignored_sections`, `notes`); `POST /import` returns it as JSON and `atlas import` prints the notes. |
| `export_quests` / `import_quests` / `clear_quests` | Quest sections (`src/atlas/services/quest_port.py`). Quest rows have no slug, so the export carries each row's `id` and its parent ids as references local to the file. Import (version 11 and later) inserts fresh rows in parent-before-child order and remaps every reference, so a merge import never collides with existing quests; a reference to an id missing from the file is a 400. The database CHECK constraints still apply. `import_quests` returns each section's file id → new id map, which the habit links use: a `habit_supports` row names its habit by slug and its item by `kind` plus that item's file `id` in the matching section (`goal` → `goals`, and so on). |

Export shape:

```json
{
  "schema_version": 14,
  "metrics": [{"slug": "pushups", "origin": "manual", "name": "Pushups", "value_type": "count", "unit": "reps", "aggregation": "sum", "direction": "higher_is_better", "archived_at": null}],
  "habits": [{"slug": "pushups-daily", "metric": "pushups", "name": "Pushups Daily", "period": "day", "target_value": 1.0, "comparator": "at_least", "weekdays": null, "active_from": "2026-08-01", "active_to": null}],
  "screen_categories": [{"slug": "entertainment", "name": "Entertainment", "judgment": "waste", "archived_at": null}],
  "screen_apps": [{"slug": "instagram", "name": "Instagram", "category": "entertainment", "metric": "instagram", "archived_at": null}],
  "screen_budgets": [{"slug": "waste-cap", "name": "Waste cap", "target_kind": "judgment", "target_slug": "waste", "period": "day", "target_value": 90.0, "comparator": "at_most", "active_from": "2026-08-01", "active_to": null}],
  "screen_devices": [{"slug": "iphone", "name": "iPhone", "archived_at": null}],
  "screen_sessions": [{"app": "instagram", "device": "iphone", "started_at": "2026-08-14T18:00:00+00:00", "ended_at": "2026-08-14T18:30:00+00:00", "minutes": 30.0, "occurred_on": "2026-08-14", "note": null, "source": "cli", "created_at": "2026-08-14T18:30:00+00:00"}],
  "library_topics": [{"slug": "physics", "name": "Physics", "archived_at": null}],
  "library_titles": [{"slug": "interstellar", "name": "Interstellar", "kind": "film", "creator": "Christopher Nolan", "recommended_by": "Alex", "status": "done", "started_on": "2026-08-11", "finished_on": "2026-08-12", "progress": null, "note": null, "rating": 5, "link": null, "topics": ["physics"], "image_url": null, "image_media_type": null, "image_base64": null, "archived_at": null, "created_at": "2026-08-12T12:00:00+00:00"}],
  "ambitions": [{"id": 1, "title": "Become a better engineer", "description": null, "position": 0, "status": "active", "completed_at": null, "archived_at": null, "created_at": "2026-11-01T09:00:00+00:00", "updated_at": "2026-11-01T09:00:00+00:00", "target_on": null, "weight": null}],
  "goals": [{"id": 1, "ambition_id": 1, "title": "Move to Copenhagen", "success_description": "Living and working there", "due_on": "2027-06-30", "weight": 2.0, "position": 0, "status": "active", "...": "container fields as above"}],
  "milestones": [{"id": 1, "goal_id": 1, "title": "Secure a job", "due_on": null, "weight": null, "...": "container fields"}],
  "side_quests": [{"id": 1, "title": "Tax declaration", "due_on": "2026-12-15", "...": "container fields"}],
  "chapters": [{"id": 1, "milestone_id": 1, "side_quest_id": null, "title": "Rust fundamentals", "description": null, "weight": null, "position": 0, "archived_at": null, "created_at": "...", "updated_at": "..."}],
  "tasks": [{"id": 1, "title": "Understand ownership", "description": null, "status": "in_progress", "priority": "high", "estimate_minutes": 120, "due_on": null, "weight": null, "position": 0, "ambition_id": null, "goal_id": null, "milestone_id": null, "chapter_id": 1, "side_quest_id": null, "organized_at": "...", "started_at": "...", "completed_at": null, "archived_at": null, "created_at": "...", "updated_at": "..."}],
  "time_blocks": [{"id": 1, "task_id": 1, "start_at": "2026-11-08T08:00:00+00:00", "end_at": "2026-11-08T09:30:00+00:00", "status": "completed", "provider": "internal", "external_event_id": null, "created_at": "...", "updated_at": "..."}],
  "habit_supports": [{"habit": "runs-weekly", "kind": "goal", "id": 1, "created_at": "2026-11-14T09:00:00+00:00"}],
  "entries": [{"metric": "pushups", "occurred_on": "2026-08-10", "occurred_at": null, "value_num": 40.0, "value_bool": null, "value_text": null, "note": "post-travel", "source": "cli", "created_at": "2026-08-10T12:00:00+00:00"}]
}
```
