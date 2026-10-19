import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "enforce_toolchain.py"


def decision(command: str) -> str | None:
    payload = json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})
    result = subprocess.run(
        [sys.executable, str(HOOK)], input=payload, capture_output=True, text=True, check=True
    )
    if not result.stdout:
        return None
    return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"]


@pytest.mark.parametrize(
    "command",
    [
        "pip install requests",
        "python -m pytest",
        "python3 scripts/seed.py",
        ".venv/bin/python -c 'print(1)'",
        "pytest -q",
        "ruff check .",
        "uvicorn atlas.api.app:app",
        "uv pip install requests",
        "uv run pip install requests",
        "uv run --with rich python -m pip install x",
        "cd web && npm install",
        "npx vitest",
        "yarn add lucide-react",
        "FOO=1 pytest",
        "sudo -E pip install x",
        "bash -lc 'cd web && npm run dev'",
        "echo ok\nnpm test",
        "git status; poetry install",
    ],
)
def test_blocks_tools_outside_uv_and_pnpm(command):
    assert decision(command) == "deny"


@pytest.mark.parametrize(
    "command",
    [
        "uv run pytest -q",
        "uv run ruff check && uv run ruff format --check",
        "uv run python -m atlas.api",
        "uv run atlas seed --replace",
        "uv add --dev pytest",
        "uv sync",
        "cd web && pnpm install && pnpm lint && pnpm test && pnpm build",
        "pnpm dlx shadcn add button",
        "node .claude/skills/brand/scripts/validate-asset.cjs logo.png",
        "git commit -m 'never npm, never pip'",
        "git commit -F - <<'EOF'\nStop using npm.\npip is banned too.\nEOF",
        "grep -rn pytest docs/",
        "ls .venv/bin/python",
        "echo 'npm install' > notes.txt",
    ],
)
def test_allows_uv_pnpm_and_mentions(command):
    assert decision(command) is None


def test_ignores_non_bash_payloads():
    payload = json.dumps({"tool_name": "Edit", "tool_input": {"file_path": "README.md"}})
    result = subprocess.run(
        [sys.executable, str(HOOK)], input=payload, capture_output=True, text=True, check=True
    )
    assert result.stdout == ""
