from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.schemas import AreaCreate, AreaOut, AreaUpdate
from atlas.services import archive_area, create_area, get_area, list_areas, update_area

router = APIRouter(prefix="/areas", tags=["areas"])


@router.get("", response_model=list[AreaOut])
def get_areas(session: SessionDep, include_archived: bool = False) -> list[AreaOut]:
    areas = list_areas(session, include_archived=include_archived)
    return [AreaOut.model_validate(area) for area in areas]


@router.post("", response_model=AreaOut, status_code=201)
def post_area(session: SessionDep, body: AreaCreate) -> AreaOut:
    area = create_area(session, body.slug, name=body.name, description=body.description)
    return AreaOut.model_validate(area)


@router.get("/{slug}", response_model=AreaOut)
def get_area_by_slug(session: SessionDep, slug: str) -> AreaOut:
    return AreaOut.model_validate(get_area(session, slug))


@router.patch("/{slug}", response_model=AreaOut)
def patch_area(session: SessionDep, slug: str, body: AreaUpdate) -> AreaOut:
    area = update_area(session, slug, **body.model_dump(exclude_unset=True))
    return AreaOut.model_validate(area)


@router.post("/{slug}/archive", response_model=AreaOut)
def post_archive_area(session: SessionDep, slug: str) -> AreaOut:
    return AreaOut.model_validate(archive_area(session, slug))
