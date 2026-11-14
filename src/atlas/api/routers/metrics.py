from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.schemas import MetricCreate, MetricOut, MetricUpdate
from atlas.api.serialize import metric_out
from atlas.services import archive_metric, create_metric, get_metric, list_metrics, update_metric

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("", response_model=list[MetricOut])
def get_metrics(session: SessionDep, include_archived: bool = False) -> list[MetricOut]:
    return [
        metric_out(metric) for metric in list_metrics(session, include_archived=include_archived)
    ]


@router.post("", response_model=MetricOut, status_code=201)
def post_metric(session: SessionDep, body: MetricCreate) -> MetricOut:
    metric = create_metric(
        session,
        body.slug,
        value_type=body.value_type,
        aggregation=body.aggregation,
        name=body.name,
        unit=body.unit,
        direction=body.direction,
    )
    return metric_out(metric)


@router.get("/{slug}", response_model=MetricOut)
def get_metric_by_slug(session: SessionDep, slug: str) -> MetricOut:
    return metric_out(get_metric(session, slug))


@router.patch("/{slug}", response_model=MetricOut)
def patch_metric(session: SessionDep, slug: str, body: MetricUpdate) -> MetricOut:
    return metric_out(update_metric(session, slug, **body.model_dump(exclude_unset=True)))


@router.post("/{slug}/archive", response_model=MetricOut)
def post_archive_metric(session: SessionDep, slug: str) -> MetricOut:
    return metric_out(archive_metric(session, slug))
