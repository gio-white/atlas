# Migrations, export, and import

Schema versions, what each one changed, and how export / import stays compatible across them.
Code: `src/atlas/db/engine.py`, `src/atlas/services/port.py`.

## Schema management

Tables are created with `SQLModel.metadata.create_all`. A single-row `schema_version` table records the version (`CURRENT_SCHEMA_VERSION = 10`). `atlas init` creates the parent directory if needed, opens the SQLite file at `ATLAS_DB`, runs `create_all`, and inserts that row when missing. If the row exists with a lower version, `init_schema` runs an explicit migrate then bumps the version. It is safe to run twice. There is no Alembic in the MVP; a schema change ships as an explicit migration step documented in the development log. Schema 2 adds `screen_category`, `screen_app`, and `screen_budget`. Schema 3 adds `task`. Schema 4 adds `Goal.horizon`, `Goal.parent_id`, `Goal.description`, and `Task.goal_id` (ALTER on existing files, then a one-time horizon backfill from the date window). Schema 5 adds `screen_device` and `screen_session`, then backfills duration-only sessions from existing entries on screen-app metrics. Schema 6 makes `Goal.area_id` nullable (table rebuild on existing SQLite files). Schema 7 adds `entertainment_topic`, `entertainment_title`, and `entertainment_title_topic` (`create_all` on existing files). Schema 8 adds `sleep_session` and `sleep_session_stage` (`create_all` on existing files). Schema 9 adds `EntertainmentTitle.rating` and `EntertainmentTitle.link` (ALTER on existing files). Schema 10 adds `Habit.kind` (backfilled from the metric's value type: bool → check, duration → duration, else count), `Habit.time_of_day`, `Habit.goal_id`, `Habit.archived_at`, and the `habit_break` table. Import accepts schema versions `1` through `10`; habits without `kind` take it from their metric, without `breaks` have none; missing `rating` and `link` import as null; payloads without `sleep_sessions` import no sleep; older payloads have empty screen, task, device, session, and/or entertainment collections, and missing `horizon` is inferred from `due_on - start_on`. Missing goal `area` is null. Schema 5 payloads that include `screen_sessions` skip importing backing entries for screen-app metrics (sessions dual-write those entries). Payloads without that key backfill sessions from screen-app entries.

## Export and import

| Function | Role |
| -------- | ---- |
| `export_all` / `import_all` | Port. Export is a JSON-serializable dict keyed by slugs, not integer ids (tasks, entries, and screen sessions use integer ids on import insert). Import upserts areas, metrics, habits, goals, milestones, screen categories, screen apps, screen budgets, screen devices, entertainment topics, and entertainment titles by slug (milestones by goal slug + name), inserts tasks, entries, screen sessions, and sleep sessions (with their nested `stages`). Goal parents are applied in a second pass so payload order does not matter. `replace=True` deletes user rows first (sleep stages before sleep sessions, entertainment links before titles before topics; sessions before entries, tasks before goals). `schema_version` must be `1` through `CURRENT_SCHEMA_VERSION` (10). Habits import after goals (their `goal` link) with their nested `breaks`. Missing `horizon` is inferred from the date window. Missing goal `area` is null. |

Export shape:

```json
{
  "schema_version": 7,
  "areas": [{"slug": "health", "name": "Health", "description": null, "archived_at": null}],
  "metrics": [{"slug": "pushups", "area": "health", "name": "Pushups", "value_type": "count", "unit": "reps", "aggregation": "sum", "direction": "higher_is_better", "archived_at": null}],
  "habits": [{"slug": "pushups-daily", "metric": "pushups", "name": "Pushups Daily", "period": "day", "target_value": 1.0, "comparator": "at_least", "weekdays": null, "active_from": "2026-08-01", "active_to": null}],
  "goals": [{"slug": "bodyweight-75", "area": "health", "name": "Bodyweight 75kg", "kind": "metric_target", "metric": "weight", "target_value": 75.0, "comparator": "at_most", "baseline_value": null, "measure": "latest_value", "start_on": "2026-01-01", "due_on": "2026-12-01", "horizon": "medium", "parent": "durable-health", "description": null, "status": "active", "achieved_at": null}],
  "milestones": [{"goal": "bodyweight-75", "name": "Hit 78kg", "due_on": null, "done_at": null}],
  "screen_categories": [{"slug": "entertainment", "name": "Entertainment", "judgment": "waste", "archived_at": null}],
  "screen_apps": [{"slug": "instagram", "name": "Instagram", "category": "entertainment", "metric": "instagram", "archived_at": null}],
  "screen_budgets": [{"slug": "waste-cap", "name": "Waste cap", "target_kind": "judgment", "target_slug": "waste", "period": "day", "target_value": 90.0, "comparator": "at_most", "active_from": "2026-08-01", "active_to": null}],
  "screen_devices": [{"slug": "iphone", "name": "iPhone", "archived_at": null}],
  "screen_sessions": [{"app": "instagram", "device": "iphone", "started_at": "2026-08-14T18:00:00+00:00", "ended_at": "2026-08-14T18:30:00+00:00", "minutes": 30.0, "occurred_on": "2026-08-14", "note": null, "source": "cli", "created_at": "2026-08-14T18:30:00+00:00"}],
  "entertainment_topics": [{"slug": "physics", "name": "Physics", "archived_at": null}],
  "entertainment_titles": [{"slug": "interstellar", "name": "Interstellar", "kind": "film", "creator": "Christopher Nolan", "recommended_by": "Alex", "status": "done", "started_on": "2026-08-11", "finished_on": "2026-08-12", "progress": null, "note": null, "rating": 5, "link": null, "topics": ["physics"], "image_url": null, "image_media_type": null, "image_base64": null, "archived_at": null, "created_at": "2026-08-12T12:00:00+00:00"}],
  "tasks": [{"title": "Family time", "bucket": "today", "due_on": "2026-08-14", "due_at": null, "priority": "normal", "goal": "workout-this-week", "done_at": null, "created_at": "2026-08-14T12:00:00+00:00"}],
  "entries": [{"metric": "pushups", "occurred_on": "2026-08-10", "occurred_at": null, "value_num": 40.0, "value_bool": null, "value_text": null, "note": "post-travel", "source": "cli", "created_at": "2026-08-10T12:00:00+00:00"}]
}
```
