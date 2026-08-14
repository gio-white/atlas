from datetime import date
from typing import Annotated

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import Response

from atlas.api.deps import SessionDep
from atlas.api.schemas import (
    EntertainmentDashboardOut,
    EntertainmentTitleCreate,
    EntertainmentTitleOut,
    EntertainmentTitleUpdate,
    EntertainmentTopicCreate,
    EntertainmentTopicOut,
    EntertainmentTopicUpdate,
    EntertainmentViewOut,
)
from atlas.api.serialize import (
    entertainment_title_out_for,
    entertainment_topic_out,
)
from atlas.domain import EntertainmentKind, EntertainmentStatus, Period
from atlas.services import (
    clear_title_image,
    create_entertainment_title,
    create_entertainment_topic,
    entertainment_dashboard,
    entertainment_view,
    get_entertainment_title,
    get_entertainment_topic,
    get_title_image,
    list_entertainment_titles,
    list_entertainment_topics,
    set_title_image,
    update_entertainment_title,
    update_entertainment_topic,
)

router = APIRouter(prefix="/entertainment", tags=["entertainment"])


@router.get("/view", response_model=EntertainmentViewOut)
def get_entertainment_view(session: SessionDep, as_of: date | None = None) -> EntertainmentViewOut:
    return EntertainmentViewOut.model_validate(entertainment_view(session, as_of=as_of))


@router.get("/dashboard", response_model=EntertainmentDashboardOut)
def get_entertainment_dashboard(
    session: SessionDep,
    period: Period = Period.WEEK,
    as_of: date | None = None,
) -> EntertainmentDashboardOut:
    return EntertainmentDashboardOut.model_validate(
        entertainment_dashboard(session, as_of=as_of, period=period)
    )


@router.get("/topics", response_model=list[EntertainmentTopicOut])
def get_topics(
    session: SessionDep,
    include_archived: bool = False,
) -> list[EntertainmentTopicOut]:
    return [
        entertainment_topic_out(topic)
        for topic in list_entertainment_topics(session, include_archived=include_archived)
    ]


@router.post("/topics", response_model=EntertainmentTopicOut, status_code=201)
def post_topic(session: SessionDep, body: EntertainmentTopicCreate) -> EntertainmentTopicOut:
    topic = create_entertainment_topic(session, body.slug, name=body.name)
    return entertainment_topic_out(topic)


@router.get("/topics/{slug}", response_model=EntertainmentTopicOut)
def get_topic_by_slug(session: SessionDep, slug: str) -> EntertainmentTopicOut:
    return entertainment_topic_out(get_entertainment_topic(session, slug))


@router.patch("/topics/{slug}", response_model=EntertainmentTopicOut)
def patch_topic(
    session: SessionDep,
    slug: str,
    body: EntertainmentTopicUpdate,
) -> EntertainmentTopicOut:
    topic = update_entertainment_topic(session, slug, **body.model_dump(exclude_unset=True))
    return entertainment_topic_out(topic)


@router.get("/titles", response_model=list[EntertainmentTitleOut])
def get_titles(
    session: SessionDep,
    kind: EntertainmentKind | None = None,
    status: EntertainmentStatus | None = None,
    topic: str | None = None,
    include_archived: bool = False,
) -> list[EntertainmentTitleOut]:
    return [
        entertainment_title_out_for(session, title)
        for title in list_entertainment_titles(
            session,
            kind=kind,
            status=status,
            topic=topic,
            include_archived=include_archived,
        )
    ]


@router.post("/titles", response_model=EntertainmentTitleOut, status_code=201)
def post_title(session: SessionDep, body: EntertainmentTitleCreate) -> EntertainmentTitleOut:
    title = create_entertainment_title(
        session,
        body.slug,
        kind=body.kind,
        name=body.name,
        creator=body.creator,
        recommended_by=body.recommended_by,
        status=body.status,
        started_on=body.started_on,
        finished_on=body.finished_on,
        progress=body.progress,
        note=body.note,
        topics=body.topics,
        image_url=body.image_url,
    )
    return entertainment_title_out_for(session, title)


@router.get("/titles/{slug}", response_model=EntertainmentTitleOut)
def get_title_by_slug(session: SessionDep, slug: str) -> EntertainmentTitleOut:
    return entertainment_title_out_for(session, get_entertainment_title(session, slug))


@router.patch("/titles/{slug}", response_model=EntertainmentTitleOut)
def patch_title(
    session: SessionDep,
    slug: str,
    body: EntertainmentTitleUpdate,
) -> EntertainmentTitleOut:
    title = update_entertainment_title(session, slug, **body.model_dump(exclude_unset=True))
    return entertainment_title_out_for(session, title)


@router.put("/titles/{slug}/image", response_model=EntertainmentTitleOut)
async def put_title_image(
    session: SessionDep,
    slug: str,
    file: Annotated[UploadFile, File()],
) -> EntertainmentTitleOut:
    data = await file.read()
    title = set_title_image(
        session,
        slug,
        data,
        media_type=file.content_type,
        filename=file.filename,
    )
    return entertainment_title_out_for(session, title)


@router.delete("/titles/{slug}/image", response_model=EntertainmentTitleOut)
def delete_title_image(session: SessionDep, slug: str) -> EntertainmentTitleOut:
    return entertainment_title_out_for(session, clear_title_image(session, slug))


@router.get("/titles/{slug}/image")
def download_title_image(session: SessionDep, slug: str) -> Response:
    data, media_type = get_title_image(session, slug)
    return Response(content=data, media_type=media_type)
