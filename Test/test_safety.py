from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from app.models.schemas import Action, Escalation, EscalationResolve, now
from app.db.repository import store
from app.services.notifier import (
    SafetyGateError,
    gate_ok,
    set_action_status,
    needs_expert,
)
from app.agents.executor import ExecutorAgent


def test_spray_direct_gating():
    store.reset()
    act = Action(
        id="act_s1",
        farm_id="f1",
        plot_id="p1",
        risk_id="r1",
        kind="spray",
        title="Spray",
        what="Spray chemical",
        when=now(),
        where="p1",
    )
    assert act.requires_expert_approval is True
    assert needs_expert(act) is True
    assert gate_ok(act, store) is False

    # Cannot set to notified
    with pytest.raises(SafetyGateError):
        set_action_status(act, "notified", store)

    # Cannot set to done
    with pytest.raises(SafetyGateError):
        set_action_status(act, "done", store)

    # Add approved escalation
    esc = Escalation(id="esc_1", farm_id="f1", action_id=act.id, reason="approval", status="approved")
    store.escalations[esc.id] = esc
    assert gate_ok(act, store) is True

    # Now passes
    set_action_status(act, "notified", store)
    assert act.status == "notified"
    set_action_status(act, "done", store)
    assert act.status == "done"


def test_non_spray_with_requires_expert_approval():
    store.reset()
    act = Action(
        id="act_custom",
        farm_id="f1",
        plot_id="p1",
        risk_id="r1",
        kind="scout",
        title="Scout",
        what="Scout",
        when=now(),
        where="p1",
        requires_expert_approval=True,
    )
    assert needs_expert(act) is True
    assert gate_ok(act, store) is False

    with pytest.raises(SafetyGateError):
        set_action_status(act, "done", store)


def test_api_task_gating_and_rejection(client: TestClient, auth_headers: dict[str, str], reset_store):
    # Create farm
    client.post("/farms", json={"id": "f_gate", "name": "Gated Farm", "phone": "+91", "budget_inr": 5000}, headers=auth_headers)
    
    # Ingest fungal conditions to trigger spray
    client.post("/ingest/weather", json={"farm_id": "f_gate", "humidity_pct": 85, "canopy_wet": True, "temp_c": 22}, headers=auth_headers)
    client.post("/ingest/drone", json={"farm_id": "f_gate", "ndvi": 0.50, "anomaly_score": 0.8}, headers=auth_headers)
    r = client.post("/orchestrate/f_gate", headers=auth_headers).json()

    spray_action = next(a for a in r["plan"]["actions"] if a["kind"] == "spray")
    assert spray_action["status"] == "awaiting_approval"
    assert len(r["escalations"]) == 1
    esc_id = r["escalations"][0]["id"]

    # No farmer SMS sent for spray
    alerts = client.get("/alerts?farm_id=f_gate", headers=auth_headers).json()
    assert not any(a.get("action_id") == spray_action["id"] for a in alerts)

    # Find task
    tasks = client.get("/tasks?farm_id=f_gate", headers=auth_headers).json()
    spray_task = next(t for t in tasks if t["kind"] == "spray")

    # PATCH task to done returns 409
    patch_res = client.patch(f"/tasks/{spray_task['id']}", json={"status": "done"}, headers=auth_headers)
    assert patch_res.status_code == 409

    # Rejection path
    client.post(f"/escalations/{esc_id}/resolve", json={"approved": False, "advice": "Too close to harvest"}, headers=auth_headers)
    
    # Action should now be skipped with expert_rejected
    esc_info = client.get(f"/escalations/{esc_id}", headers=auth_headers).json()
    assert esc_info["escalation"]["status"] == "rejected"
    assert esc_info["action"]["status"] == "skipped"
    assert esc_info["action"]["hold_reason"] == "expert_rejected"

    # Task should be removed or no longer runnable
    tasks_after = client.get("/tasks?farm_id=f_gate", headers=auth_headers).json()
    assert not any(t["id"] == spray_task["id"] for t in tasks_after)
