from __future__ import annotations

from typing import Any, Optional
from fastapi import APIRouter, HTTPException

from app.models.schemas import Escalation, EscalationResolve
from app.db.repository import store
from app.agents.orchestrator import orchestrator

esc_router = APIRouter(tags=["escalations"])


def _filter(items: list, farm_id: Optional[str]) -> list:
    return [i for i in items if farm_id is None or i.farm_id == farm_id]


@esc_router.get("/escalations", response_model=list[Escalation])
def list_escalations(
    farm_id: Optional[str] = None, status: Optional[str] = None
) -> list[Escalation]:
    items = _filter(list(store.escalations.values()), farm_id)
    return [e for e in items if status is None or e.status == status]


@esc_router.get("/escalations/{esc_id}")
def get_escalation(esc_id: str) -> dict[str, Any]:
    esc = store.escalations.get(esc_id)
    if not esc:
        raise HTTPException(404, "Escalation not found")
    return {"escalation": esc, "action": store.actions.get(esc.action_id)}


@esc_router.post("/escalations/{esc_id}/resolve", response_model=Escalation)
def resolve_escalation(esc_id: str, body: EscalationResolve) -> Escalation:
    with store.lock:
        esc = store.escalations.get(esc_id)
        if not esc:
            raise HTTPException(404, "Escalation not found")
        resolved = orchestrator.executor.resolve_escalation(esc, body, store)
        store.persist_all()
        return resolved
