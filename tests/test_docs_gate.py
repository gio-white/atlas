"""Docs gate: code-only commits are blocked, docs or the trailer let them through."""

import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GATE = ROOT / ".claude" / "hooks" / "docs_gate.py"
TRAILER = "Docs-Reviewed: no change needed"

spec = importlib.util.spec_from_file_location("docs_gate", GATE)
assert spec and spec.loader
docs_gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(docs_gate)


@pytest.mark.parametrize(
    ("staged", "message", "blocked"),
    [
        (["src/atlas/services/habits.py"], "Fix streaks", True),
        (["web/src/pages/HabitsPage.tsx"], "Tweak copy", True),
        (["src/atlas/services/habits.py", "docs/domain/habits.md"], "Fix streaks", False),
        (["src/atlas/services/habits.py"], f"Refactor\n\n{TRAILER}\n", False),
        (["src/atlas/services/habits.py"], f"Refactor {TRAILER} inline", True),
        (["tests/services/test_habits.py"], "Add a test", False),
        (["web/package.json", "README.md"], "Bump", False),
        ([], "Empty", False),
    ],
)
def test_decide(staged, message, blocked):
    assert (docs_gate.decide(staged, message) is not None) is blocked


def test_doc_map_names_docs_for_blocked_code():
    doc_map = docs_gate.load_doc_map(ROOT)
    assert doc_map, "docs/README.md must keep the code → doc map table"
    docs = docs_gate.docs_for(["src/atlas/services/habits.py"], doc_map)
    assert docs == ["`docs/domain/habits.md`"]


def test_every_code_file_maps_to_a_doc():
    doc_map = docs_gate.load_doc_map(ROOT)
    files = [
        str(path.relative_to(ROOT))
        for base in ("src", "web/src")
        for path in (ROOT / base).rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    ]
    unmapped = [path for path in files if not docs_gate.docs_for([path], doc_map)]
    assert not unmapped, f"add rows to the code → doc map in docs/README.md: {unmapped}"


# ------------------------------------------------------------ real repositories


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=check)


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    if shutil.which("git") is None:
        pytest.skip("git is not installed")
    git(tmp_path, "init", "-q", "-b", "main")
    git(tmp_path, "config", "user.email", "test@example.com")
    git(tmp_path, "config", "user.name", "Test")
    git(tmp_path, "config", "commit.gpgsign", "false")
    hooks = tmp_path / ".claude" / "hooks"
    hooks.mkdir(parents=True)
    shutil.copy(GATE, hooks / "docs_gate.py")
    shutil.copytree(ROOT / ".githooks", tmp_path / ".githooks")
    (tmp_path / "docs").mkdir()
    shutil.copy(ROOT / "docs" / "README.md", tmp_path / "docs" / "README.md")
    (tmp_path / "src" / "atlas" / "services").mkdir(parents=True)
    (tmp_path / "src" / "atlas" / "services" / "habits.py").write_text("x = 1\n")
    git(tmp_path, "add", ".")
    git(tmp_path, "commit", "-q", "-m", "init")
    git(tmp_path, "config", "core.hooksPath", ".githooks")
    return tmp_path


def change_code(repo: Path) -> None:
    (repo / "src" / "atlas" / "services" / "habits.py").write_text("x = 2\n")


def change_docs(repo: Path) -> None:
    (repo / "docs" / "README.md").write_text("# changed\n")


def claude_decision(repo: Path, command: str) -> str | None:
    payload = json.dumps(
        {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(repo)}
    )
    result = subprocess.run(
        [sys.executable, str(GATE)], input=payload, capture_output=True, text=True, check=True
    )
    if not result.stdout:
        return None
    return json.loads(result.stdout)["hookSpecificOutput"]["permissionDecision"]


def test_git_hook_blocks_code_only_commit(repo):
    change_code(repo)
    git(repo, "add", "-A")
    result = git(repo, "commit", "-m", "Change code", check=False)
    assert result.returncode != 0
    assert "docs gate" in result.stderr
    assert "docs/domain/habits.md" in result.stderr


def test_git_hook_allows_commit_with_docs(repo):
    change_code(repo)
    change_docs(repo)
    git(repo, "add", "-A")
    assert git(repo, "commit", "-m", "Change code and docs", check=False).returncode == 0


def test_git_hook_allows_trailer(repo):
    change_code(repo)
    git(repo, "add", "-A")
    message = f"Refactor\n\n{TRAILER}"
    assert git(repo, "commit", "-m", message, check=False).returncode == 0


def test_claude_hook_blocks_code_only_commit(repo):
    change_code(repo)
    git(repo, "add", "-A")
    assert claude_decision(repo, "git commit -m 'Change code'") == "deny"


def test_claude_hook_sees_files_added_in_the_same_command(repo):
    change_code(repo)
    assert claude_decision(repo, "git add -A && git commit -m 'Change code'") == "deny"
    assert claude_decision(repo, "git add src && git commit -m 'Change code'") == "deny"
    assert claude_decision(repo, "git commit -am 'Change code'") == "deny"


def test_claude_hook_allows_commit_with_docs(repo):
    change_code(repo)
    change_docs(repo)
    assert claude_decision(repo, "git add -A && git commit -m 'Code and docs'") is None


def test_claude_hook_allows_trailer(repo):
    change_code(repo)
    git(repo, "add", "-A")
    heredoc = f"git commit -F - <<'EOF'\nRefactor\n\n{TRAILER}\nEOF"
    quoted = f"git commit -m 'Refactor' -m '{TRAILER}'"
    assert claude_decision(repo, heredoc) is None
    assert claude_decision(repo, quoted) is None
    assert (
        claude_decision(repo, f"git commit -m \"$(cat <<'EOF'\nRefactor\n\n{TRAILER}\nEOF\n)\"")
        is None
    )


def test_claude_hook_ignores_other_commands(repo):
    change_code(repo)
    git(repo, "add", "-A")
    assert claude_decision(repo, "git status") is None
    assert claude_decision(repo, "echo 'git commit'") is None
