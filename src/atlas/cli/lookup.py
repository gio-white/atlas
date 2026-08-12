import difflib

from sqlmodel import Session

from atlas.services import NotFoundError, ValidationError, list_metrics


def resolve_metric_slug(session: Session, query: str) -> str:
    slugs = [metric.slug for metric in list_metrics(session)]
    return resolve_slug(query, slugs, entity="metric")


def resolve_slug(query: str, slugs: list[str], *, entity: str) -> str:
    needle = query.strip().lower()
    if not needle:
        raise ValidationError(f"{entity} slug must not be empty")
    if needle in slugs:
        return needle
    prefixes = [slug for slug in slugs if slug.startswith(needle)]
    if len(prefixes) == 1:
        return prefixes[0]
    if len(prefixes) > 1:
        raise ValidationError(_ambiguous(entity, query, prefixes))
    substrings = [slug for slug in slugs if needle in slug]
    if len(substrings) == 1:
        return substrings[0]
    if len(substrings) > 1:
        raise ValidationError(_ambiguous(entity, query, substrings))
    close = difflib.get_close_matches(needle, slugs, n=5, cutoff=0.6)
    if len(close) == 1:
        return close[0]
    if len(close) > 1:
        raise ValidationError(_ambiguous(entity, query, close))
    raise NotFoundError(entity, query)


def _ambiguous(entity: str, query: str, matches: list[str]) -> str:
    listed = ", ".join(sorted(matches))
    return f"ambiguous {entity} {query!r}; matches {listed}"
