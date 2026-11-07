# 0001 — Local-first, single user

Status: accepted (2026-08).

## Context

Atlas tracks one person's life. The data is personal, and the owner runs it on their own
computer.

## Decision

Atlas is single-user and local-first: one SQLite file (`ATLAS_DB`), an API bound to
`127.0.0.1`, no authentication, no remote exposure. Running Atlas anywhere else is out of scope
for now.

## Consequences

- No accounts, permissions, or multi-tenant data model.
- CORS is limited to the local Vite dev origins.
- Backups are `atlas export` / `atlas import`.

See [vision](../product/vision.md) and [configuration](../architecture/configuration.md).
