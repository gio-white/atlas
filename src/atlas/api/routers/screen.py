from datetime import date

from fastapi import APIRouter

from atlas.api.deps import SessionDep
from atlas.api.schemas import (
    ScreenAppCreate,
    ScreenAppOut,
    ScreenAppUpdate,
    ScreenBudgetCreate,
    ScreenBudgetOut,
    ScreenBudgetUpdate,
    ScreenCategoryCreate,
    ScreenCategoryOut,
    ScreenCategoryUpdate,
    ScreenDashboardOut,
    ScreenDeviceCreate,
    ScreenDeviceOut,
    ScreenDeviceUpdate,
    ScreenSessionCreate,
    ScreenSessionRecordOut,
    ScreenSessionUpdate,
    ScreenViewOut,
)
from atlas.api.serialize import (
    screen_apps_out,
    screen_budget_out,
    screen_category_out,
    screen_device_out,
    screen_session_records_out,
)
from atlas.domain import Period, Source
from atlas.services import (
    create_screen_app,
    create_screen_budget,
    create_screen_category,
    create_screen_device,
    delete_screen_session,
    get_screen_app,
    get_screen_budget,
    get_screen_category,
    get_screen_device,
    get_screen_session,
    list_screen_apps,
    list_screen_budgets,
    list_screen_categories,
    list_screen_devices,
    list_screen_sessions,
    log_screen_session,
    screen_dashboard,
    screen_view,
    update_screen_app,
    update_screen_budget,
    update_screen_category,
    update_screen_device,
    update_screen_session,
)

router = APIRouter(prefix="/screen", tags=["screen"])


@router.get("/view", response_model=ScreenViewOut)
def get_screen_view(session: SessionDep, as_of: date | None = None) -> ScreenViewOut:
    return ScreenViewOut.model_validate(screen_view(session, as_of=as_of))


@router.get("/dashboard", response_model=ScreenDashboardOut)
def get_screen_dashboard(
    session: SessionDep,
    period: Period = Period.WEEK,
    as_of: date | None = None,
) -> ScreenDashboardOut:
    return ScreenDashboardOut.model_validate(screen_dashboard(session, as_of=as_of, period=period))


@router.get("/categories", response_model=list[ScreenCategoryOut])
def get_categories(
    session: SessionDep,
    include_archived: bool = False,
) -> list[ScreenCategoryOut]:
    return [
        screen_category_out(category)
        for category in list_screen_categories(session, include_archived=include_archived)
    ]


@router.post("/categories", response_model=ScreenCategoryOut, status_code=201)
def post_category(session: SessionDep, body: ScreenCategoryCreate) -> ScreenCategoryOut:
    category = create_screen_category(
        session,
        body.slug,
        judgment=body.judgment,
        name=body.name,
    )
    return screen_category_out(category)


@router.get("/categories/{slug}", response_model=ScreenCategoryOut)
def get_category_by_slug(session: SessionDep, slug: str) -> ScreenCategoryOut:
    return screen_category_out(get_screen_category(session, slug))


@router.patch("/categories/{slug}", response_model=ScreenCategoryOut)
def patch_category(
    session: SessionDep,
    slug: str,
    body: ScreenCategoryUpdate,
) -> ScreenCategoryOut:
    category = update_screen_category(session, slug, **body.model_dump(exclude_unset=True))
    return screen_category_out(category)


@router.get("/apps", response_model=list[ScreenAppOut])
def get_apps(session: SessionDep, include_archived: bool = False) -> list[ScreenAppOut]:
    return screen_apps_out(session, list_screen_apps(session, include_archived=include_archived))


@router.post("/apps", response_model=ScreenAppOut, status_code=201)
def post_app(session: SessionDep, body: ScreenAppCreate) -> ScreenAppOut:
    app = create_screen_app(session, body.slug, category_slug=body.category, name=body.name)
    return screen_apps_out(session, [app])[0]


@router.get("/apps/{slug}", response_model=ScreenAppOut)
def get_app_by_slug(session: SessionDep, slug: str) -> ScreenAppOut:
    return screen_apps_out(session, [get_screen_app(session, slug)])[0]


@router.patch("/apps/{slug}", response_model=ScreenAppOut)
def patch_app(session: SessionDep, slug: str, body: ScreenAppUpdate) -> ScreenAppOut:
    dumped = body.model_dump(exclude_unset=True)
    if "category" in dumped:
        dumped["category_slug"] = dumped.pop("category")
    app = update_screen_app(session, slug, **dumped)
    return screen_apps_out(session, [app])[0]


