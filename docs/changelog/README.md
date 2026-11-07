# Changelog

What landed, one entry per cycle. The year files are append-only, newest last:

- [2026](2026.md)

## Fragments: one file per branch

Several branches run at once, so nobody edits the year file on a branch. Instead:

1. On your branch, write `docs/changelog/unreleased/<branch-name>.md` (slashes in the branch
   name become `-`, e.g. `feature-docs-knowledge-base.md`).
2. Use the year file's format, one bullet per cycle:

   ```markdown
   - **2026-11-08 —** `todo-id` — What landed, in a few sentences.
   ```

3. When the branch merges, the merging session appends the fragment's bullets to the end of the
   current year file (`2026.md`) unchanged and deletes the fragment, in the merge commit or the
   first commit after it.

Fragments never conflict because each branch owns its own file.
