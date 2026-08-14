from datetime import UTC, date, datetime

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
    create_screen_device,
    delete_entry,
    delete_screen_session,
    export_all,
    get_metric,
    import_all,
    list_areas,
    list_screen_apps,
    list_screen_sessions,
    log_entry,
    log_screen_session,
    screen_dashboard,
    screen_view,
    update_screen_app,
    update_screen_category,
    update_screen_session,
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
        assert restored["screen_devices"] == payload["screen_devices"]
        assert len(restored["screen_sessions"]) == 1
        assert restored["screen_sessions"][0]["app"] == "instagram"
        assert restored["screen_sessions"][0]["minutes"] == 30.0
        assert [app.slug for app in list_screen_apps(other)] == ["coding", "instagram", "youtube"]


def test_log_entry_on_screen_app_dual_writes_a_duration_session(session):
    _taxonomy(session)
    log_entry(session, "instagram", 30.0, occurred_on=date(2026, 8, 14))
    rows = list_screen_sessions(session)
    assert len(rows) == 1
    assert rows[0].minutes == 30.0
    assert rows[0].started_at is None
    assert rows[0].app_id is not None


def test_log_screen_session_interval_derives_minutes_and_entry(session):
    _taxonomy(session)
    create_screen_device(session, "iphone", name="iPhone")
    start = datetime(2026, 8, 14, 20, 0, tzinfo=UTC)
    end = datetime(2026, 8, 14, 20, 45, tzinfo=UTC)
    row = log_screen_session(
        session,
        "instagram",
        started_at=start,
        ended_at=end,
        device_slug="iphone",
    )
    assert row.minutes == 45.0
    assert row.started_at.replace(tzinfo=UTC) == start
    assert row.entry_id is not None
    view = screen_view(session, as_of=date(2026, 8, 14))
    assert view.judgments.total == 45.0


def test_delete_screen_session_removes_paired_entry(session):
    _taxonomy(session)
    row = log_screen_session(session, "instagram", minutes=20.0, occurred_on=date(2026, 8, 14))
    delete_screen_session(session, row.id)
    assert list_screen_sessions(session) == []
    view = screen_view(session, as_of=date(2026, 8, 14))
    assert view.judgments.total is None


def test_delete_entry_removes_paired_session(session):
    _taxonomy(session)
    entry = log_entry(session, "instagram", 15.0, occurred_on=date(2026, 8, 14))
    delete_entry(session, entry.id)
    assert list_screen_sessions(session) == []


def test_update_interval_session_syncs_entry(session):
    _taxonomy(session)
    row = log_screen_session(session, "youtube", minutes=10.0, occurred_on=date(2026, 8, 14))
    start = datetime(2026, 8, 14, 18, 0, tzinfo=UTC)
    end = datetime(2026, 8, 14, 18, 20, tzinfo=UTC)
    updated = update_screen_session(session, row.id, started_at=start, ended_at=end)
    assert updated.minutes == 20.0
    assert updated.started_at.replace(tzinfo=UTC) == start


def test_rejects_only_start_without_end(session):
    _taxonomy(session)
    with pytest.raises(ValidationError, match="both be set"):
        log_screen_session(
            session,
            "instagram",
            started_at=datetime(2026, 8, 14, 12, 0, tzinfo=UTC),
        )


def test_screen_view_clips_interval_across_midnight(session, monkeypatch):
    monkeypatch.setenv("ATLAS_TZ", "UTC")
    _taxonomy(session)
    log_screen_session(
        session,
        "instagram",
        started_at=datetime(2026, 8, 14, 23, 30, tzinfo=UTC),
        ended_at=datetime(2026, 8, 15, 0, 45, tzinfo=UTC),
    )
    today = screen_view(session, as_of=date(2026, 8, 14))
    tomorrow = screen_view(session, as_of=date(2026, 8, 15))
    assert today.judgments.total == 30.0
    assert tomorrow.judgments.total == 45.0
    assert today.sessions[0].minutes == 30.0
    assert today.budgets[0].current_value == 30.0


def test_screen_dashboard_week_totals_and_budget_insight(session, monkeypatch):
    monkeypatch.setenv("ATLAS_TZ", "UTC")
    _taxonomy(session)
    log_screen_session(session, "instagram", minutes=30.0, occurred_on=date(2026, 8, 11))
    log_screen_session(session, "youtube", minutes=40.0, occurred_on=date(2026, 8, 12))
    log_screen_session(session, "coding", minutes=90.0, occurred_on=date(2026, 8, 12))
    log_screen_session(session, "instagram", minutes=20.0, occurred_on=date(2026, 8, 14))
    dash = screen_dashboard(session, as_of=date(2026, 8, 14), period=Period.WEEK)
    assert dash.range_start == date(2026, 8, 10)
    assert dash.range_end == date(2026, 8, 14)
    assert dash.total == 180.0
    assert dash.daily_average == 36.0
    assert dash.longest_day is not None
    assert dash.longest_day.date == date(2026, 8, 12)
    assert dash.score is not None
    assert len(dash.hours) == 7
    assert len(dash.hours[0]) == 24
    assert len(dash.trend) == 8
    assert dash.hours[0] == [0.0] * 24
    assert {app.slug for app in dash.apps} == {"instagram", "youtube", "coding"}
    assert dash.budgets[0].current_value == 20.0
    kinds = {item.kind.value for item in dash.insights}
    assert "budget" not in kinds or dash.budgets[0].satisfied is True
