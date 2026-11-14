"""Export and import of the quest tables (schema 11).

Quest rows have no slug, so the export carries their integer ids and parent ids as references
local to the file. Import inserts fresh rows and remaps every reference, which makes a merge
import safe next to existing quests and keeps a replace import identical in shape.
"""

from datetime import UTC, date, datetime
from typing import Any

from sqlmodel import Session, select

from atlas.db.models import Ambition, Chapter, Goal, Milestone, SideQuest, Task, TimeBlock
from atlas.domain import (
    QuestStatus,
    TaskPriority,
    TaskStatus,
    TimeBlockProvider,
    TimeBlockStatus,
)
from atlas.services.errors import ValidationError

QUEST_SECTIONS = (
    "ambitions",
    "goals",
    "milestones",
    "side_quests",
    "chapters",
    "tasks",
    "time_blocks",
)

# Sections of exports before schema 11 that held the replaced goal/milestone/task model.
LEGACY_SECTIONS = ("goals", "milestones", "tasks")

_TASK_PARENTS = (
    ("ambition_id", "ambitions"),
    ("goal_id", "goals"),
    ("milestone_id", "milestones"),
    ("chapter_id", "chapters"),
    ("side_quest_id", "side_quests"),
)


def export_quests(session: Session) -> dict[str, list[dict[str, Any]]]:
    def rows(model: Any) -> list[Any]:
        return list(session.exec(select(model).order_by(model.id)).all())

    return {
        "ambitions": [
            {**_container(row), "target_on": _iso_date(row.target_on), "weight": row.weight}
            for row in rows(Ambition)
        ],
        "goals": [
            {
                **_container(row),
                "ambition_id": row.ambition_id,
                "success_description": row.success_description,
                "due_on": _iso_date(row.due_on),
                "weight": row.weight,
            }
            for row in rows(Goal)
        ],
        "milestones": [
            {
                **_container(row),
                "goal_id": row.goal_id,
                "due_on": _iso_date(row.due_on),
                "weight": row.weight,
            }
            for row in rows(Milestone)
        ],
        "side_quests": [
            {**_container(row), "due_on": _iso_date(row.due_on)} for row in rows(SideQuest)
        ],
        "chapters": [
            {
                "id": row.id,
                "milestone_id": row.milestone_id,
                "side_quest_id": row.side_quest_id,
                "title": row.title,
                "description": row.description,
                "weight": row.weight,
                "position": row.position,
                "archived_at": _iso_dt(row.archived_at),
                "created_at": _iso_dt(row.created_at),
                "updated_at": _iso_dt(row.updated_at),
            }
            for row in rows(Chapter)
        ],
        "tasks": [_export_task(row) for row in rows(Task)],
        "time_blocks": [
            {
                "id": row.id,
                "task_id": row.task_id,
                "start_at": _iso_dt(row.start_at),
                "end_at": _iso_dt(row.end_at),
                "status": str(row.status),
                "provider": str(row.provider),
                "external_event_id": row.external_event_id,
                "created_at": _iso_dt(row.created_at),
                "updated_at": _iso_dt(row.updated_at),
            }
            for row in rows(TimeBlock)
        ],
    }


