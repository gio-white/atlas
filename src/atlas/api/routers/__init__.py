from atlas.api.routers.areas import router as areas_router
from atlas.api.routers.entries import router as entries_router
from atlas.api.routers.goals import router as goals_router
from atlas.api.routers.habits import router as habits_router
from atlas.api.routers.journal import router as journal_router
from atlas.api.routers.metrics import router as metrics_router
from atlas.api.routers.port import router as port_router
from atlas.api.routers.screen import router as screen_router
from atlas.api.routers.slips import router as slips_router
from atlas.api.routers.tasks import router as tasks_router
from atlas.api.routers.updates import router as updates_router
from atlas.api.routers.views import router as views_router

__all__ = [
    "areas_router",
    "entries_router",
    "goals_router",
    "habits_router",
    "journal_router",
    "metrics_router",
    "port_router",
    "screen_router",
    "slips_router",
    "tasks_router",
    "updates_router",
    "views_router",
]
