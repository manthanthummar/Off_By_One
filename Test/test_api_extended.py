from __future__ import annotations

from fastapi.testclient import TestClient


def test_auth(client: TestClient, auth_headers: dict[str, str]):
    assert client.get("/health").status_code == 200
    assert client.get("/farms").status_code == 401
    assert client.get("/farms", headers={"X-API-Key": "invalid-key"}).status_code == 401
    assert client.get("/farms", headers=auth_headers).status_code == 200


def test_cors(client: TestClient):
    r = client.options(
        "/farms",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert r.headers["access-control-allow-origin"] == "http://localhost:3000"


def test_farm_crud(client: TestClient, auth_headers: dict[str, str], reset_store):
    # Create farm
    r = client.post(
        "/farms",
        json={
            "id": "farm_crud",
            "name": "CRUD Farm",
            "owner": "Owner",
            "phone": "+91",
            "budget_inr": 8000,
        },
        headers=auth_headers,
    )
    assert r.status_code == 201

    # Duplicate create -> 409
    assert client.post("/farms", json={"id": "farm_crud", "name": "Dup"}, headers=auth_headers).status_code == 409

    # Get farm
    r_get = client.get("/farms/farm_crud", headers=auth_headers)
    assert r_get.status_code == 200
    assert r_get.json()["name"] == "CRUD Farm"

    # List farms
    r_list = client.get("/farms", headers=auth_headers)
    assert any(f["id"] == "farm_crud" for f in r_list.json())

    # Delete farm
    assert client.delete("/farms/farm_crud", headers=auth_headers).status_code == 204
    assert client.get("/farms/farm_crud", headers=auth_headers).status_code == 404


def test_top_level_and_nested_filters(client: TestClient, auth_headers: dict[str, str], reset_store):
    client.post("/demo/seed", headers=auth_headers)

    # Top-level risks with filters
    r_all = client.get("/risks", headers=auth_headers).json()
    assert len(r_all) > 0

    r_f1 = client.get("/risks?farm_id=farm-001", headers=auth_headers).json()
    assert all(r["farm_id"] == "farm-001" for r in r_f1)

    r_nested = client.get("/farms/farm-001/risks", headers=auth_headers).json()
    assert len(r_nested) == len(r_f1)

    # Top-level plans
    p_all = client.get("/plans", headers=auth_headers).json()
    assert len(p_all) > 0

    p_f1 = client.get("/farms/farm-001/plans", headers=auth_headers).json()
    assert all(p["farm_id"] == "farm-001" for p in p_f1)

    # Top-level tasks
    t_all = client.get("/tasks", headers=auth_headers).json()
    assert len(t_all) > 0

    t_f2 = client.get("/tasks?farm_id=farm-002", headers=auth_headers).json()
    assert all(t["farm_id"] == "farm-002" for t in t_f2)

    # Telemetry
    telem = client.get("/farms/farm-001/telemetry?hours=24", headers=auth_headers).json()
    assert "soil" in telem and "weather" in telem and "drone" in telem


def test_insights_and_demo(client: TestClient, auth_headers: dict[str, str]):
    client.post("/demo/seed", headers=auth_headers)
    stats = client.get("/insights/stats", headers=auth_headers).json()
    assert stats["farms"] == 2
    assert "open_risks" in stats
    assert "plans" in stats

    insight = client.get("/insights/farm-001", headers=auth_headers).json()
    assert insight["farm_id"] == "farm-001"
    assert insight["source"] == "offline"
    assert len(insight["advice"]) > 0

    # Reset
    assert client.post("/demo/reset", headers=auth_headers).json()["ok"] is True
    assert client.get("/insights/stats", headers=auth_headers).json()["farms"] == 0
