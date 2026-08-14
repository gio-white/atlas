from tests.cli.conftest import invoke


def test_slip_logs_a_count_of_one(runner):
    result = invoke(runner, ["slip", "--on", "2026-08-13", "--note", "late"])
    assert "slip" in result.output
    assert "1" in result.output
    assert "late" in result.output
