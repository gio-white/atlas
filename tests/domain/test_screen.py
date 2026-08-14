from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

import pytest

from atlas.domain import (
    Aggregation,
    Comparator,
    Direction,
    EntryView,
    Period,
    ScreenAppSpec,
    ScreenBudgetSpec,
    ScreenBudgetTargetKind,
    ScreenCategorySpec,
    ScreenInsightKind,
    ScreenJudgment,
    ScreenScoreBand,
    ScreenSessionView,
    add_minutes,
    clip_interval_hours,
    current_streak,
    day_minutes,
    direction_for_judgment,
    interval_minutes,
    local_date,
    member_apps,
    previous_like_for_like,
    resolve_screen_session,
    score_band,
    screen_dashboard_math,
    screen_day_totals,
    screen_score,
)


def _app(slug: str, category: str) -> ScreenAppSpec:
    return ScreenAppSpec(slug=slug, category_slug=category, metric_slug=slug)


def _category(slug: str, judgment: ScreenJudgment) -> ScreenCategorySpec:
    return ScreenCategorySpec(slug=slug, judgment=judgment)


def test_direction_mirrors_judgment():
    assert direction_for_judgment(ScreenJudgment.USEFUL) is Direction.HIGHER_IS_BETTER
    assert direction_for_judgment(ScreenJudgment.WASTE) is Direction.LOWER_IS_BETTER
    assert direction_for_judgment(ScreenJudgment.NEUTRAL) is Direction.NEUTRAL


def test_add_minutes_treats_none_as_missing():
    assert add_minutes(None, None) is None
    assert add_minutes(None, 30.0) == 30.0
    assert add_minutes(10.0, None) == 10.0
    assert add_minutes(30.0, 40.0) == 70.0


def test_day_minutes_sums_one_day():
    entries = [
        EntryView(occurred_on=date(2026, 8, 14), value_num=30.0),
        EntryView(occurred_on=date(2026, 8, 13), value_num=10.0),
    ]
    assert day_minutes(entries, date(2026, 8, 14)) == 30.0
    assert day_minutes(entries, date(2026, 8, 15)) is None


def test_instagram_and_youtube_roll_into_entertainment_waste():
    apps = [_app("instagram", "entertainment"), _app("youtube", "entertainment")]
    categories = [
        _category("entertainment", ScreenJudgment.WASTE),
        _category("learning", ScreenJudgment.USEFUL),
    ]
    entries = {
        "instagram": [EntryView(occurred_on=date(2026, 8, 14), value_num=30.0)],
        "youtube": [EntryView(occurred_on=date(2026, 8, 14), value_num=40.0)],
    }
    by_app, by_category, by_judgment = screen_day_totals(
        apps, categories, entries, date(2026, 8, 14)
    )
    assert by_app == {"instagram": 30.0, "youtube": 40.0}
    assert by_category["entertainment"] == 70.0
    assert by_category["learning"] is None
    assert by_judgment[ScreenJudgment.WASTE] == 70.0
    assert by_judgment[ScreenJudgment.USEFUL] is None


def test_reclassifying_entertainment_moves_minutes_out_of_waste():
    apps = [_app("instagram", "entertainment")]
    waste = [_category("entertainment", ScreenJudgment.WASTE)]
    useful = [_category("entertainment", ScreenJudgment.USEFUL)]
    entries = {"instagram": [EntryView(occurred_on=date(2026, 8, 14), value_num=30.0)]}
    _, _, as_waste = screen_day_totals(apps, waste, entries, date(2026, 8, 14))
    _, _, as_useful = screen_day_totals(apps, useful, entries, date(2026, 8, 14))
    assert as_waste[ScreenJudgment.WASTE] == 30.0
    assert as_useful[ScreenJudgment.WASTE] is None
    assert as_useful[ScreenJudgment.USEFUL] == 30.0


