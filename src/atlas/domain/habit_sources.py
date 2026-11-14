"""The sources a data habit can read (habits brief §2).

One entry per source. Adding a source later (workouts, steps, mindful minutes) means adding a
member to `HabitSource`, an entry here, and a reader in the service layer that returns the
day's value and whether the day's data is complete. Nothing else changes.
"""

from dataclasses import dataclass
from enum import StrEnum

from atlas.domain.enums import HabitSource, HabitThreshold


class SourceMeasure(StrEnum):
    """What a source's value is: minutes in a day, or a time of day (minutes after midnight)."""

    MINUTES = "minutes"
    TIME_OF_DAY = "time_of_day"


class SourceFeed(StrEnum):
    """Which fact store a source reads. Completeness rules are per feed (brief §3)."""

    SLEEP = "sleep"
    SCREEN = "screen"
    SESSIONS = "sessions"


class SourceRef(StrEnum):
    """What a source needs you to pick: a screen category or a screen app."""

    CATEGORY = "category"
    APP = "app"


DURATION_THRESHOLDS = (HabitThreshold.AT_LEAST, HabitThreshold.AT_MOST)
TIME_THRESHOLDS = (HabitThreshold.BEFORE, HabitThreshold.AFTER)

# Bedtime is compared on an evening-to-morning scale, 18:00 to 17:59, so 00:40 is later than
# 23:30 (brief §2). A time on this scale is minutes after 18:00.
EVENING_SCALE_START = 18 * 60


@dataclass(frozen=True, slots=True)
class SourceSpec:
    source: HabitSource
    label: str
    """The name in the source picker."""
    subject: str
    """The start of the readable rule line, e.g. "Wake time" in "Wake time before 07:00"."""
    feed: SourceFeed
    measure: SourceMeasure
    thresholds: tuple[HabitThreshold, ...]
    default_threshold: HabitThreshold
    default_value: float
    ref: SourceRef | None = None
    evening_scale: bool = False


SOURCES: dict[HabitSource, SourceSpec] = {
    spec.source: spec
    for spec in (
        SourceSpec(
            HabitSource.WAKE_TIME,
            label="Wake time",
            subject="Wake time",
            feed=SourceFeed.SLEEP,
            measure=SourceMeasure.TIME_OF_DAY,
            thresholds=TIME_THRESHOLDS,
            default_threshold=HabitThreshold.BEFORE,
            default_value=7 * 60,
        ),
        SourceSpec(
            HabitSource.BEDTIME,
            label="Bedtime",
            subject="Bedtime",
            feed=SourceFeed.SLEEP,
            measure=SourceMeasure.TIME_OF_DAY,
            thresholds=TIME_THRESHOLDS,
            default_threshold=HabitThreshold.BEFORE,
            default_value=23 * 60,
            evening_scale=True,
        ),
        SourceSpec(
            HabitSource.TIME_ASLEEP,
            label="Time asleep",
            subject="Time asleep",
            feed=SourceFeed.SLEEP,
            measure=SourceMeasure.MINUTES,
            thresholds=DURATION_THRESHOLDS,
            default_threshold=HabitThreshold.AT_LEAST,
            default_value=7 * 60,
        ),
        SourceSpec(
            HabitSource.SCREEN_BAD_APPS,
            label="Screen time in Bad apps",
            subject="Bad apps",
            feed=SourceFeed.SCREEN,
            measure=SourceMeasure.MINUTES,
            thresholds=DURATION_THRESHOLDS,
            default_threshold=HabitThreshold.AT_MOST,
            default_value=90,
        ),
        SourceSpec(
            HabitSource.SCREEN_CATEGORY,
            label="Screen time in a category",
            subject="Screen time in",
            feed=SourceFeed.SCREEN,
            measure=SourceMeasure.MINUTES,
            thresholds=DURATION_THRESHOLDS,
            default_threshold=HabitThreshold.AT_MOST,
            default_value=60,
            ref=SourceRef.CATEGORY,
        ),
        SourceSpec(
            HabitSource.SCREEN_APP,
            label="Screen time in an app",
            subject="Screen time in",
            feed=SourceFeed.SCREEN,
            measure=SourceMeasure.MINUTES,
            thresholds=DURATION_THRESHOLDS,
            default_threshold=HabitThreshold.AT_MOST,
            default_value=30,
            ref=SourceRef.APP,
        ),
        SourceSpec(
            HabitSource.SCREEN_TOTAL,
            label="Screen time, total",
            subject="Screen time",
            feed=SourceFeed.SCREEN,
            measure=SourceMeasure.MINUTES,
            thresholds=DURATION_THRESHOLDS,
            default_threshold=HabitThreshold.AT_MOST,
            default_value=3 * 60,
        ),
        SourceSpec(
            HabitSource.SESSIONS_PLANNED,
            label="Sessions planned",
            subject="A session planned",
            feed=SourceFeed.SESSIONS,
            measure=SourceMeasure.TIME_OF_DAY,
            thresholds=(HabitThreshold.BEFORE,),
            default_threshold=HabitThreshold.BEFORE,
            default_value=12 * 60,
        ),
    )
}


def source_spec(source: HabitSource) -> SourceSpec:
    return SOURCES[HabitSource(source)]
