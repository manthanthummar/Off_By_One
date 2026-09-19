from app.api.routers.farms import farms_router
from app.api.routers.ingest import ingest_router
from app.api.routers.orchestrate import orch_router
from app.api.routers.tasks import tasks_router
from app.api.routers.escalations import esc_router
from app.api.routers.insights import insights_router
from app.api.routers.demo import demo_router

__all__ = [
    "farms_router",
    "ingest_router",
    "orch_router",
    "tasks_router",
    "esc_router",
    "insights_router",
    "demo_router",
]
