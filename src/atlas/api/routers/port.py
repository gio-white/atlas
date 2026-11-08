from typing import Any

from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.schemas import ImportSummaryOut
from atlas.services import export_all, import_all

router = APIRouter(tags=["port"])


@router.get("/export")
def get_export(session: SessionDep) -> dict[str, Any]:
    return export_all(session)


@router.post("/import", response_model=ImportSummaryOut)
def post_import(
    session: SessionDep,
    payload: dict[str, Any],
    replace: bool = False,
) -> ImportSummaryOut:
    summary = import_all(session, payload, replace=replace)
    return ImportSummaryOut(
        schema_version=summary.schema_version,
        ignored_sections=list(summary.ignored_sections),
        notes=summary.notes,
    )
