from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, Query

from app.models.schemas import TraceEntry, SmsAlert
from app.db.repository import store
from app.agents.orchestrator import orchestrator

orch_router = APIRouter(tags=["orchestrate"])


def _filter(items: list, farm_id: Optional[str]) -> list:
    return [i for i in items if farm_id is None or i.farm_id == farm_id]


@orch_router.post("/orchestrate/{farm_id}")
@orch_router.post("/farms/{farm_id}/orchestrate")
def orchestrate(farm_id: str, use_llm: bool = True) -> dict[str, Any]:
    return orchestrator.run(farm_id, use_llm)


@orch_router.get("/trace", response_model=list[TraceEntry])
def get_trace(
    farm_id: Optional[str] = None,
    run_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
) -> list[TraceEntry]:
    items = [t for t in _filter(store.trace, farm_id) if run_id is None or t.run_id == run_id]
    return items[-limit:]


@orch_router.get("/alerts", response_model=list[SmsAlert])
def get_alerts(
    farm_id: Optional[str] = None, limit: int = Query(100, ge=1, le=1000)
) -> list[SmsAlert]:
    return list(reversed(_filter(store.alerts, farm_id)))[:limit]
