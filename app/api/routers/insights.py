from __future__ import annotations

from typing import Any
from fastapi import APIRouter

from app.config import settings
from app.db.repository import store
from app.agents.orchestrator import orchestrator

insights_router = APIRouter(prefix="/insights", tags=["insights"])


@insights_router.get("/stats")
def stats() -> dict[str, Any]:
    store.refresh_overdue()
    return {
        "farms": len(store.farms),
        "open_risks": sum(r.status == "open" for r in store.risks.values()),
        "critical_risks": sum(
            r.status == "open" and r.severity == "critical" for r in store.risks.values()
        ),
        "plans": len(store.plans),
        "tasks": len(store.tasks),
        "tasks_done": sum(t.status == "done" for t in store.tasks.values()),
        "pending_escalations": sum(
            e.status == "pending" for e in store.escalations.values()
        ),
        "sms_sent": len(store.alerts),
        "llm_enabled": bool(settings.anthropic_key),
        "mqtt_enabled": bool(settings.mqtt_host),
    }


@insights_router.get("/{farm_id}")
def farm_insight(farm_id: str, use_llm: bool = True) -> dict[str, Any]:
    farm = store.farm(farm_id)
    risks = [
        r for r in store.risks.values() if r.farm_id == farm_id and r.status == "open"
    ]
    actions = store.farm_actions(farm_id)
    if use_llm:
        text, source, _ = orchestrator.advisor.advise(farm, risks, actions)
    else:
        text, source = orchestrator.advisor.template(farm, risks, actions), "offline"
    return {
        "farm_id": farm_id,
        "advice": text,
        "source": source,
        "open_risks": len(risks),
    }
