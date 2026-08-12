import pytest

from atlas.cli.lookup import resolve_slug
from atlas.services import NotFoundError, ValidationError


def test_exact_match_is_case_insensitive():
    assert resolve_slug("Pushups", ["pushups", "weight"], entity="metric") == "pushups"


def test_unique_prefix_matches():
    assert resolve_slug("push", ["pushups", "weight"], entity="metric") == "pushups"


def test_unique_substring_matches():
    assert resolve_slug("sit", ["pushups", "sit-ups"], entity="metric") == "sit-ups"


def test_close_typo_matches():
    assert resolve_slug("pusups", ["pushups", "weight"], entity="metric") == "pushups"


def test_ambiguous_prefix_lists_candidates():
    with pytest.raises(ValidationError, match="ambiguous") as exc:
        resolve_slug("p", ["pushups", "protein"], entity="metric")
    assert "protein" in str(exc.value)
    assert "pushups" in str(exc.value)


def test_unknown_slug_is_not_found():
    with pytest.raises(NotFoundError, match="metric"):
        resolve_slug("nope", ["pushups"], entity="metric")
