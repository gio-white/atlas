from tests.cli.conftest import invoke


def test_task_add_and_done(runner):
    created = invoke(
        runner,
        ["task", "add", "Family time", "--bucket", "today", "--priority", "high"],
    )
    assert "created task #" in created.output
    assert "Family time" in created.output
    task_id = created.output.split("#", 1)[1].split()[0]
    done = invoke(runner, ["task", "done", task_id])
    assert "done task #" in done.output
