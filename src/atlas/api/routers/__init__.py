from atlas.api.routers.entertainment import router as entertainment_router
from atlas.api.routers.entries import router as entries_router
from atlas.api.routers.habits import router as habits_router
from atlas.api.routers.journal import router as journal_router
from atlas.api.routers.metrics import router as metrics_router
from atlas.api.routers.port import router as port_router
from atlas.api.routers.quest_views import router as quest_views_router
from atlas.api.routers.quests import router as quests_router
from atlas.api.routers.screen import router as screen_router
from atlas.api.routers.sleep import router as sleep_router
from atlas.api.routers.time_blocks import router as time_blocks_router
from atlas.api.routers.views import router as views_router

__all__ = [
    "entries_router",
    "entertainment_router",
    "habits_router",
    "journal_router",
    "metrics_router",
    "port_router",
    "quest_views_router",
    "quests_router",
    "screen_router",
    "sleep_router",
    "time_blocks_router",
    "views_router",
]
