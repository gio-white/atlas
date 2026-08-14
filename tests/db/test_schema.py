from datetime import date

import pytest
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from atlas.db import (
    CURRENT_SCHEMA_VERSION,
    Area,
    Entry,
    Goal,
    Habit,
    Metric,
    Milestone,
    SchemaVersion,
    ScreenApp,
    ScreenBudget,
    ScreenCategory,
    create_memory_engine,
    init_db,
    init_schema,
    make_session_factory,
)
from atlas.domain import (
    Aggregation,
    Comparator,
    Direction,
    GoalKind,
    GoalStatus,
    Measure,
    Period,
    ScreenJudgment,
    Source,
    ValueType,
)


@pytest.fixture
def engine():
    memory = create_memory_engine()
    init_schema(memory)
    return memory


@pytest.fixture
def session(engine):
    factory = make_session_factory(engine)
    with factory() as db_session:
        yield db_session


def _area(session: Session, slug: str = "health") -> Area:
    area = Area(slug=slug, name=slug.title())
    session.add(area)
    session.commit()
    session.refresh(area)
    return area


def _metric(session: Session, area: Area, slug: str = "pushups") -> Metric:
    metric = Metric(
        area_id=area.id,
        slug=slug,
        name=slug.title(),
        value_type=ValueType.COUNT,
        aggregation=Aggregation.SUM,
        direction=Direction.HIGHER_IS_BETTER,
    )
    session.add(metric)
    session.commit()
    session.refresh(metric)
    return metric


def test_init_schema_records_version(engine):
    with Session(engine) as session:
        row = session.get(SchemaVersion, 1)
        assert row is not None
        assert row.version == CURRENT_SCHEMA_VERSION


def test_init_schema_is_idempotent(engine):
    init_schema(engine)
    with Session(engine) as session:
        rows = session.exec(select(SchemaVersion)).all()
        assert len(rows) == 1
        assert rows[0].version == CURRENT_SCHEMA_VERSION


def test_init_db_creates_parent_directory_and_file(tmp_path):
    db_path = tmp_path / "nested" / "atlas.db"
    engine = init_db(db_path)

    assert db_path.exists()
    with Session(engine) as session:
        assert session.get(SchemaVersion, 1) is not None


def test_entry_is_indexed_on_metric_and_occurred_on(engine):
    indexes = inspect(engine).get_indexes("entry")
    column_sets = {tuple(index["column_names"]) for index in indexes}

    assert ("metric_id", "occurred_on") in column_sets


@pytest.mark.parametrize("model", [Area, Metric, Habit, Goal])
def test_slug_is_unique(session, model):
    area = _area(session)
    metric = _metric(session, area)
    first = _row_for(model, slug="dup", area=area, metric=metric)
    session.add(first)
    session.commit()
    session.add(_row_for(model, slug="dup", area=area, metric=metric))

    with pytest.raises(IntegrityError):
        session.commit()


def test_screen_slugs_are_unique(session):
    category = ScreenCategory(
        slug="entertainment",
        name="Entertainment",
        judgment=ScreenJudgment.WASTE,
    )
    session.add(category)
    session.commit()
    session.add(ScreenCategory(slug="entertainment", name="Other", judgment=ScreenJudgment.NEUTRAL))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    area = _area(session, slug="screen")
    metric = _metric(session, area, slug="instagram")
    session.add(
        ScreenApp(
            slug="instagram",
            name="Instagram",
            category_id=category.id,
            metric_id=metric.id,
        )
    )
    session.commit()
    session.add(
        ScreenApp(
            slug="instagram",
            name="Again",
            category_id=category.id,
            metric_id=metric.id,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    session.add(
        ScreenBudget(
            slug="waste-cap",
            name="Waste cap",
            target_kind="judgment",
            target_slug="waste",
            period=Period.DAY,
            target_value=90.0,
            comparator=Comparator.AT_MOST,
            active_from=date(2026, 8, 1),
        )
    )
    session.commit()
    session.add(
        ScreenBudget(
            slug="waste-cap",
            name="Again",
            target_kind="judgment",
            target_slug="waste",
            period=Period.DAY,
            target_value=60.0,
            comparator=Comparator.AT_MOST,
            active_from=date(2026, 8, 1),
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_multiple_entries_per_day_are_allowed(session):
    metric = _metric(session, _area(session))
    day = date(2026, 8, 13)
    session.add(
        Entry(metric_id=metric.id, occurred_on=day, value_num=10, source=Source.CLI)
    )
    session.add(
        Entry(metric_id=metric.id, occurred_on=day, value_num=20, source=Source.API)
    )
    session.commit()

    rows = session.exec(select(Entry).where(Entry.metric_id == metric.id)).all()
    assert len(rows) == 2


def test_foreign_key_rejects_unknown_area(session):
    session.add(
        Metric(
            area_id=999,
            slug="orphan",
            name="Orphan",
            value_type=ValueType.COUNT,
            aggregation=Aggregation.SUM,
            direction=Direction.NEUTRAL,
        )
    )
    with pytest.raises(IntegrityError):
        session.commit()


def test_habit_weekdays_round_trip_as_json(session):
    metric = _metric(session, _area(session))
    habit = Habit(
        metric_id=metric.id,
        slug="weekday-runs",
        name="Weekday runs",
        period=Period.DAY,
        target_value=1.0,
        comparator=Comparator.AT_LEAST,
        weekdays=[1, 2, 3, 4, 5],
        active_from=date(2026, 8, 1),
    )
    session.add(habit)
    session.commit()
    session.refresh(habit)

    assert habit.weekdays == [1, 2, 3, 4, 5]


def test_goal_and_milestone_persist(session):
    area = _area(session)
    metric = _metric(session, area, slug="weight")
    goal = Goal(
        area_id=area.id,
        slug="bodyweight-75",
        name="Bodyweight 75kg",
        kind=GoalKind.METRIC_TARGET,
        metric_id=metric.id,
        target_value=75.0,
        comparator=Comparator.AT_MOST,
        measure=Measure.LATEST_VALUE,
        start_on=date(2026, 1, 1),
        due_on=date(2026, 12, 1),
        status=GoalStatus.ACTIVE,
    )
    session.add(goal)
    session.commit()
    session.refresh(goal)
    session.add(Milestone(goal_id=goal.id, name="Hit 78kg"))
    session.commit()

    stored = session.exec(select(Milestone).where(Milestone.goal_id == goal.id)).one()
    assert stored.name == "Hit 78kg"
    assert stored.done_at is None


def _row_for(model, *, slug: str, area: Area, metric: Metric):
    if model is Area:
        return Area(slug=slug, name=slug)
    if model is Metric:
        return Metric(
            area_id=area.id,
            slug=slug,
            name=slug,
            value_type=ValueType.BOOL,
            aggregation=Aggregation.SUM,
            direction=Direction.NEUTRAL,
        )
    if model is Habit:
        return Habit(
            metric_id=metric.id,
            slug=slug,
            name=slug,
            period=Period.DAY,
            target_value=1.0,
            comparator=Comparator.AT_LEAST,
            active_from=date(2026, 8, 1),
        )
    return Goal(
        area_id=area.id,
        slug=slug,
        name=slug,
        kind=GoalKind.MILESTONE,
        start_on=date(2026, 1, 1),
        due_on=date(2026, 12, 31),
    )
