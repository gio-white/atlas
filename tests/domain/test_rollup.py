from datetime import UTC, date, datetime

from atlas.domain import Aggregation, EntryView, rollup


def test_empty_bucket_rolls_up_to_none():
    assert rollup([], Aggregation.SUM) is None
    assert rollup([], Aggregation.LAST) is None


def test_sum_mean_max_min():
    entries = [
        EntryView(occurred_on=date(2026, 8, 13), value_num=10),
        EntryView(occurred_on=date(2026, 8, 13), value_num=30),
        EntryView(occurred_on=date(2026, 8, 13), value_num=20),
    ]

    assert rollup(entries, Aggregation.SUM) == 60
    assert rollup(entries, Aggregation.MEAN) == 20
    assert rollup(entries, Aggregation.MAX) == 30
    assert rollup(entries, Aggregation.MIN) == 10


def test_bool_values_count_as_one_and_zero():
    entries = [
        EntryView(occurred_on=date(2026, 8, 13), value_bool=True),
        EntryView(occurred_on=date(2026, 8, 13), value_bool=False),
        EntryView(occurred_on=date(2026, 8, 13), value_bool=True),
    ]

    assert rollup(entries, Aggregation.SUM) == 2.0


def test_text_only_entries_do_not_produce_a_numeric_rollup():
    entries = [EntryView(occurred_on=date(2026, 8, 13), value_text="felt good")]

    assert rollup(entries, Aggregation.SUM) is None


def test_last_uses_occurred_at_then_created_at_then_id():
    day = date(2026, 8, 13)
    early = datetime(2026, 8, 13, 8, 0, tzinfo=UTC)
    late = datetime(2026, 8, 13, 18, 0, tzinfo=UTC)
    entries = [
        EntryView(occurred_on=day, value_num=70, occurred_at=late, id=1),
        EntryView(occurred_on=day, value_num=78, occurred_at=early, id=2),
        EntryView(occurred_on=day, value_num=80, created_at=late, id=3),
    ]

    assert rollup(entries, Aggregation.LAST) == 70


def test_last_falls_back_to_id_when_timestamps_are_missing():
    day = date(2026, 8, 13)
    entries = [
        EntryView(occurred_on=day, value_num=1, id=1),
        EntryView(occurred_on=day, value_num=2, id=3),
        EntryView(occurred_on=day, value_num=9, id=2),
    ]

    assert rollup(entries, Aggregation.LAST) == 2
