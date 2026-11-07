#!/usr/bin/env python3
"""Docs gate: a commit that changes code must change docs too.

Blocks a commit that stages files under `src/` or `web/src/` but nothing under `docs/`,
unless the commit message has the line `Docs-Reviewed: no change needed`.
See docs/development/docs-sync.md.

One script, three entry points:

- no arguments: Claude Code PreToolUse hook. Reads the Bash tool call as JSON on stdin and
  prints a `deny` decision when the command runs `git commit` and the gate fails.
- `commit-msg <file>`: git commit-msg hook (`.githooks/commit-msg`). Exits 1 to block.
- `pre-commit`: git pre-commit hook (`.githooks/pre-commit`). Advisory only: git does not show
  the message to pre-commit, so it lists the docs to review and always exits 0.

Stdlib only, so it runs without the project environment.
"""

import fnmatch
import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

CODE_PREFIXES = ("src/", "web/src/")
DOCS_PREFIX = "docs/"
TRAILER = "Docs-Reviewed: no change needed"
TRAILER_LINE = re.compile(r"^\s*" + re.escape(TRAILER) + r"\s*$", re.MULTILINE)
MAP_ROW = re.compile(r"^\|\s*`([^`]+)`\s*\|(.+)\|\s*$")
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
OPERATORS = {";", "&&", "||", "|", "&", "(", ")", "\n"}


def is_code(path: str) -> bool:
    return path.startswith(CODE_PREFIXES)


def is_docs(path: str) -> bool:
    return path.startswith(DOCS_PREFIX)


def has_trailer(message: str) -> bool:
    return TRAILER_LINE.search(message) is not None


def decide(staged: list[str], message: str | None) -> str | None:
    """Why the commit is blocked, or None when it may go ahead.

    `message` is None when it is not known yet (pre-commit): then only the trailer cannot
    rescue a code-only commit, and the caller decides whether that blocks.
    """
    code = sorted(path for path in staged if is_code(path))
    if not code or any(is_docs(path) for path in staged):
        return None
    if message is not None and has_trailer(message):
        return None
    shown = ", ".join(code[:5]) + (f" (+{len(code) - 5} more)" if len(code) > 5 else "")
    return f"staged code without docs: {shown}"


def load_doc_map(root: Path) -> list[tuple[str, str]]:
    """(glob, docs) rows of the code → doc map table in docs/README.md."""
    readme = root / "docs" / "README.md"
    try:
        text = readme.read_text(encoding="utf-8")
    except OSError:
        return []
    section = text.split("## Code → doc map", 1)
    if len(section) < 2:
        return []
    rows: list[tuple[str, str]] = []
    for line in section[1].splitlines():
        if line.startswith("## "):
            break
        match = MAP_ROW.match(line)
        if match:
            rows.append((match.group(1), match.group(2).strip()))
    return rows


def docs_for(paths: list[str], doc_map: list[tuple[str, str]]) -> list[str]:
    found: list[str] = []
    for path in paths:
        for pattern, docs in doc_map:
            if fnmatch.fnmatch(path, pattern):
                if docs not in found:
                    found.append(docs)
                break
    return found


def explain(reason: str, staged: list[str], root: Path) -> str:
    code = [path for path in staged if is_code(path)]
    docs = docs_for(code, load_doc_map(root))
    lines = [
        f"Blocked by the docs gate (docs/development/docs-sync.md): {reason}.",
        "Review the mapped docs against the change, update them, and stage them "
        "(the docs-sync skill does this).",
    ]
    if docs:
        lines.append("Docs to review: " + "; ".join(docs) + ".")
    lines.append(f"If the docs need no change, add the line '{TRAILER}' to the commit message.")
    return " ".join(lines)


def git(root: Path, *args: str) -> list[str]:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line]


def repo_root(cwd: Path) -> Path | None:
    lines = git(cwd, "rev-parse", "--show-toplevel")
    return Path(lines[0]) if lines else None


def staged_files(root: Path) -> list[str]:
    return git(root, "diff", "--cached", "--name-only", "--diff-filter=ACMRD")


# --------------------------------------------------------------- Claude Code hook


def strip_heredocs(command: str) -> tuple[str, list[str]]:
    """The command without heredoc bodies, and the bodies themselves."""
    kept: list[str] = []
    bodies: list[str] = []
    terminators: list[str] = []
    for line in command.split("\n"):
        if terminators:
            if line.strip() == terminators[0]:
                terminators.pop(0)
            else:
                bodies.append(line)
            continue
        kept.append(line)
        terminators.extend(match.group(2) for match in HEREDOC.finditer(line))
    return "\n".join(kept), bodies


def tokenize(command: str) -> list[str]:
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:
        return command.split()


def simple_commands(tokens: list[str]) -> list[list[str]]:
    segments: list[list[str]] = [[]]
    for token in tokens:
        if token in OPERATORS or set(token) <= set(";&|()\n"):
            segments.append([])
        else:
            segments[-1].append(token)
    return [segment for segment in segments if segment]


