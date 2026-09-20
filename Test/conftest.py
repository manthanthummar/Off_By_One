from __future__ import annotations

import os
import pytest
from fastapi.testclient import TestClient

import main

@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(main.app)

@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"X-API-Key": main.settings.api_key}

@pytest.fixture
def reset_store(client: TestClient, auth_headers: dict[str, str]):
    client.post("/demo/reset", headers=auth_headers)
    yield
    client.post("/demo/reset", headers=auth_headers)

@pytest.fixture
def test_farm(client: TestClient, auth_headers: dict[str, str], reset_store) -> str:
    farm_id = "f_test"
    client.post(
        "/farms",
        json={
            "id": farm_id,
            "name": "Test Farm",
            "owner": "Test Owner",
            "phone": "+919999999999",
            "budget_inr": 5000.0,
            "plots": [
                {"id": "plot-1", "name": "Plot 1", "crop": "wheat", "area_ha": 1.0},
                {"id": "plot-2", "name": "Plot 2", "crop": "rice", "area_ha": 1.5},
            ],
        },
        headers=auth_headers,
    )
    return farm_id
