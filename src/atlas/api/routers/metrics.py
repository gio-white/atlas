from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.schemas import MetricCreate, MetricOut
from atlas.api.serialize import metrics_out
from atlas.services import create_metric, list_metrics

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
