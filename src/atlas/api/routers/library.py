from datetime import date
from typing import Annotated

from fastapi import APIRouter, File, UploadFile
from fastapi.responses import Response

from atlas.api.deps import LinkFetchDep, SessionDep
from atlas.api.schemas import (
    LibraryDashboardOut,
    LibraryLinkLookupIn,
    LibraryLinkSuggestionOut,
    LibraryTitleCreate,
    LibraryTitleFromLink,
    LibraryTitleOut,
    LibraryTitleUpdate,
    LibraryTopicCreate,
    LibraryTopicOut,
    LibraryTopicUpdate,
)
from atlas.api.serialize import (
    library_title_out_for,
    library_topic_out,
)
from atlas.domain import LibraryKind, LibraryStatus, Period
from atlas.services import (
    clear_title_image,
    create_library_title,
    create_library_topic,
    create_title_from_link,
    delete_library_title,
    get_library_title,
    get_library_topic,
    get_title_image,
    library_dashboard,
    list_library_titles,
    list_library_topics,
    lookup_link,
    set_title_image,
    update_library_title,
    update_library_topic,
)

router = APIRouter(prefix="/library", tags=["library"])


@router.get("/dashboard", response_model=LibraryDashboardOut)
def get_library_dashboard(
    session: SessionDep,
    period: Period = Period.WEEK,
    as_of: date | None = None,
) -> LibraryDashboardOut:
    return LibraryDashboardOut.model_validate(
        library_dashboard(session, as_of=as_of, period=period)
    )


@router.get("/topics", response_model=list[LibraryTopicOut])
def get_topics(
    session: SessionDep,
    include_archived: bool = False,
) -> list[LibraryTopicOut]:
    return [
        library_topic_out(topic)
        for topic in list_library_topics(session, include_archived=include_archived)
    ]


@router.post("/topics", response_model=LibraryTopicOut, status_code=201)
def post_topic(session: SessionDep, body: LibraryTopicCreate) -> LibraryTopicOut:
    topic = create_library_topic(session, body.slug, name=body.name)
    return library_topic_out(topic)


@router.get("/topics/{slug}", response_model=LibraryTopicOut)
def get_topic_by_slug(session: SessionDep, slug: str) -> LibraryTopicOut:
    return library_topic_out(get_library_topic(session, slug))


@router.patch("/topics/{slug}", response_model=LibraryTopicOut)
def patch_topic(
    session: SessionDep,
    slug: str,
    body: LibraryTopicUpdate,
) -> LibraryTopicOut:
    topic = update_library_topic(session, slug, **body.model_dump(exclude_unset=True))
    return library_topic_out(topic)


@router.get("/titles", response_model=list[LibraryTitleOut])
def get_titles(
    session: SessionDep,
    kind: LibraryKind | None = None,
    status: LibraryStatus | None = None,
    topic: str | None = None,
    include_archived: bool = False,
) -> list[LibraryTitleOut]:
    return [
        library_title_out_for(session, title)
        for title in list_library_titles(
            session,
            kind=kind,
            status=status,
            topic=topic,
            include_archived=include_archived,
        )
    ]


@router.post("/titles", response_model=LibraryTitleOut, status_code=201)
def post_title(session: SessionDep, body: LibraryTitleCreate) -> LibraryTitleOut:
    title = create_library_title(
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
        rating=body.rating,
        link=body.link,
        topics=body.topics,
        image_url=body.image_url,
    )
    return library_title_out_for(session, title)


@router.post("/lookup", response_model=LibraryLinkSuggestionOut)
def post_lookup(
    session: SessionDep,
    fetch: LinkFetchDep,
    body: LibraryLinkLookupIn,
) -> LibraryLinkSuggestionOut:
    result = lookup_link(session, body.url, fetch=fetch)
    suggestion = result.suggestion
    return LibraryLinkSuggestionOut(
        link=suggestion.link,
        name=suggestion.name,
        kind=suggestion.kind,
        creator=suggestion.creator,
        image_url=suggestion.image_url,
        existing=result.existing,
    )


@router.post("/titles/from-link", response_model=LibraryTitleOut, status_code=201)
def post_title_from_link(
    session: SessionDep,
    fetch: LinkFetchDep,
    body: LibraryTitleFromLink,
) -> LibraryTitleOut:
    title = create_title_from_link(
        session,
        body.url,
        kind=body.kind,
        status=body.status,
        topics=body.topics,
        note=body.note,
        fetch=fetch,
    )
    return library_title_out_for(session, title)


@router.get("/titles/{slug}", response_model=LibraryTitleOut)
def get_title_by_slug(session: SessionDep, slug: str) -> LibraryTitleOut:
    return library_title_out_for(session, get_library_title(session, slug))


@router.patch("/titles/{slug}", response_model=LibraryTitleOut)
def patch_title(
    session: SessionDep,
    slug: str,
    body: LibraryTitleUpdate,
) -> LibraryTitleOut:
    title = update_library_title(session, slug, **body.model_dump(exclude_unset=True))
    return library_title_out_for(session, title)


@router.delete("/titles/{slug}", status_code=204)
def delete_title(session: SessionDep, slug: str) -> None:
    delete_library_title(session, slug)


@router.put("/titles/{slug}/image", response_model=LibraryTitleOut)
async def put_title_image(
    session: SessionDep,
    slug: str,
    file: Annotated[UploadFile, File()],
) -> LibraryTitleOut:
    data = await file.read()
    title = set_title_image(
        session,
        slug,
        data,
        media_type=file.content_type,
        filename=file.filename,
    )
    return library_title_out_for(session, title)


@router.delete("/titles/{slug}/image", response_model=LibraryTitleOut)
def delete_title_image(session: SessionDep, slug: str) -> LibraryTitleOut:
    return library_title_out_for(session, clear_title_image(session, slug))


@router.get("/titles/{slug}/image")
def download_title_image(session: SessionDep, slug: str) -> Response:
    data, media_type = get_title_image(session, slug)
    return Response(content=data, media_type=media_type)
