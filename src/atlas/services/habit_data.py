"""What data habits read: one reading per day from sleep, screen time, or sessions (habits
brief §2, §3). Read only: nothing here writes to any other part of Atlas.

`HabitData.load` reads every feed once for a range of days; `HabitData.reading` then answers
one rule and day. Adding a source later means a `HabitSource` member, its entry in
`habit_sources.SOURCES`, and a branch here.
"""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta, tzinfo

from sqlmodel import Session, col, select

from atlas.db.models import ScreenDevice, TimeBlock
from atlas.domain import ScreenJudgment, SleepNight, TimeBlockStatus
from atlas.domain.enums import HabitSource
from atlas.domain.habit_sources import SourceFeed, source_spec
from atlas.domain.habits import MINUTES_IN_DAY, NO_READING, Reading, RuleSpec
from atlas.domain.quests import as_utc
from atlas.domain.screen import attributed_day_minutes
from atlas.services.screen import screen_session_views
from atlas.services.sleep import sleep_nights
from atlas.settings import load_settings


@dataclass(slots=True)
class ScreenDay:
    """A day's screen minutes by what a rule can ask for."""

    total: float = 0.0
    bad: float = 0.0
    categories: dict[str, float] = field(default_factory=dict)
    apps: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class HabitData:
    """Every feed's facts for `start`–`end`, ready to answer `reading(rule, day)`."""

    start: date
    end: date
    timezone: tzinfo
    nights: dict[date, SleepNight]
    screen: dict[date, ScreenDay]
    complete_through: tuple[datetime, ...]
    """Each active device's "complete up to" time; a device that never reported is not there."""
    devices: int
    """Active devices. Screen time is complete for a day only when every one covers it."""
    planned: dict[date, float]
    """The earliest a session on that day was created, in minutes after its local midnight
    (negative when created on an earlier day)."""

    @classmethod
    def load(cls, session: Session, start: date, end: date) -> "HabitData":
        timezone = load_settings().timezone
        devices = session.exec(
            select(ScreenDevice).where(col(ScreenDevice.archived_at).is_(None))
        ).all()
        return cls(
            start=start,
            end=end,
            timezone=timezone,
            nights=sleep_nights(session, start, end),
            screen=_screen_days(session, start, end, timezone),
            complete_through=tuple(
                as_utc(device.complete_through)
                for device in devices
                if device.complete_through is not None
            ),
            devices=len(devices),
            planned=_planned(session, start, end, timezone),
        )

    def reading(self, rule: RuleSpec, day: date) -> Reading:
        if rule.source is None:
            return NO_READING
        source = HabitSource(rule.source)
        match source_spec(source).feed:
            case SourceFeed.SLEEP:
                return self._sleep(source, day)
            case SourceFeed.SCREEN:
                return self._screen(source, rule.source_ref, day)
            case SourceFeed.SESSIONS:
                return Reading(self.planned.get(day), complete=True, received=True)

    def _sleep(self, source: HabitSource, day: date) -> Reading:
        """A night belongs to the day you wake up (brief §2); once it arrives it is final."""
        night = self.nights.get(day)
        if night is None:
            return NO_READING
        match source:
            case HabitSource.WAKE_TIME:
                value = night.wake_offset % MINUTES_IN_DAY
            case HabitSource.BEDTIME:
                value = night.bed_offset % MINUTES_IN_DAY
            case _:
                value = night.asleep_minutes
        return Reading(value, complete=True, received=True)

    def _screen(self, source: HabitSource, ref: str | None, day: date) -> Reading:
        """All devices together. A day is complete only when every active device has sent data
        covering the whole day; with no active device it never is (brief §3)."""
        totals = self.screen.get(day)
        day_start, day_end = _bounds(day, self.timezone)
        complete = self.devices > 0 and len(self.complete_through) == self.devices
        complete = complete and all(moment >= day_end for moment in self.complete_through)
        received = totals is not None or any(m > day_start for m in self.complete_through)
        if not received:
            return NO_READING
        totals = totals or ScreenDay()
        match source:
            case HabitSource.SCREEN_BAD_APPS:
                value = totals.bad
            case HabitSource.SCREEN_CATEGORY:
                value = totals.categories.get(ref or "", 0.0)
            case HabitSource.SCREEN_APP:
                value = totals.apps.get(ref or "", 0.0)
            case _:
                value = totals.total
        return Reading(value, complete=complete, received=True)


def _screen_days(
    session: Session, start: date, end: date, timezone: tzinfo
) -> dict[date, ScreenDay]:
    days: dict[date, ScreenDay] = defaultdict(ScreenDay)
    for view in screen_session_views(session):
        for day, minutes in attributed_day_minutes(view, timezone).items():
            if not start <= day <= end:
                continue
            totals = days[day]
            totals.total += minutes
            if view.judgment is ScreenJudgment.WASTE:
                totals.bad += minutes
            totals.categories[view.category_slug] = (
                totals.categories.get(view.category_slug, 0.0) + minutes
            )
            totals.apps[view.app_slug] = totals.apps.get(view.app_slug, 0.0) + minutes
    return dict(days)


def _planned(session: Session, start: date, end: date, timezone: tzinfo) -> dict[date, float]:
    """Sessions planned: any session on the day, created at any time; cancelled ones do not
    count, done and "didn't happen" ones do (habits plan, assumptions)."""
    first, _ = _bounds(start, timezone)
    _, last = _bounds(end, timezone)
    blocks = session.exec(
        select(TimeBlock).where(
            col(TimeBlock.start_at) >= first.replace(tzinfo=None),
            col(TimeBlock.start_at) < last.replace(tzinfo=None),
            TimeBlock.status != TimeBlockStatus.CANCELLED,
        )
    ).all()
    earliest: dict[date, float] = {}
    for block in blocks:
        day = as_utc(block.start_at).astimezone(timezone).date()
        midnight, _ = _bounds(day, timezone)
        minute = (as_utc(block.created_at) - midnight).total_seconds() / 60
        earliest[day] = min(earliest.get(day, minute), minute)
    return earliest


def _bounds(day: date, timezone: tzinfo) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min, tzinfo=timezone)
    end = datetime.combine(day + timedelta(days=1), time.min, tzinfo=timezone)
    return start.astimezone(UTC), end.astimezone(UTC)
