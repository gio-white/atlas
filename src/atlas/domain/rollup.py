from collections.abc import Sequence

from atlas.domain.enums import Aggregation
from atlas.domain.models import EntryView


def rollup(entries: Sequence[EntryView], aggregation: Aggregation) -> float | None:
    if not entries:
        return None
    if aggregation is Aggregation.LAST:
        latest = max(entries, key=lambda entry: entry.recency_key())
        return latest.numeric_value()
    values = [value for entry in entries if (value := entry.numeric_value()) is not None]
    if not values:
        return None
    if aggregation is Aggregation.SUM:
        return sum(values)
    if aggregation is Aggregation.MEAN:
        return sum(values) / len(values)
    if aggregation is Aggregation.MAX:
        return max(values)
    return min(values)
