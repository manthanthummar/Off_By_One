from __future__ import annotations

import asyncio
import hmac
import logging
from contextlib import asynccontextmanager
from typing import Any, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.models.schemas import now
from app.db.repository import store
from app.services.mqtt import mqtt_service
from app.agents.orchestrator import orchestrator
from app.api.routers import (
    farms_router,
    ingest_router,
    orch_router,
    tasks_router,
    esc_router,
    insights_router,
    demo_router,
)

log = logging.getLogger("farmsense")
logging.basicConfig(level=settings.log_level)


def require_api_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    if not x_api_key or not hmac.compare_digest(x_api_key, settings.api_key):
        raise HTTPException(401, "Invalid or missing X-API-Key")


async def auto_orchestrate_loop(interval: int) -> None:
    """Periodically orchestrates farms with fresh MQTT ingest data."""
    log.info("Starting background MQTT auto-orchestrator loop (interval=%ds)", interval)
    try:
        while True:
            await asyncio.sleep(interval)
            fresh_farms = mqtt_service.get_and_clear_fresh_farms()
            for farm_id in fresh_farms:
                try:
                    log.info("Background auto-orchestrating farm: %s", farm_id)
                    orchestrator.run(farm_id, use_llm=False)
                except Exception as exc:
                    log.warning("Auto-orchestration failed for farm %s: %s", farm_id, exc)
    except asyncio.CancelledError:
        log.info("Background auto-orchestrator loop cancelled")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    store.ensure_db()
    mqtt_service.start()
    bg_task = None
    if settings.auto_orchestrate_interval > 0:
        bg_task = asyncio.create_task(
            auto_orchestrate_loop(settings.auto_orchestrate_interval)
        )
    yield
    if bg_task:
        bg_task.cancel()
        try:
            await bg_task
        except asyncio.CancelledError:
            pass
    mqtt_service.stop()


app = FastAPI(
    title="FarmSense API",
    version="1.0.0",
    description="Autonomous multi-agent farm advisory & action orchestration.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["meta"])
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "llm": bool(settings.anthropic_key),
        "mqtt": bool(settings.mqtt_host),
        "ts": now(),
    }


for router in (
    farms_router,
    ingest_router,
    orch_router,
    tasks_router,
    esc_router,
    insights_router,
    demo_router,
):
    app.include_router(router, dependencies=[Depends(require_api_key)])
