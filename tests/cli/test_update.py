from tests.cli.conftest import invoke


def test_update_logs_a_checkin(runner):
    result = invoke(runner, ["update", "--on", "2026-08-13", "--note", "here"])
    assert "checkin" in result.output
    assert "yes" in result.output
    assert "2026-08-13" in result.output
    assert "here" in result.output
