from atlas.db import init_db, make_session_factory
from atlas.domain import ScreenJudgment
from atlas.services import create_screen_app, create_screen_category
from tests.cli.conftest import invoke


def _taxonomy(db_path):
    engine = init_db(db_path)
    with make_session_factory(engine)() as session:
        create_screen_category(session, "entertainment", judgment=ScreenJudgment.WASTE)
        create_screen_app(session, "instagram", category_slug="entertainment")
        create_screen_app(session, "youtube", category_slug="entertainment")


def test_screen_log_duration(runner, db_path):
    _taxonomy(db_path)
    result = invoke(runner, ["screen", "log", "instagram", "30", "--on", "2026-08-14"])
    assert "instagram" in result.output
    assert "30" in result.output
    assert "2026-08-14" in result.output


def test_screen_log_interval(runner, db_path):
    _taxonomy(db_path)
    result = invoke(
        runner,
        [
            "screen",
            "log",
            "youtube",
            "--from",
            "2026-08-14T20:00:00+00:00",
            "--to",
            "2026-08-14T20:40:00+00:00",
        ],
    )
    assert "youtube" in result.output
    assert "40" in result.output
