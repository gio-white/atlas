# 0003 — The web app is the only frontend

Status: accepted (the CLI became admin only in the 2026 development log; see [changelog](../changelog/2026.md)).

## Context

Atlas once had CLI review and capture commands next to the web UI, so features were built
twice and drifted.

## Decision

The React SPA in `web/` is the only frontend. It is an HTTP client of the API and never
reimplements streaks, adherence, goal progress, or other derived values. The CLI is admin only:
`init`, `seed`, `serve`, `export`, `import`.

## Consequences

- One place to add a feature: a service, an endpoint, and a page.
- `web/` must not import `atlas.*`.

See [frontend](../architecture/frontend.md) and [cli](../architecture/cli.md).
