from __future__ import annotations

import json
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.schemas import SoilReading, WeatherReading, DroneReading
from app.services.mqtt import ingest_payload
from app.agents.orchestrator import orchestrator

ingest_router = APIRouter(prefix="/ingest", tags=["ingest"])


def _ingest(kind: str, body: BaseModel, auto: bool, use_llm: bool) -> dict[str, Any]:
    farm_id = body.farm_id  # type: ignore[attr-defined]
    try:
        ingest_payload(kind, farm_id, json.loads(body.model_dump_json(exclude={"farm_id"})))
    except KeyError:
        raise HTTPException(404, f"Farm '{farm_id}' not found")
    out: dict[str, Any] = {"ok": True, "kind": kind, "farm_id": farm_id}
    if auto:
        r = orchestrator.run(farm_id, use_llm)
        out["orchestration"] = {
            "run_id": r["run_id"],
            "risks": len(r["risks"]),
            "tasks": len(r["tasks"]),
        }
    return out


@ingest_router.post("/soil")
def ingest_soil(
    body: SoilReading, auto_orchestrate: bool = False, use_llm: bool = True
) -> dict[str, Any]:
    return _ingest("soil", body, auto_orchestrate, use_llm)


@ingest_router.post("/weather")
def ingest_weather(
    body: WeatherReading, auto_orchestrate: bool = False, use_llm: bool = True
) -> dict[str, Any]:
    return _ingest("weather", body, auto_orchestrate, use_llm)


@ingest_router.post("/drone")
def ingest_drone(
    body: DroneReading, auto_orchestrate: bool = False, use_llm: bool = True
) -> dict[str, Any]:
    return _ingest("drone", body, auto_orchestrate, use_llm)
