from datetime import date

import pytest

from atlas.db import create_memory_engine, init_schema, make_session_factory
from atlas.domain import Comparator, Direction, Period, ScreenJudgment, ValueType
from atlas.services import (
    AlreadyExistsError,
    NotFoundError,
    ValidationError,
    create_screen_app,
    create_screen_budget,
    create_screen_category,
    export_all,
    get_metric,
    import_all,
    list_areas,
    list_screen_apps,
    log_entry,
    screen_view,
    update_screen_app,
    update_screen_category,
)


def _taxonomy(session):
    create_screen_category(session, "entertainment", judgment=ScreenJudgment.WASTE)
    create_screen_category(session, "learning", judgment=ScreenJudgment.USEFUL)
    create_screen_app(session, "instagram", category_slug="entertainment")
    create_screen_app(session, "youtube", category_slug="entertainment")
    create_screen_app(session, "coding", category_slug="learning")
    create_screen_budget(
        session,
        "waste-cap",
        name="Waste cap",
        target_kind="judgment",
        target_slug="waste",
        period=Period.DAY,
        target_value=90.0,
        comparator=Comparator.AT_MOST,
        active_from=date(2026, 8, 1),
    )


def test_create_category_creates_screen_area(session):
    create_screen_category(session, "entertainment", judgment=ScreenJudgment.WASTE)
    assert [area.slug for area in list_areas(session)] == ["screen"]


def test_create_app_creates_duration_metric_mirroring_judgment(session):
    create_screen_category(session, "entertainment", judgment=ScreenJudgment.WASTE)
    app = create_screen_app(session, "instagram", category_slug="entertainment", name="Instagram")
    metric = get_metric(session, "instagram")
    assert app.metric_id == metric.id
    assert metric.value_type == ValueType.DURATION
    assert metric.aggregation == "sum"
    assert metric.unit == "min"
    assert metric.direction is Direction.LOWER_IS_BETTER
    assert metric.name == "Instagram"


def test_view_rolls_apps_into_category_and_waste_budget(session):
    _taxonomy(session)
    log_entry(session, "instagram", 30.0, occurred_on=date(2026, 8, 14))
    log_entry(session, "youtube", 40.0, occurred_on=date(2026, 8, 14))
    log_entry(session, "coding", 90.0, occurred_on=date(2026, 8, 14))
    view = screen_view(session, as_of=date(2026, 8, 14))
    by_slug = {category.slug: category for category in view.categories}
    assert by_slug["entertainment"].minutes == 70.0
    assert by_slug["learning"].minutes == 90.0
    assert view.judgments.waste == 70.0
    assert view.judgments.useful == 90.0
    assert view.judgments.total == 160.0
    budget = view.budgets[0]
    assert budget.current_value == 70.0
    assert budget.satisfied is True
    assert [session_row.app for session_row in view.sessions] == ["instagram", "youtube", "coding"]


def test_reclassify_entertainment_moves_minutes_out_of_waste(session):
    _taxonomy(session)
    log_entry(session, "instagram", 30.0, occurred_on=date(2026, 8, 14))
    update_screen_category(session, "entertainment", judgment=ScreenJudgment.USEFUL)
    view = screen_view(session, as_of=date(2026, 8, 14))
    assert view.judgments.waste is None
    assert view.judgments.useful == 30.0
    assert get_metric(session, "instagram").direction is Direction.HIGHER_IS_BETTER
    assert view.budgets[0].current_value is None
    assert view.budgets[0].satisfied is True


def test_moving_an_app_changes_its_category_total(session):
    _taxonomy(session)
    log_entry(session, "instagram", 30.0, occurred_on=date(2026, 8, 14))
    update_screen_app(session, "instagram", category_slug="learning")
    view = screen_view(session, as_of=date(2026, 8, 14))
    by_slug = {category.slug: category for category in view.categories}
    assert by_slug["entertainment"].minutes is None
    assert by_slug["learning"].minutes == 30.0
    assert view.judgments.waste is None
    assert view.judgments.useful == 30.0


def test_waste_budget_fails_when_over_cap(session):
    _taxonomy(session)
    log_entry(session, "instagram", 50.0, occurred_on=date(2026, 8, 14))
    log_entry(session, "youtube", 50.0, occurred_on=date(2026, 8, 14))
    view = screen_view(session, as_of=date(2026, 8, 14))
    assert view.budgets[0].current_value == 100.0
    assert view.budgets[0].satisfied is False


def test_duplicate_category_slug_is_rejected(session):
    create_screen_category(session, "entertainment", judgment=ScreenJudgment.WASTE)
    with pytest.raises(AlreadyExistsError):
        create_screen_category(session, "entertainment", judgment=ScreenJudgment.NEUTRAL)


def test_app_requires_an_existing_category(session):
    with pytest.raises(NotFoundError):
        create_screen_app(session, "instagram", category_slug="missing")


def test_judgment_budget_rejects_unknown_target(session):
    with pytest.raises(ValidationError, match="judgment target"):
        create_screen_budget(
            session,
            "bad",
            target_kind="judgment",
            target_slug="entertainment",
            period=Period.DAY,
            target_value=90.0,
            comparator=Comparator.AT_MOST,
        )


def test_export_round_trips_screen_taxonomy(session):
    _taxonomy(session)
    log_entry(session, "instagram", 30.0, occurred_on=date(2026, 8, 14))
    payload = export_all(session)
    assert {row["slug"] for row in payload["screen_categories"]} == {"entertainment", "learning"}
    assert {row["slug"] for row in payload["screen_apps"]} == {"coding", "instagram", "youtube"}
    assert payload["screen_budgets"][0]["target_slug"] == "waste"

    engine = create_memory_engine()
    init_schema(engine)
    with make_session_factory(engine)() as other:
        import_all(other, payload)
        restored = export_all(other)
        assert restored["screen_categories"] == payload["screen_categories"]
        assert restored["screen_apps"] == payload["screen_apps"]
        assert restored["screen_budgets"] == payload["screen_budgets"]
        assert [app.slug for app in list_screen_apps(other)] == ["coding", "instagram", "youtube"]
