# Architecture

Layers (imports only flow downward):

```
cli, api  →  services  →  db, domain
db        →  domain
domain    →  (stdlib / typing only)
```

## Import bans

- `atlas/domain/` must not import `atlas.db`, `atlas.api`, `atlas.cli`, or `atlas.services`.
- `atlas/api/` and `atlas/cli/` must not open a session, query tables, or import `atlas.db` except to obtain a session factory they pass into services. They never call SQLModel/SQLAlchemy APIs themselves.
- Routers and Typer commands call `atlas.services` only. Shared behavior lives in services so API and CLI cannot diverge.
- The React SPA in `web/` is the only frontend. It consumes the HTTP API only and must not import `atlas.*` or reimplement streaks, Habits kept, or quest progress. The CLI is admin only (`init`, `seed`, `serve`, `export`, `import`) — capture, definition, and review belong in the SPA.
- Ruff enforces the domain import ban. A check finding is work in this cycle (`.claude/rules/checks.md`), not a note for later.

```python
# ❌ BAD — router talks to the session
def create_metric(session: Session, body: MetricCreate):
    session.add(Metric(**body.model_dump()))

# ✅ GOOD — router calls a service
def create_metric(session: Session, body: MetricCreate):
    return metric_service.create_metric(session, **body.model_dump())
```

## Data principles

- **Facts are stored; everything derived is computed on read.** Entries, screen sessions, sleep, sessions (time blocks), quest items, and a habit's rule versions, marks, and freezes are the stored facts. Streaks, Habits kept, quest progress, and pace are computed on read. Never persist derived columns.
- **Screen time is a dedicated fact store.** Sessions live in `screen_session` (optional start/end interval plus duration). Capture dual-writes minutes onto the app's backing entry, so the minutes show in All entries and exports. The screen dashboard and screen-time habits read sessions, not entries.
- **Habits do not read metrics.** A habit is ticked by you (`PUT` / `DELETE /habits/{slug}/days/{day}`) or judged from your data (sleep, screen sessions, planned sessions). Metric values go through `POST /entries`, screen sessions through `POST /screen/sessions`.
- **Slugs are the human key.** Integer PKs internally; unique slugs (`pushups`, `reading`) on the wire.
- **Local dates for occurrence, UTC for bookkeeping.** `Entry.occurred_on` and `ScreenSession.occurred_on` are local dates in `ATLAS_TZ`. Interval timestamps and `created_at` are UTC.