@router.get("/budgets", response_model=list[ScreenBudgetOut])
def get_budgets(session: SessionDep) -> list[ScreenBudgetOut]:
    return [screen_budget_out(budget) for budget in list_screen_budgets(session)]


@router.post("/budgets", response_model=ScreenBudgetOut, status_code=201)
def post_budget(session: SessionDep, body: ScreenBudgetCreate) -> ScreenBudgetOut:
    budget = create_screen_budget(
        session,
        body.slug,
        target_kind=body.target_kind,
        target_slug=body.target_slug,
        period=body.period,
        target_value=body.target_value,
        comparator=body.comparator,
        name=body.name,
        active_from=body.active_from,
        active_to=body.active_to,
    )
    return screen_budget_out(budget)


@router.get("/budgets/{slug}", response_model=ScreenBudgetOut)
def get_budget_by_slug(session: SessionDep, slug: str) -> ScreenBudgetOut:
    return screen_budget_out(get_screen_budget(session, slug))


@router.patch("/budgets/{slug}", response_model=ScreenBudgetOut)
def patch_budget(
    session: SessionDep,
    slug: str,
    body: ScreenBudgetUpdate,
) -> ScreenBudgetOut:
    budget = update_screen_budget(session, slug, **body.model_dump(exclude_unset=True))
    return screen_budget_out(budget)


@router.get("/devices", response_model=list[ScreenDeviceOut])
def get_devices(session: SessionDep, include_archived: bool = False) -> list[ScreenDeviceOut]:
    return [
        screen_device_out(device)
        for device in list_screen_devices(session, include_archived=include_archived)
    ]


@router.post("/devices", response_model=ScreenDeviceOut, status_code=201)
def post_device(session: SessionDep, body: ScreenDeviceCreate) -> ScreenDeviceOut:
    return screen_device_out(create_screen_device(session, body.slug, name=body.name))


@router.get("/devices/{slug}", response_model=ScreenDeviceOut)
def get_device_by_slug(session: SessionDep, slug: str) -> ScreenDeviceOut:
    return screen_device_out(get_screen_device(session, slug))


@router.patch("/devices/{slug}", response_model=ScreenDeviceOut)
def patch_device(
    session: SessionDep,
    slug: str,
    body: ScreenDeviceUpdate,
) -> ScreenDeviceOut:
    return screen_device_out(
        update_screen_device(session, slug, **body.model_dump(exclude_unset=True))
    )


@router.get("/sessions", response_model=list[ScreenSessionRecordOut])
def get_sessions(
    session: SessionDep,
    occurred_on: date | None = None,
) -> list[ScreenSessionRecordOut]:
    return screen_session_records_out(
        session,
        list_screen_sessions(session, occurred_on=occurred_on),
    )


@router.post("/sessions", response_model=ScreenSessionRecordOut, status_code=201)
def post_session(session: SessionDep, body: ScreenSessionCreate) -> ScreenSessionRecordOut:
    row = log_screen_session(
        session,
        body.app,
        minutes=body.minutes,
        started_at=body.started_at,
        ended_at=body.ended_at,
        occurred_on=body.occurred_on,
        device_slug=body.device,
        note=body.note,
        source=Source.API,
    )
    return screen_session_records_out(session, [row])[0]


@router.get("/sessions/{session_id}", response_model=ScreenSessionRecordOut)
def get_session_by_id(session: SessionDep, session_id: int) -> ScreenSessionRecordOut:
    return screen_session_records_out(session, [get_screen_session(session, session_id)])[0]


@router.patch("/sessions/{session_id}", response_model=ScreenSessionRecordOut)
def patch_session(
    session: SessionDep,
    session_id: int,
    body: ScreenSessionUpdate,
) -> ScreenSessionRecordOut:
    dumped = body.model_dump(exclude_unset=True)
    if "device" in dumped:
        dumped["device_slug"] = dumped.pop("device")
    row = update_screen_session(session, session_id, **dumped)
    return screen_session_records_out(session, [row])[0]


@router.delete("/sessions/{session_id}", status_code=204)
def remove_session(session: SessionDep, session_id: int) -> None:
    delete_screen_session(session, session_id)
