import pytest

from atlas.services import (
    AlreadyExistsError,
    NotFoundError,
    ValidationError,
    archive_area,
    create_area,
    list_areas,
)


def test_create_area_uses_slug_as_name_by_default(session):
    area = create_area(session, "health")

    assert area.id is not None
    assert area.slug == "health"
    assert area.name == "Health"
    assert area.archived_at is None


def test_create_area_normalizes_slug_case(session):
    area = create_area(session, "Health")

    assert area.slug == "health"


def test_duplicate_slug_is_rejected(session):
    create_area(session, "health")

    with pytest.raises(AlreadyExistsError, match="health"):
        create_area(session, "health")


def test_invalid_slug_is_rejected(session):
    with pytest.raises(ValidationError, match="invalid slug"):
        create_area(session, "Health_1")


def test_list_areas_hides_archived(session):
    create_area(session, "health")
    create_area(session, "career")
    archive_area(session, "career")

    assert [area.slug for area in list_areas(session)] == ["health"]
    assert [area.slug for area in list_areas(session, include_archived=True)] == [
        "career",
        "health",
    ]


def test_archive_unknown_area(session):
    with pytest.raises(NotFoundError, match="area"):
        archive_area(session, "missing")


def test_archive_is_not_idempotent(session):
    create_area(session, "health")
    archive_area(session, "health")

    with pytest.raises(ValidationError, match="already archived"):
        archive_area(session, "health")