def test_member_apps_for_judgment_and_category_budgets():
    apps = [
        _app("instagram", "entertainment"),
        _app("coding", "learning"),
    ]
    categories = [
        _category("entertainment", ScreenJudgment.WASTE),
        _category("learning", ScreenJudgment.USEFUL),
    ]
    waste = ScreenBudgetSpec(
        target_kind=ScreenBudgetTargetKind.JUDGMENT,
        target_slug="waste",
        period=Period.DAY,
        target_value=90.0,
        comparator=Comparator.AT_MOST,
        active_from=date(2026, 8, 1),
    )
    entertainment = ScreenBudgetSpec(
        target_kind=ScreenBudgetTargetKind.CATEGORY,
        target_slug="entertainment",
        period=Period.DAY,
        target_value=45.0,
        comparator=Comparator.AT_MOST,
        active_from=date(2026, 8, 1),
    )
    assert [app.slug for app in member_apps(apps, categories, waste)] == ["instagram"]
    assert [app.slug for app in member_apps(apps, categories, entertainment)] == ["instagram"]


def test_waste_budget_streak_uses_merged_app_entries():
    budget = ScreenBudgetSpec(
        target_kind=ScreenBudgetTargetKind.JUDGMENT,
        target_slug="waste",
        period=Period.DAY,
        target_value=90.0,
        comparator=Comparator.AT_MOST,
        active_from=date(2026, 8, 12),
    )
    merged = [
        EntryView(occurred_on=date(2026, 8, 12), value_num=30.0),
        EntryView(occurred_on=date(2026, 8, 12), value_num=40.0),
        EntryView(occurred_on=date(2026, 8, 13), value_num=20.0),
        EntryView(occurred_on=date(2026, 8, 14), value_num=80.0),
    ]
    habit = budget.as_habit()
    assert habit.aggregation is Aggregation.SUM
    assert current_streak(habit, merged, date(2026, 8, 14)) == 3


def test_interval_session_derives_minutes_and_local_date():
    start = datetime(2026, 8, 14, 21, 30, tzinfo=UTC)
    end = datetime(2026, 8, 14, 22, 0, tzinfo=UTC)
    spec = resolve_screen_session(
        started_at=start,
        ended_at=end,
        minutes=None,
        occurred_on=None,
        timezone=ZoneInfo("Europe/Berlin"),
        today=date(2026, 8, 15),
    )
    assert spec.minutes == 30.0
    assert spec.occurred_on == date(2026, 8, 14)
    assert spec.has_interval() is True


def test_duration_only_uses_minutes_and_today():
    spec = resolve_screen_session(
        started_at=None,
        ended_at=None,
        minutes=45.0,
        occurred_on=None,
        timezone=UTC,
        today=date(2026, 8, 14),
    )
    assert spec.minutes == 45.0
    assert spec.occurred_on == date(2026, 8, 14)
    assert spec.has_interval() is False


def test_interval_rejects_mismatched_minutes():
    start = datetime(2026, 8, 14, 12, 0, tzinfo=UTC)
    end = datetime(2026, 8, 14, 12, 30, tzinfo=UTC)
    with pytest.raises(ValueError, match="must match the interval"):
        resolve_screen_session(
            started_at=start,
            ended_at=end,
            minutes=10.0,
            occurred_on=None,
            timezone=UTC,
            today=date(2026, 8, 14),
        )


def test_rejects_half_interval_and_non_positive_minutes():
    start = datetime(2026, 8, 14, 12, 0, tzinfo=UTC)
    with pytest.raises(ValueError, match="both be set"):
        resolve_screen_session(
            started_at=start,
            ended_at=None,
            minutes=None,
            occurred_on=None,
            timezone=UTC,
            today=date(2026, 8, 14),
        )
    with pytest.raises(ValueError, match="greater than 0"):
        resolve_screen_session(
            started_at=None,
            ended_at=None,
            minutes=0,
            occurred_on=date(2026, 8, 14),
            timezone=UTC,
            today=date(2026, 8, 14),
        )


