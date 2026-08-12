from typing import Any

from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.services import export_all, import_all

router = APIRouter(tags=["port"])


@router.get("/export")
def get_export(session: SessionDep) -> dict[str, Any]:
    return export_all(session)


@router.post("/import", status_code=204)
def post_import(
    session: SessionDep,
    payload: dict[str, Any],
    replace: bool = False,
) -> None:
    import_all(session, payload, replace=replace)
