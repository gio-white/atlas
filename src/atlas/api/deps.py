from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlmodel import Session

from atlas.services import http_get_text
from atlas.services.entertainment_lookup import Fetch


def get_session(request: Request) -> Iterator[Session]:
    with request.app.state.session_factory() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def get_link_fetch() -> Fetch:
    return http_get_text


LinkFetchDep = Annotated[Fetch, Depends(get_link_fetch)]
