from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
import main
from simulator.simulate import run_simulation


@pytest.fixture
def sim_client():
    return TestClient(main.app, base_url="http://testserver")


def test_simulator_drought(sim_client, auth_headers):
    # Reset store
    sim_client.post("/demo/reset", headers=auth_headers)

    res = run_simulation(
        scenario="drought",
        farm_id="sim-drought",
        api_url="http://testserver",
        rest_only=True,
        client=sim_client,
    )

    # 1. Critical water stress
    assert any(r["kind"] == "water_stress" and r["severity"] == "critical" for r in res["risks"])
    
    # 2. Urgent irrigation task
    assert len(res["tasks"]) == 1
    assert res["tasks"][0]["kind"] == "irrigate"
    
    # 3. SMS alert <= 160 chars
    assert len(res["alerts"]) >= 1
    assert all(len(a["message"]) <= 160 for a in res["alerts"])


def test_simulator_fungal(sim_client, auth_headers):
    sim_client.post("/demo/reset", headers=auth_headers)

    res = run_simulation(
        scenario="fungal",
        farm_id="sim-fungal",
        api_url="http://testserver",
        rest_only=True,
        client=sim_client,
    )

    # 1. Critical fungal disease
    assert any(r["kind"] == "fungal_disease" and r["severity"] == "critical" for r in res["risks"])

    # 2. Actions contain scout and spray
    actions = {a["kind"]: a for a in res["plan"]["actions"]}
    assert "scout" in actions
    assert "spray" in actions
    assert actions["spray"]["status"] == "awaiting_approval"
    assert actions["spray"]["requires_expert_approval"] is True

    # 3. Escalation created
    assert len(res["escalations"]) == 1
    assert res["escalations"][0]["status"] == "pending"

    # 4. No farmer SMS for spray before approval
    spray_id = actions["spray"]["id"]
    assert not any(a.get("action_id") == spray_id for a in res["alerts"])


def test_simulator_nutrient(sim_client, auth_headers):
    sim_client.post("/demo/reset", headers=auth_headers)

    res = run_simulation(
        scenario="nutrient",
        farm_id="sim-nutrient",
        api_url="http://testserver",
        rest_only=True,
        client=sim_client,
    )

    # 1. High nutrient deficiency
    assert any(r["kind"] == "nutrient_deficiency" and r["severity"] == "high" for r in res["risks"])

    # 2. Split-dose urea: 2 doses, 14 days apart
    fertilize_tasks = [t for t in res["tasks"] if t["kind"] == "fertilize"]
    assert len(fertilize_tasks) == 2


def test_simulator_rain_deferral_and_resume(sim_client, auth_headers):
    sim_client.post("/demo/reset", headers=auth_headers)

    # Step 1: Heavy rain
    res1 = run_simulation(
        scenario="rain_deferral",
        farm_id="sim-rain",
        api_url="http://testserver",
        rest_only=True,
        client=sim_client,
    )

    statuses = {a["kind"]: a["status"] for a in res1["plan"]["actions"]}
    assert statuses["irrigate"] == "skipped"
    assert statuses["fertilize"] == "deferred"
    assert res1["tasks"] == []

    # Step 2: Clear rain
    res2 = run_simulation(
        scenario="rain_deferral",
        farm_id="sim-rain",
        api_url="http://testserver",
        rest_only=True,
        clear_rain=True,
        client=sim_client,
    )

    # Actions auto-resumed -> 3 tasks created (1 irrigate + 2 urea)
    assert len(res2["tasks"]) == 3
