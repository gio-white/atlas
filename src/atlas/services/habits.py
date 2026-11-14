"""Habits: rule versions, your answers (marks), and freezes (habits brief §2, §5).

A habit is ticked by you (`manual`) or checked from your data (`data`). Its schedule and check
are stored as rule versions; a day is judged by the version in force that day. Only facts and
decisions are stored here. Results, streaks, and percentages are computed on read.

Habits only read other parts of Atlas (sleep, screen time, sessions); nothing here writes to
them.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from sqlmodel import Session, col, or_, select

from atlas.db.models import Habit, HabitFreeze, HabitMark, HabitRule, HabitSupport
from atlas.domain import (
    HabitApply,
    HabitCheck,
    HabitFrequency,
    HabitMarkResult,
    HabitSource,
    HabitThreshold,
    TimeOfDay,
)
from atlas.domain.habit_sources import SourceMeasure, SourceRef, source_spec
from atlas.domain.screen import local_date
from atlas.services.clock import resolve_today
from atlas.services.errors import NotFoundError, ValidationError
from atlas.services.lookups import (
    ensure_unique_slug,
    require_habit,
    require_screen_app,
    require_screen_category,
)
from atlas.services.slugs import normalize_slug, slug_from_name
from atlas.settings import load_settings

ARCHIVED_REASON = "Archived"
MINUTES_IN_DAY = 24 * 60


@dataclass(frozen=True, slots=True)
class RuleInput:
    """A rule as asked for: "How often?" plus "How is it checked?" (brief §9)."""

    frequency: HabitFrequency
    check: HabitCheck = HabitCheck.MANUAL
    weekdays: tuple[int, ...] | None = None
    times: int | None = None
    source: HabitSource | None = None
    source_ref: str | None = None
    threshold: HabitThreshold | None = None
    value: float | None = None


@dataclass(frozen=True, slots=True)
class HabitView:
    """A habit with the rule in force on `on`, and the name of the category or app it reads."""

    habit: Habit
    rule: HabitRule
    source_ref_name: str | None


def create_habit(
    session: Session,
    name: str,
    rule: RuleInput,
    *,
    slug: str | None = None,
    time_of_day: TimeOfDay = TimeOfDay.ANYTIME,
    first_day: date | None = None,
) -> Habit:
    if not isinstance(name, str) or not name.strip():
        raise ValidationError("a habit needs a name")
    slug = normalize_slug(slug) if slug is not None else slug_from_name(name)
    ensure_unique_slug(session, Habit, slug)
    rule = validate_rule(session, rule)
    first_day = resolve_today(None) if first_day is None else first_day
    habit = Habit(
        slug=slug, name=name.strip(), time_of_day=TimeOfDay(time_of_day), first_day=first_day
    )
    session.add(habit)
    session.flush()
    session.add(_rule_row(habit, rule, first_day))
    session.commit()
    session.refresh(habit)
    return habit


def list_habits(session: Session, *, include_archived: bool = True) -> list[Habit]:
    statement = select(Habit).order_by(Habit.name, Habit.slug)
    if not include_archived:
        statement = statement.where(col(Habit.archived_at).is_(None))
    return list(session.exec(statement).all())


def get_habit(session: Session, slug: str) -> Habit:
    return require_habit(session, normalize_slug(slug))


def habit_rules(session: Session, habit: Habit) -> list[HabitRule]:
    """Every rule version of a habit, oldest first."""
    return list(
        session.exec(
            select(HabitRule).where(HabitRule.habit_id == habit.id).order_by(HabitRule.starts_on)
        ).all()
    )


def rule_on(rules: Sequence[HabitRule], day: date) -> HabitRule:
    """The version in force on `day`; before the first day, the first version."""
    current = rules[0]
    for rule in rules:
        if rule.starts_on <= day:
            current = rule
    return current


def habit_view(session: Session, habit: Habit, *, on: date | None = None) -> HabitView:
    rule = rule_on(habit_rules(session, habit), resolve_today(on))
    return HabitView(habit=habit, rule=rule, source_ref_name=_source_ref_name(session, rule))


def update_habit(
    session: Session,
    slug: str,
    *,
    name: str | None = None,
    time_of_day: TimeOfDay | None = None,
    rule: RuleInput | None = None,
    apply: HabitApply = HabitApply.FROM_TODAY,
    today: date | None = None,
) -> Habit:
    """Rename, move to another time of day, or change the rule.

    A rule change applies `from_today` (a version starting today, replacing one already made
    today) or to `all_days` (every version replaced by one from the habit's first day). Name and
    time of day are not versioned. An unchanged rule stores nothing.
    """
    habit = require_habit(session, normalize_slug(slug))
    if name is not None:
        if not isinstance(name, str) or not name.strip():
            raise ValidationError("name must not be empty")
        habit.name = name.strip()
    if time_of_day is not None:
        habit.time_of_day = TimeOfDay(time_of_day)
    if rule is not None:
        _change_rule(session, habit, validate_rule(session, rule), HabitApply(apply), today)
    session.add(habit)
    session.commit()
    session.refresh(habit)
    return habit


def archive_habit(session: Session, slug: str) -> Habit:
    """Hide a habit everywhere but the Archived list. Its history stays."""
    habit = require_habit(session, normalize_slug(slug))
    if habit.archived_at is not None:
        raise ValidationError(f"habit {habit.slug!r} is already archived")
    habit.archived_at = datetime.now(UTC)
    session.add(habit)
    session.commit()
    session.refresh(habit)
    return habit


def restore_habit(session: Session, slug: str, *, today: date | None = None) -> Habit:
    """Bring an archived habit back. The days it was archived are frozen (reason "Archived"),
    so it does not return with a broken streak."""
    habit = require_habit(session, normalize_slug(slug))
    if habit.archived_at is None:
        raise ValidationError(f"habit {habit.slug!r} is not archived")
    today = resolve_today(today)
    archived_on = max(local_date(habit.archived_at, load_settings().timezone), habit.first_day)
    yesterday = today - timedelta(days=1)
    if archived_on <= yesterday:
        session.add(
            HabitFreeze(
                habit_id=habit.id, start_on=archived_on, end_on=yesterday, reason=ARCHIVED_REASON
            )
        )
    habit.archived_at = None
    session.add(habit)
    session.commit()
    session.refresh(habit)
    return habit


def delete_habit(session: Session, slug: str) -> None:
    """Delete a habit with its history: rule versions, answers, its own freezes, quest links."""
    habit = require_habit(session, normalize_slug(slug))
    for model in (HabitRule, HabitMark, HabitFreeze, HabitSupport):
        for row in session.exec(select(model).where(model.habit_id == habit.id)).all():
            session.delete(row)
    session.flush()
    session.delete(habit)
    session.commit()


def set_habit_day(
    session: Session,
    slug: str,
    day: date,
    result: HabitMarkResult,
    *,
    today: date | None = None,
) -> HabitMark | None:
    """Answer a day: Mark done or Mark not done.

    On a manual habit Done is a tick and Not done removes it (a day without a tick is Not done).
    On a data habit either answer is stored and wins over the data ("Set by you").
    """
    habit = require_habit(session, normalize_slug(slug))
    _check_answerable(habit, day, resolve_today(today))
    result = HabitMarkResult(result)
    rule = rule_on(habit_rules(session, habit), day)
    mark = _mark_on(session, habit, day)
    if HabitCheck(rule.check) is HabitCheck.MANUAL and result is HabitMarkResult.NOT_DONE:
        if mark is not None:
            session.delete(mark)
            session.commit()
        return None
    if mark is None:
        mark = HabitMark(habit_id=habit.id, day=day, result=result)
    else:
        mark.result = result
        mark.created_at = datetime.now(UTC)
    session.add(mark)
    session.commit()
    session.refresh(mark)
    return mark


def clear_habit_day(session: Session, slug: str, day: date) -> None:
    """Remove your answer for a day: untick, or "Use data again". Nothing to remove is fine."""
    habit = require_habit(session, normalize_slug(slug))
    mark = _mark_on(session, habit, day)
    if mark is not None:
        session.delete(mark)
        session.commit()


def habit_marks(session: Session, habit: Habit) -> list[HabitMark]:
    return list(
        session.exec(
            select(HabitMark).where(HabitMark.habit_id == habit.id).order_by(HabitMark.day)
        ).all()
    )


def add_freeze(
    session: Session,
    *,
    start_on: date | None = None,
    end_on: date | None = None,
    reason: str | None = None,
    habit_slug: str | None = None,
) -> HabitFreeze:
    """Freeze one habit, or every habit when `habit_slug` is empty, from `start_on` to
    `end_on` (one day when no end is given; today when neither is)."""
    habit = require_habit(session, normalize_slug(habit_slug)) if habit_slug else None
    start_on = resolve_today(None) if start_on is None else start_on
    end_on = start_on if end_on is None else end_on
    if end_on < start_on:
        raise ValidationError("the end date must be on or after the start date")
    row = HabitFreeze(
        habit_id=habit.id if habit is not None else None,
        start_on=start_on,
        end_on=end_on,
        reason=(reason.strip() or None) if isinstance(reason, str) else None,
    )
    session.add(row)
    session.commit()
    session.refresh(row)
    return row


def list_freezes(session: Session, *, habit_slug: str | None = None) -> list[HabitFreeze]:
    """All freezes, newest first; for a habit, its own freezes and those for all habits."""
    statement = select(HabitFreeze).order_by(
        col(HabitFreeze.start_on).desc(), col(HabitFreeze.id).desc()
    )
    if habit_slug:
        habit = require_habit(session, normalize_slug(habit_slug))
        statement = statement.where(
            or_(col(HabitFreeze.habit_id) == habit.id, col(HabitFreeze.habit_id).is_(None))
        )
    return list(session.exec(statement).all())


def delete_freeze(session: Session, freeze_id: int) -> None:
    row = session.get(HabitFreeze, freeze_id)
    if row is None:
        raise NotFoundError("freeze", freeze_id)
    session.delete(row)
    session.commit()


def freeze_habit_slug(session: Session, freeze: HabitFreeze) -> str | None:
    if freeze.habit_id is None:
        return None
    habit = session.get(Habit, freeze.habit_id)
    return habit.slug if habit is not None else None


def validate_rule(session: Session, rule: RuleInput) -> RuleInput:
    """Check a rule and fill a data source's default threshold and value."""
    frequency = HabitFrequency(rule.frequency)
    weekdays: tuple[int, ...] | None = None
    times: int | None = None
    if frequency is HabitFrequency.SPECIFIC_DAYS:
        days = sorted({int(day) for day in rule.weekdays or ()})
        if not days:
            raise ValidationError("pick at least one day")
        if any(day < 1 or day > 7 for day in days):
            raise ValidationError("days must be 1 (Monday) to 7 (Sunday)")
        weekdays = tuple(days)
    elif rule.weekdays:
        raise ValidationError("days are only set for specific days")
    if frequency in (HabitFrequency.TIMES_A_WEEK, HabitFrequency.TIMES_A_MONTH):
        most = 7 if frequency is HabitFrequency.TIMES_A_WEEK else 31
        if rule.times is None or not 1 <= int(rule.times) <= most:
            raise ValidationError(f"times must be 1 to {most}")
        times = int(rule.times)
    elif rule.times is not None:
        raise ValidationError("times are only set for times a week or a month")

    check = HabitCheck(rule.check)
    if check is HabitCheck.MANUAL:
        data_fields = (rule.source, rule.source_ref, rule.threshold, rule.value)
        if any(field is not None for field in data_fields):
            raise ValidationError("a habit you tick has no source or threshold")
        return RuleInput(frequency=frequency, weekdays=weekdays, times=times, check=check)

    if rule.source is None:
        raise ValidationError("a data habit needs a source")
    spec = source_spec(HabitSource(rule.source))
    threshold = HabitThreshold(rule.threshold) if rule.threshold else spec.default_threshold
    if threshold not in spec.thresholds:
        allowed = ", ".join(item.value for item in spec.thresholds)
        raise ValidationError(f"{spec.label} takes {allowed}")
    value = spec.default_value if rule.value is None else float(rule.value)
    if spec.measure is SourceMeasure.TIME_OF_DAY:
        if not 0 <= value < MINUTES_IN_DAY:
            raise ValidationError("a time must be between 00:00 and 23:59")
    elif not 0 < value <= MINUTES_IN_DAY:
        raise ValidationError("minutes must be more than 0 and at most 24 hours")
    source_ref: str | None = None
    if spec.ref is SourceRef.CATEGORY:
        source_ref = _active_ref(rule.source_ref, "category")
        category = require_screen_category(session, source_ref)
        if category.archived_at is not None:
            raise ValidationError(f"category {source_ref!r} is archived")
    elif spec.ref is SourceRef.APP:
        source_ref = _active_ref(rule.source_ref, "app")
        app = require_screen_app(session, source_ref)
        if app.archived_at is not None:
            raise ValidationError(f"app {source_ref!r} is archived")
    elif rule.source_ref is not None:
        raise ValidationError(f"{spec.label} does not take a category or app")
    return RuleInput(
        frequency=frequency,
        weekdays=weekdays,
        times=times,
        check=check,
        source=spec.source,
        source_ref=source_ref,
        threshold=threshold,
        value=value,
    )


def rule_input(rule: HabitRule) -> RuleInput:
    return RuleInput(
        frequency=HabitFrequency(rule.frequency),
        weekdays=tuple(rule.weekdays) if rule.weekdays else None,
        times=rule.times,
        check=HabitCheck(rule.check),
        source=HabitSource(rule.source) if rule.source else None,
        source_ref=rule.source_ref,
        threshold=HabitThreshold(rule.threshold) if rule.threshold else None,
        value=rule.value,
    )


def _change_rule(
    session: Session, habit: Habit, rule: RuleInput, apply: HabitApply, today: date | None
) -> None:
    today = resolve_today(today)
    rules = habit_rules(session, habit)
    if apply is HabitApply.ALL_DAYS:
        if len(rules) == 1 and rule_input(rules[0]) == rule:
            return
        for row in rules:
            session.delete(row)
        session.flush()
        session.add(_rule_row(habit, rule, habit.first_day))
        return
    starts_on = max(today, habit.first_day)
    if rule_input(rule_on(rules, starts_on)) == rule:
        return
    same_day = next((row for row in rules if row.starts_on == starts_on), None)
    if same_day is not None:
        session.delete(same_day)
        session.flush()
    session.add(_rule_row(habit, rule, starts_on))


def _rule_row(habit: Habit, rule: RuleInput, starts_on: date) -> HabitRule:
    return HabitRule(
        habit_id=habit.id,
        starts_on=starts_on,
        frequency=rule.frequency,
        weekdays=list(rule.weekdays) if rule.weekdays else None,
        times=rule.times,
        check=rule.check,
        source=rule.source,
        source_ref=rule.source_ref,
        threshold=rule.threshold,
        value=rule.value,
    )


def _source_ref_name(session: Session, rule: HabitRule) -> str | None:
    if rule.source is None or rule.source_ref is None:
        return None
    ref = source_spec(HabitSource(rule.source)).ref
    if ref is SourceRef.CATEGORY:
        return require_screen_category(session, rule.source_ref).name
    if ref is SourceRef.APP:
        return require_screen_app(session, rule.source_ref).name
    return None


def _active_ref(value: str | None, what: str) -> str:
    if not value:
        raise ValidationError(f"pick a {what}")
    return normalize_slug(value)


def _check_answerable(habit: Habit, day: date, today: date) -> None:
    if day > today:
        raise ValidationError("a future day cannot be answered yet")
    if day < habit.first_day:
        raise ValidationError(f"habit {habit.slug!r} starts on {habit.first_day.isoformat()}")


def _mark_on(session: Session, habit: Habit, day: date) -> HabitMark | None:
    return session.exec(
        select(HabitMark).where(HabitMark.habit_id == habit.id, HabitMark.day == day)
    ).first()
