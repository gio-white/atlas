"""Synthetic quest data for `atlas seed`, in the version 11 export shape.

It exercises every structure in brief Part 4: an ambition with goals and direct tasks, an
ambition with nothing under it, an independent goal, a milestone with chapters and direct tasks,
an empty chapter, a side quest with chapters and tasks, standalone tasks, Inbox items, a goal
completed by hand with open items, and time blocks yesterday, today, and tomorrow (one left
unconfirmed, one cancelled). Dates are relative to `as_of`; block times are local in `zone`.
"""

from datetime import UTC, date, datetime, time, timedelta, tzinfo
from typing import Any


class _Builder:
    def __init__(self, as_of: date, zone: tzinfo) -> None:
        self.as_of = as_of
        self.zone = zone
        self.data: dict[str, list[dict[str, Any]]] = {
            "ambitions": [],
            "goals": [],
            "milestones": [],
            "side_quests": [],
            "chapters": [],
            "tasks": [],
            "time_blocks": [],
        }
        self.created = self.at(-14, 9, 0)

    def at(self, days: int, hour: int, minute: int = 0) -> str:
        local = datetime.combine(self.as_of + timedelta(days=days), time(hour, minute), self.zone)
        return local.astimezone(UTC).isoformat()

    def day(self, days: int) -> str:
        return (self.as_of + timedelta(days=days)).isoformat()

    def _add(self, section: str, row: dict[str, Any]) -> int:
        rows = self.data[section]
        row_id = len(rows) + 1
        position = sum(
            1
            for other in rows
            if all(other.get(key) == row.get(key) for key in _PARENT_KEYS if key in row)
        )
        rows.append(
            {
                "id": row_id,
                "description": None,
                "position": position,
                "archived_at": None,
                "created_at": self.created,
                "updated_at": self.created,
                **row,
            }
        )
        return row_id

    def container(self, section: str, title: str, **fields: Any) -> int:
        completed_at = fields.pop("completed_at", None)
        return self._add(
            section,
            {
                "title": title,
                "status": "completed" if completed_at else "active",
                "completed_at": completed_at,
                **fields,
            },
        )

    def chapter(self, title: str, **fields: Any) -> int:
        return self._add("chapters", {"title": title, **fields})

    def task(
        self,
        title: str,
        status: str = "todo",
        *,
        organized: bool = True,
        **fields: Any,
    ) -> int:
        started = self.at(-7, 18) if status != "todo" else None
        return self._add(
            "tasks",
            {
                "title": title,
                "status": status,
                "priority": fields.pop("priority", "normal"),
                "organized_at": self.at(-13, 9) if organized else None,
                "started_at": started,
                "completed_at": self.at(-3, 17) if status == "completed" else None,
                **fields,
            },
        )

    def block(
        self,
        task_id: int,
        days: int,
        start: tuple[int, int],
        minutes: int,
        status: str,
        *,
        planned: tuple[int, int, int] | None = None,
    ):
        """`planned` is when the session was put in the calendar: (day offset, hour, minute)."""
        start_at = self.at(days, *start)
        end_at = (datetime.fromisoformat(start_at) + timedelta(minutes=minutes)).isoformat()
        self._add(
            "time_blocks",
            {
                "task_id": task_id,
                "start_at": start_at,
                "end_at": end_at,
                "status": status,
                "provider": "internal",
                "external_event_id": None,
                **({"created_at": self.at(*planned)} if planned else {}),
            },
        )


_PARENT_KEYS = (
    "ambition_id",
    "goal_id",
    "milestone_id",
    "chapter_id",
    "side_quest_id",
    "organized_at",
)