def git_subcommand(words: list[str]) -> tuple[str, list[str]] | None:
    """('commit', args) for `git [-C dir] [-c k=v] commit args`, else None."""
    while words and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*=.*", words[0]):
        words = words[1:]
    if not words or os.path.basename(words[0]) != "git":
        return None
    index = 1
    while index < len(words) and words[index].startswith("-"):
        index += 2 if words[index] in {"-C", "-c"} else 1
    if index >= len(words):
        return None
    return words[index], words[index + 1 :]


def commit_message(args: list[str], bodies: list[str], cwd: Path) -> str:
    parts: list[str] = list(bodies)
    index = 0
    while index < len(args):
        arg = args[index]
        takes_message = arg == "--message" or re.fullmatch(r"-[a-zA-Z]*m", arg)
        takes_file = arg == "--file" or re.fullmatch(r"-[a-zA-Z]*F", arg)
        if (takes_message or takes_file) and index + 1 < len(args):
            value = args[index + 1]
            if takes_file:
                try:
                    value = (cwd / value).read_text(encoding="utf-8")
                except OSError:
                    value = ""
            parts.append(value)
            index += 2
            continue
        if arg.startswith("--message="):
            parts.append(arg[len("--message=") :])
        elif re.fullmatch(r"-[a-zA-Z]*m.+", arg):
            parts.append(arg.split("m", 1)[1])
        index += 1
    return "\n".join(parts)


def changed_files(root: Path) -> list[str]:
    tracked = git(root, "diff", "--name-only", "HEAD")
    untracked = git(root, "ls-files", "--others", "--exclude-standard")
    return sorted(set(tracked) | set(untracked))


def pending_adds(add_args: list[str], root: Path, cwd: Path) -> list[str]:
    """Files a `git add` earlier in the same command will stage (best effort)."""
    paths = [arg for arg in add_args if not arg.startswith("-")]
    every = {"-A", "--all", "-u", "--update"} & set(add_args)
    changed = changed_files(root)
    if every or "." in paths and cwd == root:
        return changed
    picked: list[str] = []
    for spec in paths:
        rel = os.path.relpath(cwd / spec, root).replace(os.sep, "/")
        rel = "" if rel == "." else rel
        for path in changed:
            if not rel or path == rel or path.startswith(rel.rstrip("/") + "/"):
                picked.append(path)
    return picked


def check_command(command: str, cwd: Path) -> str | None:
    """Deny reason for a Bash command, or None to let it through."""
    if "commit" not in command:
        return None
    root = repo_root(cwd)
    if root is None:
        return None
    stripped, bodies = strip_heredocs(command)
    pending: list[str] = []
    for words in simple_commands(tokenize(stripped)):
        found = git_subcommand(words)
        if found is None:
            continue
        name, args = found
        if name == "add":
            pending.extend(pending_adds(args, root, cwd))
        elif name == "commit":
            staged = staged_files(root) + pending
            if any(a == "--all" or re.fullmatch(r"-[b-zA-Z]*a[a-zA-Z]*", a) for a in args):
                staged += git(root, "diff", "--name-only", "HEAD")
            message = commit_message(args, bodies, cwd)
            reason = decide(sorted(set(staged)), message)
            if reason:
                return explain(reason, staged, root)
    return None


def claude_hook() -> int:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    command = (payload.get("tool_input") or {}).get("command")
    if not isinstance(command, str):
        return 0
    cwd = Path(payload.get("cwd") or os.getcwd())
    reason = check_command(command, cwd)
    if reason is None:
        return 0
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )
    return 0


# ----------------------------------------------------------------------- git hooks


def strip_comments(message: str) -> str:
    return "\n".join(line for line in message.splitlines() if not line.startswith("#"))


def commit_msg_hook(message_file: str) -> int:
    root = repo_root(Path.cwd()) or Path.cwd()
    message = strip_comments(Path(message_file).read_text(encoding="utf-8"))
    staged = staged_files(root)
    reason = decide(staged, message)
    if reason is None:
        return 0
    print(explain(reason, staged, root), file=sys.stderr)
    return 1


def pre_commit_hook() -> int:
    root = repo_root(Path.cwd()) or Path.cwd()
    staged = staged_files(root)
    if decide(staged, None) is None:
        return 0
    docs = docs_for([path for path in staged if is_code(path)], load_doc_map(root))
    note = f" Docs to review: {'; '.join(docs)}." if docs else ""
    print(
        "docs gate: code is staged without docs; the commit will be blocked unless docs are "
        f"staged or the message has '{TRAILER}'.{note}",
        file=sys.stderr,
    )
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        return claude_hook()
    if argv[0] == "commit-msg" and len(argv) == 2:
        return commit_msg_hook(argv[1])
    if argv[0] == "pre-commit":
        return pre_commit_hook()
    print("usage: docs_gate.py [commit-msg <file> | pre-commit]", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
