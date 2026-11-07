# 0002 — Progress is computed on read

Status: accepted (2026-08).

## Context

Streaks, adherence, goal progress, and pace all depend on recorded facts that can be
backfilled or corrected at any time.

## Decision

Entries (and the dedicated fact stores for screen sessions, sleep, and the entertainment
library) are the stored facts. Every derived value is a pure function of those facts plus
configuration and an explicit `as_of` date. Derived columns are never persisted.

## Consequences

- Backfilling or correcting an entry fixes every dependent number with no recalculation step.
- Calculations live in `src/atlas/domain/` as pure functions and are tested without a database.
- Reads do more work; at single-user scale that is fine.

See [overview](../architecture/overview.md#derived-computations).
