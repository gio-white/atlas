from datetime import date

import pytest

from atlas.cli.parse import parse_iso_date
from atlas.services import ValidationError


def test_parse_iso_date():
    assert parse_iso_date("2026-08-10") == date(2026, 8, 10)
    assert parse_iso_date(None) is None
    with pytest.raises(ValidationError, match="YYYY-MM-DD"):
        parse_iso_date("13/08/2026")
