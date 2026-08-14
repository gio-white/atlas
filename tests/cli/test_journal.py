from tests.cli.conftest import invoke


def test_journal_logs_text(runner):
    result = invoke(runner, ["journal", "shipped the dashboard", "--on", "2026-08-14"])
    assert "journal" in result.output
    assert "shipped the dashboard" in result.output
    assert "2026-08-14" in result.output