def demo_quests(as_of: date, zone: tzinfo) -> dict[str, list[dict[str, Any]]]:
    q = _Builder(as_of, zone)

    engineer = q.container("ambitions", "Become a better software engineer", target_on=None)
    calmer = q.container("ambitions", "Live a calmer life")

    job = q.container(
        "goals",
        "Land a data engineering job in Copenhagen",
        ambition_id=engineer,
        success_description="Signed an offer and moved by summer",
        due_on=q.day(200),
        weight=2.0,
    )
    rust = q.container(
        "milestones", "Get comfortable with Rust", goal_id=job, due_on=q.day(45), weight=2.0
    )
    basics = q.chapter("Rust fundamentals", milestone_id=rust)
    q.chapter("Async Rust", milestone_id=rust)
    q.task("Understand ownership and borrowing", "completed", chapter_id=basics)
    csv = q.task(
        "Write a CLI that parses CSV files",
        "in_progress",
        chapter_id=basics,
        estimate_minutes=180,
        priority="high",
    )
    q.task("Learn error handling with Result", chapter_id=basics, estimate_minutes=90)
    q.task("Pick a Rust book", "completed", milestone_id=rust)
    apply = q.container("milestones", "Apply to five companies", goal_id=job, due_on=q.day(90))
    cv = q.task("Update my CV", milestone_id=apply, priority="high", due_on=q.day(3))
    q.task("Write a cover letter template", milestone_id=apply, estimate_minutes=60)
    q.task("Ask Sam about the Copenhagen job market", goal_id=job)

    open_source = q.container("goals", "Contribute to an open-source project", ambition_id=engineer)
    q.task("Find a project with good first issues", "completed", goal_id=open_source)
    q.task("Open a first pull request", goal_id=open_source)

    book = q.task("Read Designing Data-Intensive Applications", "in_progress", ambition_id=engineer)
    q.task("Set up a weekly learning review", ambition_id=engineer)

    marathon = q.container("goals", "Run a half marathon", due_on=q.day(90))
    ten_k = q.container("milestones", "Run 10 km without stopping", goal_id=marathon)
    q.task("Buy running shoes", "completed", milestone_id=ten_k)
    plan = q.task("Follow a six-week running plan", "in_progress", milestone_id=ten_k)
    q.task("Register for the race", goal_id=marathon, due_on=q.day(14))

    flat = q.container("goals", "Furnish the new flat", completed_at=q.at(-2, 19))
    q.task("Buy a sofa", "completed", goal_id=flat)
    q.task("Hang the pictures", goal_id=flat)

    taxes = q.container("side_quests", "Tax declaration", due_on=q.day(30))
    documents = q.chapter("Collect documents", side_quest_id=taxes)
    q.task("Download payslips", "completed", chapter_id=documents)
    q.task("Find donation receipts", chapter_id=documents)
    q.task("Submit the declaration", side_quest_id=taxes, due_on=q.day(30))
    trip = q.container("side_quests", "Plan the summer trip")
    dates = q.task("Choose dates with friends", side_quest_id=trip)

    q.task("Renew passport", due_on=q.day(0), priority="high")
    q.task("Fix the bike light", "completed")

    for title in ("Look into climbing gyms", "Idea: write about learning Rust", "Call the dentist"):
        q.task(title, organized=False)

    # Past weekday sessions for the "Plan the day" habit: most planned that morning or the
    # evening before, every third one only after noon, so the habit misses on those days.
    for days in range(-13, -1):
        if (as_of + timedelta(days=days)).isoweekday() > 5:
            continue
        planned = (days, 13, 30) if days % 3 == 0 else (days, 7, 45)
        q.block(csv, days, (16, 0), 60, "completed", planned=planned)
    q.block(csv, -1, (16, 0), 90, "completed")
    q.block(book, -1, (20, 0), 60, "scheduled")
    q.block(dates, -1, (12, 0), 30, "cancelled")
    q.block(csv, 0, (9, 0), 90, "completed")
    q.block(cv, 0, (14, 0), 60, "scheduled")
    q.block(plan, 0, (18, 0), 45, "scheduled")
    q.block(csv, 1, (9, 30), 90, "scheduled")
    q.block(cv, 1, (11, 30), 30, "scheduled")

    # Habits that support quest items, at several levels (informational only).
    q.data["habit_supports"] = [
        {"habit": "meditated-daily", "kind": "ambition", "id": calmer},
        {"habit": "runs-weekly", "kind": "goal", "id": marathon},
        {"habit": "runs-weekly", "kind": "milestone", "id": ten_k},
        {"habit": "deep-work-weekdays", "kind": "chapter", "id": basics},
        {"habit": "deep-work-weekdays", "kind": "task", "id": book},
    ]
    return q.data