def test_interval_minutes_and_local_date_helpers():
    start = datetime(2026, 8, 14, 23, 30, tzinfo=UTC)
    end = datetime(2026, 8, 15, 0, 0, tzinfo=UTC)
    assert interval_minutes(start, end) == 30.0
    assert local_date(start, ZoneInfo("UTC")) == date(2026, 8, 14)


def _view(
    *,
    app: str,
    minutes: float,
    occurred_on: date,
    judgment: ScreenJudgment = ScreenJudgment.WASTE,
    started_at: datetime | None = None,
    ended_at: datetime | None = None,
    category: str = "entertainment",
    device: str | None = None,
    name: str | None = None,
) -> ScreenSessionView:
    return ScreenSessionView(
        minutes=minutes,
        occurred_on=occurred_on,
        app_slug=app,
        app_name=name if name is not None else app.title(),
        category_slug=category,
        category_name=category.title(),
        judgment=judgment,
        started_at=started_at,
        ended_at=ended_at,
        device_slug=device,
        device_name=device.title() if device else None,
    )


def test_clip_interval_hours_splits_midnight():
    slices = clip_interval_hours(
        datetime(2026, 8, 14, 23, 30, tzinfo=UTC),
        datetime(2026, 8, 15, 0, 45, tzinfo=UTC),
        UTC,
    )
    assert slices == [
        (date(2026, 8, 14), 23, 30.0),
        (date(2026, 8, 15), 0, 45.0),
    ]


def test_like_for_like_previous_week_and_month():
    assert previous_like_for_like(date(2026, 8, 12), Period.WEEK) == (
        date(2026, 8, 3),
        date(2026, 8, 5),
    )
    assert previous_like_for_like(date(2026, 3, 31), Period.MONTH) == (
        date(2026, 2, 1),
        date(2026, 2, 28),
    )
    assert previous_like_for_like(date(2026, 8, 14), Period.DAY) == (
        date(2026, 8, 13),
        date(2026, 8, 13),
    )


def test_score_bands():
    assert screen_score(70, 30, 0, 100) == 70
    assert score_band(70) is ScreenScoreBand.GOOD
    assert score_band(40) is ScreenScoreBand.OK
    assert score_band(39) is ScreenScoreBand.POOR
    assert screen_score(0, 0, 0, 0) is None


def test_dashboard_clips_interval_and_omits_duration_from_hours():
    views = [
        _view(
            app="youtube",
            minutes=75,
            occurred_on=date(2026, 8, 14),
            started_at=datetime(2026, 8, 14, 23, 30, tzinfo=UTC),
            ended_at=datetime(2026, 8, 15, 0, 45, tzinfo=UTC),
        ),
        _view(
            app="notes",
            minutes=20,
            occurred_on=date(2026, 8, 14),
            judgment=ScreenJudgment.USEFUL,
            category="learning",
        ),
    ]
    math = screen_dashboard_math(
        views,
        as_of=date(2026, 8, 14),
        period=Period.DAY,
        timezone=UTC,
    )
    assert math.total == 50.0
    assert math.hours[0][23] == 30.0
    assert math.hours[0][0] == 0.0
    assert math.apps[0].slug == "youtube"
    assert math.apps[0].minutes == 30.0
    assert math.apps[1].slug == "notes"
    assert math.apps[1].minutes == 20.0


def test_dashboard_week_comparison_and_weekend_spike():
    views = []
    for day in (date(2026, 8, 10), date(2026, 8, 11), date(2026, 8, 12)):
        views.append(
            _view(
                app="coding",
                minutes=40,
                occurred_on=day,
                judgment=ScreenJudgment.USEFUL,
                category="work",
            )
        )
    views.append(
        _view(
            app="youtube",
            minutes=80,
            occurred_on=date(2026, 8, 8),
            judgment=ScreenJudgment.WASTE,
        )
    )
    views.append(
        _view(
            app="youtube",
            minutes=80,
            occurred_on=date(2026, 8, 9),
            judgment=ScreenJudgment.WASTE,
        )
    )
    math = screen_dashboard_math(
        views,
        as_of=date(2026, 8, 12),
        period=Period.WEEK,
        timezone=UTC,
    )
    assert math.range_start == date(2026, 8, 10)
    assert math.range_end == date(2026, 8, 12)
    assert math.previous_start == date(2026, 8, 3)
    assert math.previous_end == date(2026, 8, 5)
    assert math.total == 120.0
    assert math.daily_average == 40.0
    assert len(math.comparison) == 3
    assert math.hours[0][0] == 0.0
    assert len(math.hours) == 7
    assert any(item.kind is ScreenInsightKind.WEEKEND_SPIKE for item in math.insights) is False


