---
name: docs-sync
description: Bring docs/ in line with the staged code change before committing. Maps each staged file under src/ or web/src/ to its docs through the code → doc map in docs/README.md, re-checks each doc against the code, updates and stages it, and adds the branch changelog fragment. Use before every commit that touches code, when the docs gate blocks a commit, or when the user mentions docs drift, docs-sync, or "Docs-Reviewed".
---

# Docs sync

Code and docs change in the same commit (`.claude/rules/documentation.md`,
`docs/development/docs-sync.md`). This skill does that for the staged diff.

## Steps

1. **List the staged code.**

   ```bash
   git diff --cached --name-only -- src web/src
   ```

   If nothing is listed, there is nothing to sync.

2. **Map files to docs.** Read the `## Code → doc map` table in `docs/README.md`. For each
   staged file, the first row whose glob matches gives its docs. A blocked commit's message
   already names them.

3. **Re-check each doc against the code, not against the diff alone.** Read the staged diff
   (`git diff --cached -- <file>`) and the current code, then each mapped doc. For a
   `docs/domain/*.md` file, walk every heading: Purpose, Concepts, Data model (fields, types,
   enums), Rules and calculations (exact definitions, not summaries), API (every endpoint row
   and service row), Screens, Tests (list new test files), Status. Fix anything stale or
   missing. Also check:
   - new or removed routes → the API tables (`tests/test_docs_drift.py` checks this) and
     `docs/product/navigation.md` for SPA routes (`web/src/docs-drift.test.ts`);
   - schema changes → `docs/architecture/migrations.md` and `docs/architecture/data-model.md`;
   - user-facing text → `docs/product/ux-writing.md` (no slugs, enum values, or jargon on screen);
   - a new code file with no matching row → add a row to the code → doc map.

4. **Add the changelog fragment.** Append one bullet to
   `docs/changelog/unreleased/<branch>.md` (slashes become `-`), in the year file's format:
   `- **YYYY-MM-DD —** \`todo-id\` — what landed.`

5. **Stage the docs** with the code: `git add docs/...`.

6. **Only if the docs genuinely need no change** (pure refactor, test helper, formatting), say
   which docs you re-read and add this line to the commit message:

   ```text
   Docs-Reviewed: no change needed
   ```

   Do not use the trailer to skip a doc that is out of date.

7. Run the gates (`uv run pytest` includes the API drift test; `pnpm test` in `web/` includes
   the navigation drift test) and commit.
