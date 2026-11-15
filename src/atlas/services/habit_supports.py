"""Habit → quest links: a habit supports quest items at any level (redesign brief phase 6).

A link is informational. No quest rule reads `habit_support`: `QuestIndex` never loads it, so
progress, completion, weights, eligibility, and Next action are the same with or without links.
"""

from dataclasses import dataclass
from datetime import datetime

from sqlmodel import Session, select

from atlas.db.models import Habit, HabitSupport
from atlas.domain import HabitCheck
from atlas.domain.quests import QuestKind
from atlas.services.clock import resolve_today
from atlas.services.errors import ConflictError, NotFoundError, ValidationError
from atlas.services.habits import habit_rules, rule_on
from atlas.services.lookups import require_habit
from atlas.services.quests import SUPPORT_COLUMNS, ItemRef, Key, QuestIndex
from atlas.services.slugs import normalize_slug


@dataclass(frozen=True, slots=True)
class SupportedItem:
    """One quest item a habit supports, with the ancestors above it (`path`)."""

    kind: QuestKind
    id: int
    title: str
    path: list[ItemRef]
    archived: bool
    created_at: datetime


@dataclass(frozen=True, slots=True)
class SupportingHabit:
    """A habit linked to a quest item or to an item under it (`linked_to`, `direct`)."""

    slug: str
    name: str
    check: HabitCheck
    archived: bool
    linked_to: ItemRef
    direct: bool


def list_habit_supports(session: Session, slug: str) -> list[SupportedItem]:
    """The quest items a habit supports, in tree order (ambitions first, tasks last)."""
    habit = require_habit(session, normalize_slug(slug))
    index = QuestIndex(session)
    links = session.exec(select(HabitSupport).where(HabitSupport.habit_id == habit.id)).all()
    items = [_supported_item(index, link) for link in links]
    order = list(SUPPORT_COLUMNS)
    return sorted(items, key=lambda item: (order.index(item.kind), item.title.lower(), item.id))


def add_habit_support(session: Session, slug: str, kind: QuestKind, item_id: int) -> SupportedItem:
    habit = require_habit(session, normalize_slug(slug))
    if habit.archived_at is not None:
        raise ValidationError(f"habit {habit.slug!r} is archived; restore it first")
    index = QuestIndex(session)
    row = index.row(kind, item_id)
    if row.archived_at is not None:
        raise ValidationError(f"{_label(kind)} {item_id} is archived and cannot be linked")
    if _find(session, habit, kind, item_id) is not None:
        raise ConflictError(f"habit {habit.slug!r} already supports {_label(kind)} {item_id}")
    link = HabitSupport(habit_id=habit.id, **{SUPPORT_COLUMNS[kind]: item_id})
    session.add(link)
    session.commit()
    session.refresh(link)
    return _supported_item(index, link)


def remove_habit_support(session: Session, slug: str, kind: QuestKind, item_id: int) -> None:
    habit = require_habit(session, normalize_slug(slug))
    link = _find(session, habit, kind, item_id)
    if link is None:
        raise NotFoundError("habit_support", f"{habit.slug}/{kind.value}/{item_id}")
    session.delete(link)
    session.commit()


def habits_supporting(session: Session, kind: QuestKind, item_id: int) -> list[SupportingHabit]:
    """Habits linked to this item (`direct`) or to any item under it, at any depth.

    A goal lists habits on the goal, its milestones, their chapters, and every task below. One
    row per link, so a habit linked at two levels appears twice, each with its `linked_to`.
    """
    index = QuestIndex(session)
    index.row(kind, item_id)
    keys = [(kind, item_id), *_descendants(index, kind, item_id)]
    habits = {habit.id: habit for habit in session.exec(select(Habit)).all()}
    today = resolve_today(None)
    rows: list[SupportingHabit] = []
    for key_kind, key_id in keys:
        column = getattr(HabitSupport, SUPPORT_COLUMNS[key_kind])
        for link in session.exec(select(HabitSupport).where(column == key_id)).all():
            habit = habits[link.habit_id]
            rows.append(
                SupportingHabit(
                    slug=habit.slug,
                    name=habit.name,
                    check=HabitCheck(rule_on(habit_rules(session, habit), today).check),
                    archived=habit.archived_at is not None,
                    linked_to=index.ref(key_kind, key_id),
                    direct=(key_kind, key_id) == (kind, item_id),
                )
            )
    return sorted(rows, key=lambda row: (not row.direct, row.name.lower(), row.linked_to.id))


def _supported_item(index: QuestIndex, link: HabitSupport) -> SupportedItem:
    kind, item_id = _target(link)
    row = index.row(kind, item_id)
    return SupportedItem(
        kind=kind,
        id=item_id,
        title=row.title,
        path=index.path(kind, row),
        archived=row.archived_at is not None,
        created_at=link.created_at,
    )


def _target(link: HabitSupport) -> Key:
    for kind, column in SUPPORT_COLUMNS.items():
        value = getattr(link, column)
        if value is not None:
            return kind, value
    raise ValueError(f"habit_support {link.id} points at no quest item")


def _find(session: Session, habit: Habit, kind: QuestKind, item_id: int) -> HabitSupport | None:
    column = getattr(HabitSupport, SUPPORT_COLUMNS[kind])
    return session.exec(
        select(HabitSupport).where(HabitSupport.habit_id == habit.id, column == item_id)
    ).first()


def _descendants(index: QuestIndex, kind: QuestKind, item_id: int) -> list[Key]:
    found: list[Key] = []
    for child in index.child_keys(kind, item_id):
        found.append(child)
        found.extend(_descendants(index, *child))
    return found


def _label(kind: QuestKind) -> str:
    return kind.value.replace("_", " ")
