from __future__ import annotations

from datetime import timedelta
from typing import Any
from fastapi import APIRouter

from app.models.schemas import Farm, Plot, SoilReading, WeatherReading, DroneReading, now
from app.db.repository import store
from app.agents.orchestrator import orchestrator

demo_router = APIRouter(prefix="/demo", tags=["demo"])


@demo_router.post("/reset")
def demo_reset() -> dict[str, bool]:
    store.reset()
    return {"ok": True}


@demo_router.post("/seed")
def demo_seed() -> dict[str, Any]:
    """Deterministic mock state: 2 farms, 48h telemetry history, one orchestration run each."""
    store.reset()
    base = now() - timedelta(hours=47)
    farms = [
        Farm(
            id="farm-001",
            name="Green Valley Farm",
            owner="Demo Farmer A",
            phone="+910000000001",
            lat=22.55,
            lon=72.95,
            budget_inr=6000,
            plots=[
                Plot(id="plot-1", name="North Plot", crop="wheat", area_ha=1.5),
                Plot(id="plot-2", name="River Plot", crop="wheat", area_ha=1.0),
            ],
        ),
        Farm(
            id="farm-002",
            name="Sunrise Fields",
            owner="Demo Farmer B",
            phone="+910000000002",
            lat=21.17,
            lon=72.83,
            budget_inr=4000,
            plots=[Plot(id="plot-1", name="Main Plot", crop="rice", area_ha=2.0)],
        ),
    ]
    for f in farms:
        store.farms[f.id] = f
    for h in range(48):  # deterministic 48h history for the dashboard chart
        ts = base + timedelta(hours=h)
        m1 = 38 - h * 0.16 + (2 if h % 24 in (2, 3, 4) else 0)
        m2 = 30 - h * 0.12
        store.add_soil(
            SoilReading(
                farm_id="farm-001",
                plot_id="plot-1",
                moisture_pct=round(m1, 1),
                nitrogen_ppm=58,
                ph=6.8,
                ts=ts,
            )
        )
        store.add_soil(
            SoilReading(
                farm_id="farm-001",
                plot_id="plot-2",
                moisture_pct=round(m2, 1),
                nitrogen_ppm=52,
                ph=6.6,
                ts=ts,
            )
        )
        store.add_soil(
            SoilReading(
                farm_id="farm-002",
                plot_id="plot-1",
                moisture_pct=round(40 - h * 0.05, 1),
                nitrogen_ppm=round(36 - h * 0.02, 1),
                ph=6.4,
                ts=ts,
            )
        )
        evap = round(0.2 + 0.5 * max(0.0, 1 - abs((h % 24) - 13) / 7), 2)
        for fid in ("farm-001", "farm-002"):
            store.add_weather(
                WeatherReading(
                    farm_id=fid,
                    temp_c=24 + (h % 24) / 3,
                    humidity_pct=55 + (h % 24),
                    canopy_wet=False,
                    rain_24h_mm=0,
                    wind_kph=8,
                    evaporation_mm=evap,
                    ts=ts,
                )
            )
    store.add_drone(DroneReading(farm_id="farm-001", plot_id="plot-1", ndvi=0.72, ndvi_prev=0.73))
    store.add_drone(DroneReading(farm_id="farm-001", plot_id="plot-2", ndvi=0.66, ndvi_prev=0.68))
    store.add_drone(DroneReading(farm_id="farm-002", plot_id="plot-1", ndvi=0.70, ndvi_prev=0.71))
    runs = {f.id: orchestrator.run(f.id, use_llm=False) for f in farms}
    store.persist_all()
    return {
        "ok": True,
        "farms": [f.id for f in farms],
        "risks": {k: len(v["risks"]) for k, v in runs.items()},
        "tasks": {k: len(v["tasks"]) for k, v in runs.items()},
    }
