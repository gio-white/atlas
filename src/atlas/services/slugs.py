import re

from atlas.services.errors import ValidationError

_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


def normalize_slug(slug: str) -> str:
    stripped = slug.strip().lower()
    if not _SLUG.fullmatch(stripped):
        raise ValidationError(f"invalid slug {slug!r}; use lowercase letters, digits, and hyphens")
    return stripped


def display_name(slug: str) -> str:
    return slug.replace("-", " ").title()
