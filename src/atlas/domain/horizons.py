from datetime import date

from atlas.domain.enums import GoalHorizon, PaceStatus

LONG_WINDOW_DAYS = 365
MEDIUM_WINDOW_DAYS = 28

COLUMN_ON_TRACK_PACES = frozenset({PaceStatus.ON_TRACK, PaceStatus.AHEAD, PaceStatus.ACHIEVED})


def infer_horizon(start_on: date, due_on: date) -> GoalHorizon:
    days = (due_on - start_on).days
    if days >= LONG_WINDOW_DAYS:
        return GoalHorizon.LONG
    if days >= MEDIUM_WINDOW_DAYS:
        return GoalHorizon.MEDIUM
    return GoalHorizon.SHORT


def required_parent_horizon(horizon: GoalHorizon) -> GoalHorizon | None:
    if horizon is GoalHorizon.LONG:
        return None
    if horizon is GoalHorizon.MEDIUM:
        return GoalHorizon.LONG
    return GoalHorizon.MEDIUM


def parent_horizon_is_valid(child: GoalHorizon, parent: GoalHorizon | None) -> bool:
    required = required_parent_horizon(child)
    if required is None:
        return parent is None
    if parent is None:
        return True
    return parent is required


def is_column_on_track(pace: PaceStatus) -> bool:
    return pace in COLUMN_ON_TRACK_PACES
