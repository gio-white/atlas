from atlas.cli.app import app
from tests.cli.conftest import invoke, seed_health


def test_amend_and_delete_entry(runner):
    seed_health(runner)
    logged = invoke(runner, ["log", "pushups", "10", "--on", "2026-08-13"])
    entry_id = _entry_id(logged.output)

    amended = invoke(
        runner,
        ["entry", "amend", str(entry_id), "--value", "40", "--note", "fixed"],
    )
    assert "40" in amended.output
    assert str(entry_id) in amended.output

    deleted = invoke(runner, ["entry", "rm", str(entry_id)])
    assert str(entry_id) in deleted.output

    missing = runner.invoke(app, ["entry", "rm", str(entry_id)])
    assert missing.exit_code == 1
    assert "entry" in (missing.output + (missing.stderr or ""))


def _entry_id(output: str) -> int:
    start = output.index("#") + 1
    digits = []
    for char in output[start:]:
        if char.isdigit():
            digits.append(char)
        else:
            break
    return int("".join(digits))