def import_quests(session: Session, payload: dict[str, Any]) -> dict[str, dict[int, int]]:
    """Insert the quest sections; returns each section's file id → new row id."""
    ids: dict[str, dict[int, int]] = {section: {} for section in QUEST_SECTIONS}

    def insert(section: str, raw: dict[str, Any], row: Any) -> None:
        session.add(row)
        session.flush()
        ids[section][int(_require(raw, "id"))] = row.id

    def ref(section: str, raw: dict[str, Any], key: str) -> int | None:
        value = raw.get(key)
        if value is None:
            return None
        try:
            return ids[section][int(value)]
        except KeyError as exc:
            raise ValidationError(f"import {key} {value!r} is not in {section}") from exc

    for raw in payload.get("ambitions", []):
        insert(
            "ambitions",
            raw,
            Ambition(
                **_container_fields(raw),
                target_on=_parse_date(raw.get("target_on")),
                weight=raw.get("weight"),
            ),
        )
    for raw in payload.get("goals", []):
        insert(
            "goals",
            raw,
            Goal(
                **_container_fields(raw),
                ambition_id=ref("ambitions", raw, "ambition_id"),
                success_description=raw.get("success_description"),
                due_on=_parse_date(raw.get("due_on")),
                weight=raw.get("weight"),
            ),
        )
    for raw in payload.get("milestones", []):
        insert(
            "milestones",
            raw,
            Milestone(
                **_container_fields(raw),
                goal_id=ref("goals", raw, "goal_id"),
                due_on=_parse_date(raw.get("due_on")),
                weight=raw.get("weight"),
            ),
        )
    for raw in payload.get("side_quests", []):
        insert(
            "side_quests",
            raw,
            SideQuest(**_container_fields(raw), due_on=_parse_date(raw.get("due_on"))),
        )
    for raw in payload.get("chapters", []):
        insert(
            "chapters",
            raw,
            Chapter(
                milestone_id=ref("milestones", raw, "milestone_id"),
                side_quest_id=ref("side_quests", raw, "side_quest_id"),
                title=_require(raw, "title"),
                description=raw.get("description"),
                weight=raw.get("weight"),
                position=int(raw.get("position") or 0),
                **_bookkeeping(raw),
            ),
        )
    for raw in payload.get("tasks", []):
        parents = {column: ref(section, raw, column) for column, section in _TASK_PARENTS}
        insert(
            "tasks",
            raw,
            Task(
                title=_require(raw, "title"),
                description=raw.get("description"),
                status=TaskStatus(raw.get("status") or TaskStatus.TODO),
                priority=TaskPriority(raw.get("priority") or TaskPriority.NORMAL),
                estimate_minutes=raw.get("estimate_minutes"),
                due_on=_parse_date(raw.get("due_on")),
                weight=raw.get("weight"),
                position=int(raw.get("position") or 0),
                organized_at=_parse_datetime(raw.get("organized_at")),
                started_at=_parse_datetime(raw.get("started_at")),
                completed_at=_parse_datetime(raw.get("completed_at")),
                **parents,
                **_bookkeeping(raw),
            ),
        )
    for raw in payload.get("time_blocks", []):
        insert(
            "time_blocks",
            raw,
            TimeBlock(
                task_id=ref("tasks", raw, "task_id"),
                start_at=_parse_datetime(_require(raw, "start_at")),
                end_at=_parse_datetime(_require(raw, "end_at")),
                status=TimeBlockStatus(raw.get("status") or TimeBlockStatus.SCHEDULED),
                provider=TimeBlockProvider(raw.get("provider") or TimeBlockProvider.INTERNAL),
                external_event_id=raw.get("external_event_id"),
                created_at=_parse_datetime(raw.get("created_at")) or datetime.now(UTC),
                updated_at=_parse_datetime(raw.get("updated_at")) or datetime.now(UTC),
            ),
        )
    return ids


def clear_quests(session: Session) -> None:
    for model in (TimeBlock, Task, Chapter, Milestone, Goal, SideQuest, Ambition):
        for row in session.exec(select(model)).all():
            session.delete(row)
        session.flush()


def _container(row: Any) -> dict[str, Any]:
    return {
        "id": row.id,
        "title": row.title,
        "description": row.description,
        "position": row.position,
        "status": str(row.status),
        "completed_at": _iso_dt(row.completed_at),
        "archived_at": _iso_dt(row.archived_at),
        "created_at": _iso_dt(row.created_at),
        "updated_at": _iso_dt(row.updated_at),
    }


def _container_fields(raw: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": _require(raw, "title"),
        "description": raw.get("description"),
        "position": int(raw.get("position") or 0),
        "status": QuestStatus(raw.get("status") or QuestStatus.ACTIVE),
        "completed_at": _parse_datetime(raw.get("completed_at")),
        **_bookkeeping(raw),
    }


def _bookkeeping(raw: dict[str, Any]) -> dict[str, Any]:
    now = datetime.now(UTC)
    return {
        "archived_at": _parse_datetime(raw.get("archived_at")),
        "created_at": _parse_datetime(raw.get("created_at")) or now,
        "updated_at": _parse_datetime(raw.get("updated_at")) or now,
    }


def _export_task(row: Task) -> dict[str, Any]:
    return {
        "id": row.id,
        "title": row.title,
        "description": row.description,
        "status": str(row.status),
        "priority": str(row.priority),
        "estimate_minutes": row.estimate_minutes,
        "due_on": _iso_date(row.due_on),
        "weight": row.weight,
        "position": row.position,
        "ambition_id": row.ambition_id,
        "goal_id": row.goal_id,
        "milestone_id": row.milestone_id,
        "chapter_id": row.chapter_id,
        "side_quest_id": row.side_quest_id,
        "organized_at": _iso_dt(row.organized_at),
        "started_at": _iso_dt(row.started_at),
        "completed_at": _iso_dt(row.completed_at),
        "archived_at": _iso_dt(row.archived_at),
        "created_at": _iso_dt(row.created_at),
        "updated_at": _iso_dt(row.updated_at),
    }


def _require(raw: dict[str, Any], key: str) -> Any:
    if key not in raw or raw[key] is None or raw[key] == "":
        raise ValidationError(f"import is missing required field {key!r}")
    return raw[key]


def _iso_date(value: date | None) -> str | None:
    return value.isoformat() if value is not None else None


def _iso_dt(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()


def _parse_date(raw: str | date | None) -> date | None:
    if raw is None or raw == "":
        return None
    if isinstance(raw, date):
        return raw
    return date.fromisoformat(str(raw))


def _parse_datetime(raw: str | datetime | None) -> datetime | None:
    if raw is None or raw == "":
        return None
    value = raw if isinstance(raw, datetime) else datetime.fromisoformat(str(raw))
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
