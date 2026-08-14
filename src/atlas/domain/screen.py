from collections.abc import Mapping, Sequence
from datetime import date

from atlas.domain.enums import Aggregation, Direction, ScreenBudgetTargetKind, ScreenJudgment
from atlas.domain.models import EntryView, ScreenAppSpec, ScreenBudgetSpec, ScreenCategorySpec
from atlas.domain.rollup import rollup


def direction_for_judgment(judgment: ScreenJudgment) -> Direction:
    if judgment is ScreenJudgment.USEFUL:
        return Direction.HIGHER_IS_BETTER
    if judgment is ScreenJudgment.WASTE:
        return Direction.LOWER_IS_BETTER
    return Direction.NEUTRAL


def add_minutes(left: float | None, right: float | None) -> float | None:
    if left is None:
        return right
    if right is None:
        return left
    return left + right


def day_minutes(entries: Sequence[EntryView], day: date) -> float | None:
    return rollup([entry for entry in entries if entry.occurred_on == day], Aggregation.SUM)


def member_apps(
    apps: Sequence[ScreenAppSpec],
    categories: Sequence[ScreenCategorySpec],
    budget: ScreenBudgetSpec,
) -> list[ScreenAppSpec]:
    by_slug = {category.slug: category for category in categories}
    if budget.target_kind is ScreenBudgetTargetKind.JUDGMENT:
        judgment = ScreenJudgment(budget.target_slug)
        return [
            app
            for app in apps
            if by_slug[app.category_slug].judgment is judgment
        ]
    return [app for app in apps if app.category_slug == budget.target_slug]


def screen_day_totals(
    apps: Sequence[ScreenAppSpec],
    categories: Sequence[ScreenCategorySpec],
    entries_by_metric: Mapping[str, Sequence[EntryView]],
    day: date,
) -> tuple[dict[str, float | None], dict[str, float | None], dict[ScreenJudgment, float | None]]:
    by_app = {
        app.slug: day_minutes(entries_by_metric.get(app.metric_slug, []), day) for app in apps
    }
    by_category: dict[str, float | None] = {category.slug: None for category in categories}
    by_judgment: dict[ScreenJudgment, float | None] = {
        ScreenJudgment.USEFUL: None,
        ScreenJudgment.WASTE: None,
        ScreenJudgment.NEUTRAL: None,
    }
    category_by_slug = {category.slug: category for category in categories}
    for app in apps:
        category = category_by_slug[app.category_slug]
        minutes = by_app[app.slug]
        by_category[category.slug] = add_minutes(by_category[category.slug], minutes)
        by_judgment[category.judgment] = add_minutes(by_judgment[category.judgment], minutes)
    return by_app, by_category, by_judgment
