#!/usr/bin/env python3
"""PreToolUse hook: Python goes through `uv`, the web app through `pnpm`.

Reads the Bash tool call as JSON on stdin. If any simple command in it runs a
banned tool, prints a `deny` decision naming the uv / pnpm replacement;
otherwise exits silently and the normal permission flow continues.
"""

import json
import os
import re
import shlex
import sys

PYTHON_TOOLS = {
    "pip": "uv add <pkg> (or uv add --dev <pkg>); uv sync to install the lockfile",
    "pip3": "uv add <pkg> (or uv add --dev <pkg>); uv sync to install the lockfile",
    "pipx": "uv tool run <tool> / uvx <tool>",
    "pytest": "uv run pytest",
    "ruff": "uv run ruff check / uv run ruff format",
    "uvicorn": "uv run uvicorn atlas.api.app:app --reload (or uv run atlas serve)",
    "atlas": "uv run atlas ...",
    "poetry": "uv (uv add / uv sync / uv run)",
    "pipenv": "uv (uv add / uv sync / uv run)",
    "conda": "uv (uv add / uv sync / uv run)",
    "virtualenv": "uv sync (it manages .venv)",
}
JS_TOOLS = {
    "npm": "pnpm (pnpm install / pnpm add <pkg> / pnpm <script>) from web/",
    "npx": "pnpm dlx <pkg> or a package.json script via pnpm",
    "yarn": "pnpm (pnpm install / pnpm add <pkg>) from web/",
    "bun": "pnpm from web/",
    "bunx": "pnpm dlx <pkg>",
}
PYTHON_BINARY = re.compile(r"python(\d+(\.\d+)*)?")
OPERATOR_CHARS = set(";&|()\n")
PREFIXES = {"sudo", "env", "command", "exec", "time", "nohup", "nice", "builtin"}
SHELLS = {"bash", "sh", "zsh", "dash"}
ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=.*")
HEREDOC = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")


def strip_heredocs(command: str) -> str:
    """Drop heredoc bodies: they are data (a commit message, a file), not commands."""
    kept: list[str] = []
    terminators: list[str] = []
    for line in command.split("\n"):
        if terminators:
            if line.strip() == terminators[0]:
                terminators.pop(0)
            continue
        kept.append(line)
        terminators.extend(match.group(2) for match in HEREDOC.finditer(line))
    return "\n".join(kept)


def tokenize(command: str) -> list[str]:
    # Newlines separate commands only outside quotes, so they are punctuation, not whitespace.
    lexer = shlex.shlex(command, posix=True, punctuation_chars=";&|()\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:
        return command.split()


def simple_commands(command: str) -> list[list[str]]:
    segments: list[list[str]] = [[]]
    for token in tokenize(strip_heredocs(command)):
        if set(token) <= OPERATOR_CHARS:
            segments.append([])
        else:
            segments[-1].append(token)
    return [segment for segment in segments if segment]


def strip_prefixes(words: list[str]) -> list[str]:
    index = 0
    while index < len(words):
        word = words[index]
        prefix_flag = (
            word.startswith("-") and index > 0 and os.path.basename(words[index - 1]) in PREFIXES
        )
        if not (ASSIGNMENT.fullmatch(word) or os.path.basename(word) in PREFIXES or prefix_flag):
            break
        index += 1
    return words[index:]


def uv_run_target(words: list[str]) -> list[str]:
    """The command after `uv run [options]`, or [] when that is not what `words` is."""
    if len(words) < 2 or os.path.basename(words[0]) != "uv" or words[1] != "run":
        return []
    rest = words[2:]
    takes_value = {"--with", "--python", "-p", "--package", "--extra", "--group", "--env-file"}
    index = 0
    while index < len(rest) and rest[index].startswith("-"):
        index += 2 if rest[index] in takes_value else 1
    return rest[index:]


def violation(words: list[str]) -> str | None:
    words = strip_prefixes(words)
    if not words:
        return None
    name = os.path.basename(words[0])
    if name in SHELLS:
        for position, flag in enumerate(words[1:], start=1):
            is_command_flag = re.fullmatch(r"-[a-z]*c[a-z]*", flag) is not None
            if is_command_flag and position + 1 < len(words):
                return check(words[position + 1])
    if name == "uv" and len(words) > 1 and words[1] == "pip":
        return "`uv pip` bypasses the lockfile; use uv add <pkg> / uv sync"
    inner = uv_run_target(words)
    if inner:
        inner_name = os.path.basename(inner[0])
        if inner_name in {"pip", "pip3"} or (
            PYTHON_BINARY.fullmatch(inner_name) and inner[1:3] == ["-m", "pip"]
        ):
            return "installing with pip inside uv bypasses the lockfile; use uv add <pkg>"
        return None
    if PYTHON_BINARY.fullmatch(name):
        if words[1:3] in (["-m", "pip"], ["-m", "pytest"], ["-m", "ruff"]):
            return f"`{name} {' '.join(words[1:3])}` must go through uv: uv run {words[2]}"
        return f"bare `{name}` runs outside the project env; use uv run python ..."
    if name in PYTHON_TOOLS:
        return f"`{name}` is not used in this project; use {PYTHON_TOOLS[name]}"
    if name in JS_TOOLS:
        return f"`{name}` is not used in this project; use {JS_TOOLS[name]}"
    return None


def check(command: str) -> str | None:
    for words in simple_commands(command):
        found = violation(words)
        if found:
            return found
    return None


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return
    command = (payload.get("tool_input") or {}).get("command")
    if not isinstance(command, str):
        return
    found = check(command)
    if found is None:
        return
    reason = (
        f"Blocked by the atlas toolchain rule (.claude/rules/tooling.md): {found}. "
        "Python commands go through uv, web commands through pnpm."
    )
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


if __name__ == "__main__":
    main()
