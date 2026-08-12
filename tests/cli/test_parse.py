from datetime import date

import pytest

from atlas.cli.parse import (
    comparator_and_target,
    parse_iso_date,
    parse_log_value,
    parse_weekdays,
    slugify,
)
from atlas.domain import Comparator
from atlas.services import ValidationError


def test_parse_iso_date():
    assert parse_iso_date("2026-08-10") == date(2026, 8, 10)
    assert parse_iso_date(None) is None
    with pytest.raises(ValidationError, match="YYYY-MM-DD"):
        parse_iso_date("13/08/2026")


def test_parse_log_value_accepts_numbers_bools_and_text():
    assert parse_log_value(None) is None
    assert parse_log_value("40") == 40.0
    assert parse_log_value("78.4") == 78.4
    assert parse_log_value("true") is True
    assert parse_log_value("no") is False
    assert parse_log_value("felt good") == "felt good"


def test_slugify_turns_a_name_into_a_slug():
    assert slugify("Bodyweight 75kg") == "bodyweight-75kg"


def test_parse_weekdays_accepts_names_and_numbers():
    assert parse_weekdays("mon,tue,wed,thu,fri") == [1, 2, 3, 4, 5]
    assert parse_weekdays("1,7") == [1, 7]


def test_comparator_and_target_requires_exactly_one_flag():
    assert comparator_and_target(3, None, None) == (Comparator.AT_LEAST, 3)
    with pytest.raises(ValidationError, match="exactly one"):
        comparator_and_target(3, 1, None)
    with pytest.raises(ValidationError, match="exactly one"):
        comparator_and_target(None, None, None)
