# 0005 — Docs change with code

Status: accepted (2026-11-08, restructure plan decision 5).

## Context

Docs written "later" go stale, and a reviewer cannot tell whether a stale doc or the code is
wrong. Several branches now work in parallel, so docs must also be split so they do not
collide.

## Decision

Docs live in a knowledge base under `docs/`, with one file per feature and a code → doc map.
A commit that changes `src/` or `web/src/` must also change `docs/`, unless its message says
`Docs-Reviewed: no change needed`. This is a hard block for everyone: a Claude Code hook in
every session, and a git hook each clone enables once with
`git config core.hooksPath .githooks`.

## Consequences

- Code and docs disagreeing is treated as a bug.
- Drift tests check API routes and SPA routes against the docs.
- Changelog entries are per-branch fragments, so docs edits do not conflict.

See [docs-sync](../development/docs-sync.md).
