from datetime import date

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
    ScreenJudgment,
    add_minutes,
    current_streak,
    day_minutes,
    direction_for_judgment,
    member_apps,
    screen_day_totals,
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