def test_weekend_spike_insight():
    views = [
        _view(
            app="coding",
            minutes=40,
            occurred_on=date(2026, 8, 10 + offset),
            judgment=ScreenJudgment.USEFUL,
            category="work",
        )
        for offset in range(5)
    ]
    views.extend(
        [
            _view(app="youtube", minutes=80, occurred_on=date(2026, 8, 15)),
            _view(app="youtube", minutes=80, occurred_on=date(2026, 8, 16)),
        ]
    )
    math = screen_dashboard_math(
        views,
        as_of=date(2026, 8, 16),
        period=Period.WEEK,
        timezone=UTC,
    )
    assert any(item.kind is ScreenInsightKind.WEEKEND_SPIKE for item in math.insights)


def test_insights_waste_late_night_sequence_improving():
    start = datetime(2026, 8, 14, 21, 0, tzinfo=UTC)
    mid = datetime(2026, 8, 14, 21, 40, tzinfo=UTC)
    end = datetime(2026, 8, 14, 22, 10, tzinfo=UTC)
    views = [
        _view(
            app="youtube",
            name="YouTube",
            minutes=40,
            occurred_on=date(2026, 8, 14),
            started_at=start,
            ended_at=mid,
        ),
        _view(
            app="instagram",
            name="Instagram",
            minutes=30,
            occurred_on=date(2026, 8, 14),
            started_at=datetime(2026, 8, 14, 21, 50, tzinfo=UTC),
            ended_at=end,
        ),
        _view(app="youtube", minutes=200, occurred_on=date(2026, 8, 13)),
    ]
    math = screen_dashboard_math(
        views,
        as_of=date(2026, 8, 14),
        period=Period.DAY,
        timezone=UTC,
    )
    kinds = {item.kind for item in math.insights}
    assert ScreenInsightKind.WASTE_SHARE in kinds
    assert ScreenInsightKind.SEQUENCE in kinds
    assert ScreenInsightKind.IMPROVING in kinds
    sequence = next(item for item in math.insights if item.kind is ScreenInsightKind.SEQUENCE)
    assert "YouTube → Instagram" in sequence.summary
    late = screen_dashboard_math(
        [
            _view(
                app="youtube",
                minutes=60,
                occurred_on=date(2026, 8, 14),
                started_at=datetime(2026, 8, 14, 22, 0, tzinfo=UTC),
                ended_at=datetime(2026, 8, 14, 23, 0, tzinfo=UTC),
            )
        ],
        as_of=date(2026, 8, 14),
        period=Period.DAY,
        timezone=UTC,
    )
    assert any(item.kind is ScreenInsightKind.LATE_NIGHT for item in late.insights)


def test_unknown_device_and_trend_weeks():
    views = [
        _view(app="instagram", minutes=30, occurred_on=date(2026, 8, 14)),
        _view(
            app="instagram",
            minutes=10,
            occurred_on=date(2026, 8, 14),
            device="iphone",
        ),
    ]
    math = screen_dashboard_math(
        views,
        as_of=date(2026, 8, 14),
        period=Period.WEEK,
        timezone=UTC,
    )
    slugs = [row.slug for row in math.devices]
    assert slugs[0] == "unknown"
    assert math.devices[0].name == "Unknown"
    assert len(math.trend) == 8
    assert math.trend[-1].week_start == date(2026, 8, 10)
