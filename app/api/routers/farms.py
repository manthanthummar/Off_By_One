from __future__ import annotations

from datetime import timedelta
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query

from app.models.schemas import Farm, Risk, Plan, Task, now
from app.db.repository import store
from app.services.weather import fetch_open_meteo

farms_router = APIRouter(tags=["farms"])


def _filter(items: list, farm_id: Optional[str]) -> list:
    return [i for i in items if farm_id is None or i.farm_id == farm_id]


def _tasks(farm_id: Optional[str], status: Optional[str]) -> list[Task]:
    store.refresh_overdue()
    items = _filter(list(store.tasks.values()), farm_id)
    return [t for t in items if status is None or t.status == status]


def _risks(
    farm_id: Optional[str], status: Optional[str], severity: Optional[str]
) -> list[Risk]:
    items = _filter(list(store.risks.values()), farm_id)
    return [
        r
        for r in items
        if (status is None or r.status == status)
        and (severity is None or r.severity == severity)
    ]


def _plans(farm_id: Optional[str]) -> list[Plan]:
    return sorted(
        _filter(list(store.plans.values()), farm_id),
        key=lambda p: p.created_at,
        reverse=True,
    )


@farms_router.post("/farms", response_model=Farm, status_code=201)
def create_farm(farm: Farm) -> Farm:
    with store.lock:
        if farm.id in store.farms:
            raise HTTPException(409, f"Farm '{farm.id}' already exists")
        store.farms[farm.id] = farm
        store.persist_all()
    return farm


@farms_router.get("/farms", response_model=list[Farm])
def list_farms() -> list[Farm]:
    return list(store.farms.values())


@farms_router.get("/farms/{farm_id}", response_model=Farm)
def get_farm(farm_id: str) -> Farm:
    return store.farm(farm_id)


@farms_router.delete("/farms/{farm_id}", status_code=204)
def delete_farm(farm_id: str) -> None:
    with store.lock:
        store.farm(farm_id)
        del store.farms[farm_id]
        for bucket in (store.soil, store.weather, store.drone):
            bucket.pop(farm_id, None)
        for coll in (
            store.risks,
            store.plans,
            store.actions,
            store.tasks,
            store.escalations,
        ):
            for k in [k for k, v in coll.items() if v.farm_id == farm_id]:
                del coll[k]
        store.persist_all()


@farms_router.get("/farms/{farm_id}/telemetry")
def farm_telemetry(
    farm_id: str, hours: int = Query(48, ge=1, le=336)
) -> dict[str, Any]:
    store.farm(farm_id)
    cutoff = now() - timedelta(hours=hours)
    return {
        "farm_id": farm_id,
        "hours": hours,
        "soil": [r for r in store.soil.get(farm_id, []) if r.ts >= cutoff],
        "weather": [r for r in store.weather.get(farm_id, []) if r.ts >= cutoff],
        "drone": [r for r in store.drone.get(farm_id, []) if r.ts >= cutoff],
    }


@farms_router.post("/farms/{farm_id}/weather/refresh")
def refresh_weather(farm_id: str) -> dict[str, Any]:
    farm = store.farm(farm_id)
    reading = fetch_open_meteo(farm)
    if reading is None:
        return {"source": "offline", "weather": store.latest_weather(farm_id)}
    with store.lock:
        store.add_weather(reading)
    return {"source": "open-meteo", "weather": reading}


@farms_router.get("/farms/{farm_id}/risks", response_model=list[Risk])
def farm_risks(
    farm_id: str,
    status: Optional[str] = None,
    severity: Optional[str] = None,
) -> list[Risk]:
    store.farm(farm_id)
    return _risks(farm_id, status, severity)


@farms_router.get("/farms/{farm_id}/plans", response_model=list[Plan])
def farm_plans(farm_id: str) -> list[Plan]:
    store.farm(farm_id)
    return _plans(farm_id)


@farms_router.get("/farms/{farm_id}/tasks", response_model=list[Task])
def farm_tasks(farm_id: str, status: Optional[str] = None) -> list[Task]:
    store.farm(farm_id)
    return _tasks(farm_id, status)


# -- top-level filterable views (multi-farm / global)
@farms_router.get("/risks", response_model=list[Risk])
def all_risks(
    farm_id: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
) -> list[Risk]:
    return _risks(farm_id, status, severity)


@farms_router.get("/plans", response_model=list[Plan])
def all_plans(farm_id: Optional[str] = None) -> list[Plan]:
    return _plans(farm_id)
