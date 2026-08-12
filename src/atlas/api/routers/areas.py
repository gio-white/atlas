from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.schemas import AreaCreate, AreaOut
from atlas.services import create_area, list_areas

router = APIRouter(prefix="/areas", tags=["areas"])


@router.get("", response_model=list[AreaOut])
def get_areas(session: SessionDep, include_archived: bool = False) -> list[AreaOut]:
    areas = list_areas(session, include_archived=include_archived)
    return [AreaOut.model_validate(area) for area in areas]


@router.post("", response_model=AreaOut, status_code=201)
def post_area(session: SessionDep, body: AreaCreate) -> AreaOut:
    area = create_area(session, body.slug, name=body.name, description=body.description)
    return AreaOut.model_validate(area)
