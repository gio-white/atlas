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
    ScreenViewOut,
)
from atlas.api.serialize import (
    screen_apps_out,
    screen_budget_out,
    screen_category_out,
)
from atlas.services import (
    create_screen_app,
    create_screen_budget,
    create_screen_category,
    get_screen_app,
    get_screen_budget,
    get_screen_category,
    list_screen_apps,
    list_screen_budgets,
    list_screen_categories,
    screen_view,
    update_screen_app,
    update_screen_budget,
    update_screen_category,
)

router = APIRouter(prefix="/screen", tags=["screen"])


@router.get("/view", response_model=ScreenViewOut)
def get_screen_view(session: SessionDep, as_of: date | None = None) -> ScreenViewOut:
    return ScreenViewOut.model_validate(screen_view(session, as_of=as_of))


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
