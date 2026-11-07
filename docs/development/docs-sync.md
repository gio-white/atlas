# Docs sync: docs change with code

Docs and code change in the same commit. This page explains the rule, how to follow it, and
the gate that enforces it. The reasoning is [decision 0005](../decisions/0005-docs-change-with-code.md).

## The rule

A commit that stages files under `src/` or `web/src/` must also stage at least one file under
`docs/`. When you reviewed the docs and they genuinely need no change (a refactor, a test-only
helper, a typo in code), add this line to the commit message on its own line:

```text
Docs-Reviewed: no change needed
```

## How to follow it

1. Look up each changed file in the **code → doc map** in [docs/README.md](../README.md#code--doc-map).
2. Re-read each mapped doc against the code as it now is (data model, rules, API table, screens,
   status). Fix anything stale. Code and docs disagreeing is a bug.
3. Add or edit your branch's changelog fragment in `docs/changelog/unreleased/<branch>.md`
   ([how fragments work](../changelog/README.md)).
4. Stage the doc changes with the code and commit.

In Claude Code, the `docs-sync` skill (`.claude/skills/docs-sync/SKILL.md`) does these steps
for the staged diff.

## The gate

One script, `.claude/hooks/docs_gate.py`, holds the check. It runs in two places:

| Where | When | How it gets the message |
| ----- | ---- | ----------------------- |
| Claude Code `PreToolUse` hook (`.claude/settings.json`) | Before any Bash call that runs `git commit` in a Claude session | From the command (`-m`, heredoc, `-F file`) |
| Git `commit-msg` hook (`.githooks/commit-msg`) | Every commit in a clone that enabled `.githooks` | The message file git passes |

`.githooks/pre-commit` runs the same script in advisory mode: it lists the docs mapped to your
staged code before you write the message, but never blocks (git does not show the message to a
pre-commit hook, so the trailer can only be checked at `commit-msg`).

When a commit is blocked, the message names the mapped docs to review.

### Enable the git hooks once per clone

```bash
git config core.hooksPath .githooks
```

The Claude hook needs nothing: it is configured in `.claude/settings.json` and applies to every
Claude Code session in this repository.

### Tests

`tests/test_docs_gate.py` pins the behaviour: a code-only commit is blocked, a commit with docs
is allowed, and the trailer allows a code-only commit — for the pure decision function, the
Claude hook payload, and the real git hooks in a temporary repository.

## Drift checks

Besides the gate, two tests catch docs that drifted from code (they run with the normal test
suites; see [testing](testing.md#drift-checks)):

- every FastAPI route is in an API table, and every documented route exists;
- every route in `web/src/App.tsx` is in [navigation](../product/navigation.md).
