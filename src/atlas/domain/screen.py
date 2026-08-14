from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta, tzinfo

from atlas.domain.buckets import bucket_for, previous_bucket
from atlas.domain.enums import (
    Aggregation,
    Direction,
    Period,
    ScreenBudgetTargetKind,
    ScreenInsightKind,
    ScreenJudgment,
    ScreenScoreBand,
)
from atlas.domain.models import (
    EntryView,
    ScreenAppSpec,
    ScreenBudgetSpec,
    ScreenCategorySpec,
    ScreenSessionSpec,
    ScreenSessionView,
)
from atlas.domain.rollup import rollup

MINUTES_EPSILON = 0.01


def interval_minutes(started_at: datetime, ended_at: datetime) -> float:
    return (_as_utc(ended_at) - _as_utc(started_at)).total_seconds() / 60.0


def local_date(instant: datetime, timezone: tzinfo) -> date:
    return _as_utc(instant).astimezone(timezone).date()


def resolve_screen_session(
    *,
    started_at: datetime | None,
    ended_at: datetime | None,
    minutes: float | None,
    occurred_on: date | None,
    timezone: tzinfo,
    today: date,
) -> ScreenSessionSpec:
    has_start = started_at is not None
    has_end = ended_at is not None
    if has_start != has_end:
        raise ValueError("started_at and ended_at must both be set, or both omitted")
    if has_start and has_end:
        start = _as_utc(started_at)
        end = _as_utc(ended_at)
        if end <= start:
            raise ValueError("ended_at must be after started_at")
        derived = interval_minutes(start, end)
        if derived <= 0:
            raise ValueError("minutes must be greater than 0")
        if minutes is not None and abs(float(minutes) - derived) > MINUTES_EPSILON:
            raise ValueError("minutes must match the interval")
        return ScreenSessionSpec(
            occurred_on=local_date(start, timezone),
            minutes=derived,
            started_at=start,
            ended_at=end,
        )
    if minutes is None:
        raise ValueError("provide started_at and ended_at, or minutes")
    value = float(minutes)
    if value <= 0:
        raise ValueError("minutes must be greater than 0")
    if occurred_on is not None and (
        isinstance(occurred_on, datetime) or not isinstance(occurred_on, date)
    ):
        raise ValueError("occurred_on must be a date")
    return ScreenSessionSpec(
        occurred_on=occurred_on if occurred_on is not None else today,
        minutes=value,
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


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
        return [app for app in apps if by_slug[app.category_slug].judgment is judgment]
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


UNKNOWN_DEVICE_SLUG = "unknown"
UNKNOWN_DEVICE_NAME = "Unknown"
SEQUENCE_GAP = timedelta(minutes=15)
LATE_NIGHT_HOURS = frozenset({22, 23, 0, 1, 2, 3, 4})
WEEKEND_SPIKE_RATIO = 1.25
WASTE_SHARE_THRESHOLD = 0.4
LATE_NIGHT_SHARE_THRESHOLD = 0.2
IMPROVING_FRACTION = -0.1
TREND_WEEKS = 8


@dataclass(frozen=True, slots=True)
class ScreenAppShare:
    slug: str
    name: str
    category: str
    category_name: str
    judgment: ScreenJudgment
    minutes: float
    share: float


@dataclass(frozen=True, slots=True)
class ScreenCategoryShare:
    slug: str
    name: str
    judgment: ScreenJudgment
    minutes: float
    share: float
    apps: tuple[ScreenAppShare, ...]


@dataclass(frozen=True, slots=True)
class ScreenDeviceShare:
    slug: str
    name: str
    minutes: float
    share: float


@dataclass(frozen=True, slots=True)
class ScreenDayBar:
    date: date
    useful: float
    waste: float
    neutral: float
    total: float


@dataclass(frozen=True, slots=True)
class ScreenComparisonPoint:
    current: float
    previous: float


@dataclass(frozen=True, slots=True)
class ScreenTrendPoint:
    week_start: date
    daily_average: float | None


@dataclass(frozen=True, slots=True)
class ScreenLongestDay:
    date: date
    minutes: float


@dataclass(frozen=True, slots=True)
class ScreenInsight:
    kind: ScreenInsightKind
    summary: str
    prescription: str


@dataclass(frozen=True, slots=True)
class ScreenDashboardMath:
    period: Period
    as_of: date
    range_start: date
    range_end: date
    previous_start: date
    previous_end: date
    total: float | None
    daily_average: float | None
    longest_day: ScreenLongestDay | None
    delta_minutes: float | None
    delta_fraction: float | None
    score: int | None
    score_band: ScreenScoreBand | None
    useful: float | None
    waste: float | None
    neutral: float | None
    apps: tuple[ScreenAppShare, ...]
    categories: tuple[ScreenCategoryShare, ...]
    devices: tuple[ScreenDeviceShare, ...]
    daily: tuple[ScreenDayBar, ...]
    comparison: tuple[ScreenComparisonPoint, ...]
    hours: tuple[tuple[float, ...], ...]
    trend: tuple[ScreenTrendPoint, ...]
    insights: tuple[ScreenInsight, ...]


def clip_interval_hours(
    started_at: datetime,
    ended_at: datetime,
    timezone: tzinfo,
) -> list[tuple[date, int, float]]:
    start = _as_utc(started_at).astimezone(timezone)
    end = _as_utc(ended_at).astimezone(timezone)
    if end <= start:
        return []
    cursor = start.replace(minute=0, second=0, microsecond=0)
    slices: list[tuple[date, int, float]] = []
    while cursor < end:
        hour_end = cursor + timedelta(hours=1)
        overlap_start = max(start, cursor)
        overlap_end = min(end, hour_end)
        if overlap_end > overlap_start:
            minutes = (overlap_end - overlap_start).total_seconds() / 60.0
            slices.append((cursor.date(), cursor.hour, minutes))
        cursor = hour_end
    return slices


def attributed_day_minutes(
    view: ScreenSessionView,
    timezone: tzinfo,
) -> dict[date, float]:
    if view.has_interval() and view.started_at is not None and view.ended_at is not None:
        by_day: dict[date, float] = {}
        for day, _hour, minutes in clip_interval_hours(view.started_at, view.ended_at, timezone):
            by_day[day] = by_day.get(day, 0.0) + minutes
        return by_day
    return {view.occurred_on: view.minutes}


def session_entry_views(
    views: Sequence[ScreenSessionView],
    timezone: tzinfo,
) -> dict[str, list[EntryView]]:
    by_app: dict[str, list[EntryView]] = {}
    for view in views:
        for day, minutes in attributed_day_minutes(view, timezone).items():
            by_app.setdefault(view.app_slug, []).append(
                EntryView(occurred_on=day, value_num=minutes)
            )
    return by_app


def clipped_period_range(as_of: date, period: Period) -> tuple[date, date]:
    bucket = bucket_for(as_of, period)
    return bucket.start, min(bucket.end, as_of)


def previous_like_for_like(as_of: date, period: Period) -> tuple[date, date]:
    start, end = clipped_period_range(as_of, period)
    elapsed = (end - start).days + 1
    if period is Period.DAY:
        previous = as_of - timedelta(days=1)
        return previous, previous
    previous = previous_bucket(bucket_for(as_of, period))
    previous_end = min(previous.start + timedelta(days=elapsed - 1), previous.end)
    return previous.start, previous_end


def minutes_in_range(
    views: Sequence[ScreenSessionView],
    start: date,
    end: date,
    timezone: tzinfo,
) -> float | None:
    total = 0.0
    found = False
    for view in views:
        for day, minutes in attributed_day_minutes(view, timezone).items():
            if start <= day <= end:
                total += minutes
                found = True
    return total if found else None


def screen_score(useful: float, waste: float, neutral: float, total: float) -> int | None:
    if total <= 0:
        return None
    return round(100 * (useful + 0.5 * neutral) / total)


def score_band(score: int | None) -> ScreenScoreBand | None:
    if score is None:
        return None
    if score >= 70:
        return ScreenScoreBand.GOOD
    if score >= 40:
        return ScreenScoreBand.OK
    return ScreenScoreBand.POOR


def screen_dashboard_math(
    views: Sequence[ScreenSessionView],
    *,
    as_of: date,
    period: Period,
    timezone: tzinfo,
) -> ScreenDashboardMath:
    period = Period(period)
    range_start, range_end = clipped_period_range(as_of, period)
    previous_start, previous_end = previous_like_for_like(as_of, period)
    total = minutes_in_range(views, range_start, range_end, timezone)
    previous_total = minutes_in_range(views, previous_start, previous_end, timezone)
    elapsed = (range_end - range_start).days + 1
    daily_average = None if total is None else total / elapsed
    daily = _daily_bars(views, range_start, range_end, timezone)
    longest = _longest_day(daily) if total is not None else None
    delta_minutes, delta_fraction = _delta(total, previous_total)
    useful, waste, neutral = _judgment_totals(daily, total)
    score = (
        None if total is None else screen_score(useful or 0.0, waste or 0.0, neutral or 0.0, total)
    )
    apps = _app_shares(views, range_start, range_end, timezone, total)
    return ScreenDashboardMath(
        period=period,
        as_of=as_of,
        range_start=range_start,
        range_end=range_end,
        previous_start=previous_start,
        previous_end=previous_end,
        total=total,
        daily_average=daily_average,
        longest_day=longest,
        delta_minutes=delta_minutes,
        delta_fraction=delta_fraction,
        score=score,
        score_band=score_band(score),
        useful=useful,
        waste=waste,
        neutral=neutral,
        apps=apps,
        categories=_category_shares(apps, total),
        devices=_device_shares(views, range_start, range_end, timezone, total),
        daily=daily,
        comparison=_comparison_series(
            views,
            range_start,
            range_end,
            previous_start,
            previous_end,
            timezone,
        ),
        hours=_hour_grid(views, range_start, range_end, period, timezone),
        trend=_trend(views, as_of, timezone),
        insights=_insights(
            views,
            daily,
            range_start,
            range_end,
            timezone,
            waste=waste,
            total=total,
            delta_fraction=delta_fraction,
        ),
    )


def _days(start: date, end: date) -> list[date]:
    return [start + timedelta(days=offset) for offset in range((end - start).days + 1)]


def _daily_bars(
    views: Sequence[ScreenSessionView],
    start: date,
    end: date,
    timezone: tzinfo,
) -> tuple[ScreenDayBar, ...]:
    bars = {
        day: {ScreenJudgment.USEFUL: 0.0, ScreenJudgment.WASTE: 0.0, ScreenJudgment.NEUTRAL: 0.0}
        for day in _days(start, end)
    }
    for view in views:
        for day, minutes in attributed_day_minutes(view, timezone).items():
            if day not in bars:
                continue
            bars[day][view.judgment] += minutes
    return tuple(
        ScreenDayBar(
            date=day,
            useful=values[ScreenJudgment.USEFUL],
            waste=values[ScreenJudgment.WASTE],
            neutral=values[ScreenJudgment.NEUTRAL],
            total=sum(values.values()),
        )
        for day, values in bars.items()
    )


def _longest_day(daily: Sequence[ScreenDayBar]) -> ScreenLongestDay | None:
    if not daily:
        return None
    best = max(daily, key=lambda bar: (bar.total, -bar.date.toordinal()))
    if best.total <= 0:
        return None
    return ScreenLongestDay(date=best.date, minutes=best.total)


def _delta(
    current: float | None,
    previous: float | None,
) -> tuple[float | None, float | None]:
    if current is None and previous is None:
        return None, None
    this_value = current or 0.0
    last_value = previous or 0.0
    fraction = None if last_value == 0 else (this_value - last_value) / last_value
    return this_value - last_value, fraction


def _judgment_totals(
    daily: Sequence[ScreenDayBar],
    total: float | None,
) -> tuple[float | None, float | None, float | None]:
    if total is None:
        return None, None, None
    useful = sum(bar.useful for bar in daily)
    waste = sum(bar.waste for bar in daily)
    neutral = sum(bar.neutral for bar in daily)
    return useful, waste, neutral


def _app_shares(
    views: Sequence[ScreenSessionView],
    start: date,
    end: date,
    timezone: tzinfo,
    total: float | None,
) -> tuple[ScreenAppShare, ...]:
    if total is None or total <= 0:
        return ()
    buckets: dict[str, ScreenAppShare] = {}
    for view in views:
        minutes = sum(
            value
            for day, value in attributed_day_minutes(view, timezone).items()
            if start <= day <= end
        )
        if minutes <= 0:
            continue
        existing = buckets.get(view.app_slug)
        if existing is None:
            buckets[view.app_slug] = ScreenAppShare(
                slug=view.app_slug,
                name=view.app_name,
                category=view.category_slug,
                category_name=view.category_name,
                judgment=view.judgment,
                minutes=minutes,
                share=minutes / total,
            )
        else:
            combined = existing.minutes + minutes
            buckets[view.app_slug] = ScreenAppShare(
                slug=existing.slug,
                name=existing.name,
                category=existing.category,
                category_name=existing.category_name,
                judgment=existing.judgment,
                minutes=combined,
                share=combined / total,
            )
    return tuple(sorted(buckets.values(), key=lambda row: (-row.minutes, row.slug)))


def _category_shares(
    apps: Sequence[ScreenAppShare],
    total: float | None,
) -> tuple[ScreenCategoryShare, ...]:
    if total is None or total <= 0:
        return ()
    grouped: dict[str, list[ScreenAppShare]] = {}
    meta: dict[str, ScreenAppShare] = {}
    for app in apps:
        grouped.setdefault(app.category, []).append(app)
        meta.setdefault(app.category, app)
    rows = []
    for slug, members in grouped.items():
        minutes = sum(app.minutes for app in members)
        sample = meta[slug]
        rows.append(
            ScreenCategoryShare(
                slug=slug,
                name=sample.category_name,
                judgment=sample.judgment,
                minutes=minutes,
                share=minutes / total,
                apps=tuple(members),
            )
        )
    return tuple(sorted(rows, key=lambda row: (-row.minutes, row.slug)))


def _device_shares(
    views: Sequence[ScreenSessionView],
    start: date,
    end: date,
    timezone: tzinfo,
    total: float | None,
) -> tuple[ScreenDeviceShare, ...]:
    if total is None or total <= 0:
        return ()
    buckets: dict[str, ScreenDeviceShare] = {}
    for view in views:
        minutes = sum(
            value
            for day, value in attributed_day_minutes(view, timezone).items()
            if start <= day <= end
        )
        if minutes <= 0:
            continue
        slug = view.device_slug if view.device_slug else UNKNOWN_DEVICE_SLUG
        name = view.device_name if view.device_slug and view.device_name else UNKNOWN_DEVICE_NAME
        existing = buckets.get(slug)
        if existing is None:
            buckets[slug] = ScreenDeviceShare(
                slug=slug,
                name=name,
                minutes=minutes,
                share=minutes / total,
            )
        else:
            combined = existing.minutes + minutes
            buckets[slug] = ScreenDeviceShare(
                slug=existing.slug,
                name=existing.name,
                minutes=combined,
                share=combined / total,
            )
    return tuple(sorted(buckets.values(), key=lambda row: (-row.minutes, row.slug)))


def _comparison_series(
    views: Sequence[ScreenSessionView],
    start: date,
    end: date,
    previous_start: date,
    previous_end: date,
    timezone: tzinfo,
) -> tuple[ScreenComparisonPoint, ...]:
    current_days = _days(start, end)
    previous_days = _days(previous_start, previous_end)
    current_totals = _totals_by_day(views, start, end, timezone)
    previous_totals = _totals_by_day(views, previous_start, previous_end, timezone)
    length = min(len(current_days), len(previous_days))
    return tuple(
        ScreenComparisonPoint(
            current=current_totals.get(current_days[index], 0.0),
            previous=previous_totals.get(previous_days[index], 0.0),
        )
        for index in range(length)
    )


def _totals_by_day(
    views: Sequence[ScreenSessionView],
    start: date,
    end: date,
    timezone: tzinfo,
) -> dict[date, float]:
    totals = {day: 0.0 for day in _days(start, end)}
    for view in views:
        for day, minutes in attributed_day_minutes(view, timezone).items():
            if day in totals:
                totals[day] += minutes
    return totals


def _hour_grid(
    views: Sequence[ScreenSessionView],
    start: date,
    end: date,
    period: Period,
    timezone: tzinfo,
) -> tuple[tuple[float, ...], ...]:
    days = _days(start, end)
    by_day_hour = {day: [0.0] * 24 for day in days}
    for view in views:
        if not view.has_interval() or view.started_at is None or view.ended_at is None:
            continue
        for day, hour, minutes in clip_interval_hours(view.started_at, view.ended_at, timezone):
            if day in by_day_hour:
                by_day_hour[day][hour] += minutes
    if period is Period.DAY:
        return (tuple(by_day_hour[days[0]]),)
    if period is Period.WEEK:
        bucket_start = bucket_for(end, Period.WEEK).start
        rows = []
        for offset in range(7):
            day = bucket_start + timedelta(days=offset)
            rows.append(tuple(by_day_hour.get(day, [0.0] * 24)))
        return tuple(rows)
    weekday_sums = [[0.0] * 24 for _ in range(7)]
    weekday_counts = [0] * 7
    for day in days:
        weekday = day.isoweekday() - 1
        weekday_counts[weekday] += 1
        for hour, minutes in enumerate(by_day_hour[day]):
            weekday_sums[weekday][hour] += minutes
    rows = []
    for weekday in range(7):
        count = weekday_counts[weekday]
        if count == 0:
            rows.append(tuple(0.0 for _ in range(24)))
            continue
        rows.append(tuple(value / count for value in weekday_sums[weekday]))
    return tuple(rows)


def _trend(
    views: Sequence[ScreenSessionView],
    as_of: date,
    timezone: tzinfo,
) -> tuple[ScreenTrendPoint, ...]:
    bucket = bucket_for(as_of, Period.WEEK)
    weeks: list[tuple[date, date]] = []
    for _ in range(TREND_WEEKS):
        weeks.append((bucket.start, min(bucket.end, as_of)))
        bucket = previous_bucket(bucket)
    weeks.reverse()
    points = []
    for start, end in weeks:
        total = minutes_in_range(views, start, end, timezone)
        elapsed = (end - start).days + 1
        points.append(
            ScreenTrendPoint(
                week_start=start,
                daily_average=None if total is None else total / elapsed,
            )
        )
    return tuple(points)


def _insights(
    views: Sequence[ScreenSessionView],
    daily: Sequence[ScreenDayBar],
    start: date,
    end: date,
    timezone: tzinfo,
    *,
    waste: float | None,
    total: float | None,
    delta_fraction: float | None,
) -> tuple[ScreenInsight, ...]:
    insights: list[ScreenInsight] = []
    weekend = _weekend_spike(daily)
    if weekend is not None:
        insights.append(weekend)
    if (
        total is not None
        and total > 0
        and waste is not None
        and (waste / total) > WASTE_SHARE_THRESHOLD
    ):
        insights.append(
            ScreenInsight(
                kind=ScreenInsightKind.WASTE_SHARE,
                summary="Waste apps are more than 40% of this period.",
                prescription="Cap the waste category before it becomes the default evening loop.",
            )
        )
    late_night = _late_night(views, start, end, timezone)
    if late_night is not None:
        insights.append(late_night)
    if delta_fraction is not None and delta_fraction <= IMPROVING_FRACTION:
        insights.append(
            ScreenInsight(
                kind=ScreenInsightKind.IMPROVING,
                summary="This period is at least 10% below the last one.",
                prescription="Keep the current pace — the cut is holding versus last period.",
            )
        )
    sequence = _sequence_insight(views, start, end, timezone)
    if sequence is not None:
        insights.append(sequence)
    return tuple(insights)


def _weekend_spike(daily: Sequence[ScreenDayBar]) -> ScreenInsight | None:
    weekday = [bar.total for bar in daily if bar.date.isoweekday() < 6]
    weekend = [bar.total for bar in daily if bar.date.isoweekday() >= 6]
    if not weekday or not weekend:
        return None
    weekday_avg = sum(weekday) / len(weekday)
    weekend_avg = sum(weekend) / len(weekend)
    if weekday_avg <= 0 or weekend_avg <= weekday_avg * WEEKEND_SPIKE_RATIO:
        return None
    return ScreenInsight(
        kind=ScreenInsightKind.WEEKEND_SPIKE,
        summary="Weekend daily average is more than 25% above weekdays.",
        prescription="Set a weekend cap so Saturday and Sunday do not outrun the weekday pace.",
    )


def _late_night(
    views: Sequence[ScreenSessionView],
    start: date,
    end: date,
    timezone: tzinfo,
) -> ScreenInsight | None:
    interval_minutes = 0.0
    late_minutes = 0.0
    for view in views:
        if not view.has_interval() or view.started_at is None or view.ended_at is None:
            continue
        for day, hour, minutes in clip_interval_hours(view.started_at, view.ended_at, timezone):
            if not (start <= day <= end):
                continue
            interval_minutes += minutes
            if hour in LATE_NIGHT_HOURS:
                late_minutes += minutes
    if interval_minutes <= 0 or (late_minutes / interval_minutes) <= LATE_NIGHT_SHARE_THRESHOLD:
        return None
    return ScreenInsight(
        kind=ScreenInsightKind.LATE_NIGHT,
        summary="More than 20% of timed minutes fall between 22:00 and 05:00.",
        prescription="Wind down earlier; move late-night sessions before 22:00.",
    )


def _sequence_insight(
    views: Sequence[ScreenSessionView],
    start: date,
    end: date,
    timezone: tzinfo,
) -> ScreenInsight | None:
    overlapping = []
    for view in views:
        if not view.has_interval() or view.started_at is None or view.ended_at is None:
            continue
        if any(start <= day <= end for day in attributed_day_minutes(view, timezone)):
            overlapping.append(view)
    overlapping.sort(key=lambda view: _as_utc(view.started_at) if view.started_at else datetime.min)
    pairs: Counter[tuple[str, str]] = Counter()
    names: dict[str, str] = {}
    for left, right in zip(overlapping, overlapping[1:], strict=False):
        if left.ended_at is None or right.started_at is None:
            continue
        gap = _as_utc(right.started_at) - _as_utc(left.ended_at)
        if timedelta(0) <= gap <= SEQUENCE_GAP and left.app_slug != right.app_slug:
            pairs[(left.app_slug, right.app_slug)] += 1
            names[left.app_slug] = left.app_name
            names[right.app_slug] = right.app_name
    if not pairs:
        return None
    app_a, app_b = pairs.most_common(1)[0][0]
    label_a = names.get(app_a, app_a)
    label_b = names.get(app_b, app_b)
    return ScreenInsight(
        kind=ScreenInsightKind.SEQUENCE,
        summary=f"The most common handoff is {label_a} → {label_b}.",
        prescription=(
            f"Break the {label_a} → {label_b} chain; insert a pause before opening {label_b}."
        ),
    )
