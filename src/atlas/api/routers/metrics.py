from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.schemas import MetricCreate, MetricOut, MetricUpdate
from atlas.api.serialize import metrics_out
from atlas.services import archive_metric, create_metric, get_metric, list_metrics, update_metric

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("", response_model=list[MetricOut])
def get_metrics(
    session: SessionDep,
    area: str | None = None,
    include_archived: bool = False,
) -> list[MetricOut]:
    return metrics_out(
        session,
        list_metrics(session, area_slug=area, include_archived=include_archived),
    )


@router.post("", response_model=MetricOut, status_code=201)
def post_metric(session: SessionDep, body: MetricCreate) -> MetricOut:
    metric = create_metric(
        session,
        body.slug,
        area_slug=body.area,
        value_type=body.value_type,
        aggregation=body.aggregation,
        name=body.name,
        unit=body.unit,
        direction=body.direction,
    )
    return metrics_out(session, [metric])[0]


@router.get("/{slug}", response_model=MetricOut)
def get_metric_by_slug(session: SessionDep, slug: str) -> MetricOut:
    return metrics_out(session, [get_metric(session, slug)])[0]


@router.patch("/{slug}", response_model=MetricOut)
def patch_metric(session: SessionDep, slug: str, body: MetricUpdate) -> MetricOut:
    metric = update_metric(session, slug, **body.model_dump(exclude_unset=True))
    return metrics_out(session, [metric])[0]


@router.post("/{slug}/archive", response_model=MetricOut)
def post_archive_metric(session: SessionDep, slug: str) -> MetricOut:
    return metrics_out(session, [archive_metric(session, slug)])[0]
