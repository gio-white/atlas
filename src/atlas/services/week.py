"""This week so far: four numbers for Home, each reusing its section's own calculation.

The week runs from the local Monday to the end of `as_of`. Nothing here is stored.
"""

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta

from sqlmodel import Session, col, select

from atlas.db.models import TimeBlock
from atlas.domain import Period
from atlas.domain.quests import as_utc, sessions_kept
from atlas.services.clock import resolve_today
from atlas.services.habits import pooled_adherence_counts
from atlas.services.quest_views import local_day_bounds
from atlas.services.quests import block_view
from atlas.services.screen import screen_dashboard
from atlas.services.sleep import sleep_view


@dataclass(frozen=True, slots=True)
class WeekSoFar:
    as_of: date
    week_start: date
    sessions_kept: int
    sessions_total: int
    habits_kept: int
    habits_judged: int
    habits_kept_share: float | None
    sleep_average_minutes: float | None
    sleep_nights: int
    screen_score: int | None


def week_so_far(
    session: Session, *, as_of: date | None = None, now: datetime | None = None
) -> WeekSoFar:
    as_of = resolve_today(as_of)
    monday = as_of - timedelta(days=as_of.weekday())
    week_start, _ = local_day_bounds(monday)
    _, day_end = local_day_bounds(as_of)
    # Looking back at a past day, "now" is the end of that day: later answers do not exist yet.
    now = min(as_utc(now) if now is not None else datetime.now(UTC), day_end)

    rows = session.exec(
        select(TimeBlock).where(
            col(TimeBlock.start_at) >= week_start.replace(tzinfo=None),
            col(TimeBlock.start_at) < day_end.replace(tzinfo=None),
        )
    ).all()
    kept = sessions_kept([block_view(row) for row in rows], week_start, day_end, now)

    satisfied, judged = pooled_adherence_counts(session, monday, as_of)
    sleep = sleep_view(session, as_of=as_of, days=(as_of - monday).days + 1)
    screen = screen_dashboard(session, as_of=as_of, period=Period.WEEK)
    return WeekSoFar(
        as_of=as_of,
        week_start=monday,
        sessions_kept=kept.kept,
        sessions_total=kept.total,
        habits_kept=satisfied,
        habits_judged=judged,
        habits_kept_share=None if judged == 0 else satisfied / judged,
        sleep_average_minutes=sleep.average_asleep,
        sleep_nights=sleep.nights_logged,
        screen_score=screen.score,
    )
