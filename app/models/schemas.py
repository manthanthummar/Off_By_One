from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, model_validator


def now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def uid(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ════════════════════════════════════════════════════════════════════════════
# Domain Enums & Schemas (Pydantic v2)
# ════════════════════════════════════════════════════════════════════════════
Severity = Literal["low", "medium", "high", "critical"]
ActionKind = Literal["irrigate", "fertilize", "scout", "spray"]
ActionStatus = Literal["planned", "deferred", "skipped", "awaiting_approval", "notified", "done"]
TaskStatus = Literal["pending", "in_progress", "done", "overdue"]


class Plot(BaseModel):
    id: str = "plot-1"
    name: str = "Plot 1"
    crop: str = "wheat"
    area_ha: float = 1.0


class Farm(BaseModel):
    id: str = Field(default_factory=lambda: uid("farm"))
    name: str
    owner: str = ""
    phone: str = ""
    lat: Optional[float] = None
    lon: Optional[float] = None
    budget_inr: float = 5000.0
    plots: list[Plot] = Field(default_factory=lambda: [Plot()])


class SoilReading(BaseModel):
    farm_id: str
    plot_id: str = "plot-1"
    moisture_pct: float
    nitrogen_ppm: Optional[float] = None
    ph: Optional[float] = None
    temp_c: Optional[float] = None
    ts: datetime = Field(default_factory=now)


class WeatherReading(BaseModel):
    farm_id: str
    temp_c: Optional[float] = None
    humidity_pct: float
    canopy_wet: bool = False
    rain_24h_mm: float = 0.0            # forecast rain in the next 24 h
    wind_kph: float = 0.0
    evaporation_mm: float = 0.0         # ET0 / evaporation
    forecast: list[dict[str, Any]] = Field(default_factory=list)   # JSONB-friendly
    ts: datetime = Field(default_factory=now)


class DroneReading(BaseModel):
    farm_id: str
    plot_id: str = "plot-1"
    ndvi: float
    ndvi_prev: Optional[float] = None
    anomaly_score: float = 0.0          # 0..1
    anomaly_signature: str = ""         # e.g. "leaf-lesion-cluster"
    ts: datetime = Field(default_factory=now)


class Risk(BaseModel):
    id: str = Field(default_factory=lambda: uid("risk"))
    farm_id: str
    plot_id: str
    kind: Literal["water_stress", "fungal_disease", "nutrient_deficiency", "vegetation_decline"]
    severity: Severity
    score: int
    summary: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    status: Literal["open", "resolved"] = "open"
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)


class Action(BaseModel):
    id: str = Field(default_factory=lambda: uid("act"))
    plan_id: str = ""
    farm_id: str
    plot_id: str
    risk_id: str
    kind: ActionKind
    title: str
    what: str
    when: datetime
    where: str
    cost_inr: float = 0.0
    status: ActionStatus = "planned"
    requires_expert_approval: bool = False
    rationale: str = ""
    safety_notes: list[str] = Field(default_factory=list)
    hold_reason: Optional[Literal["weather", "budget", "expert_rejected"]] = None
    hold_notified: bool = False
    deferred_until: Optional[datetime] = None

    @model_validator(mode="after")
    def _spray_always_gated(self) -> "Action":
        if self.kind == "spray":
            self.requires_expert_approval = True
        return self


class Plan(BaseModel):
    id: str = Field(default_factory=lambda: uid("plan"))
    farm_id: str
    created_at: datetime = Field(default_factory=now)
    actions: list[Action] = Field(default_factory=list)   # same objects as Store.actions (live view)
    total_cost_inr: float = 0.0
    budget_inr: float = 0.0
    weather_rationale: list[str] = Field(default_factory=list)
    advice: str = ""
    advice_source: Literal["llm", "offline"] = "offline"


class Task(BaseModel):
    id: str = Field(default_factory=lambda: uid("task"))
    farm_id: str
    action_id: str
    plot_id: str
    kind: ActionKind
    title: str
    status: TaskStatus = "pending"
    due: datetime
    requires_expert_approval: bool = False
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)


class Escalation(BaseModel):
    id: str = Field(default_factory=lambda: uid("esc"))
    farm_id: str
    action_id: str
    reason: str
    status: Literal["pending", "approved", "rejected"] = "pending"
    advice: str = ""
    resolved_by: str = ""
    created_at: datetime = Field(default_factory=now)
    resolved_at: Optional[datetime] = None


class SmsAlert(BaseModel):
    id: str = Field(default_factory=lambda: uid("sms"))
    farm_id: str
    action_id: Optional[str] = None
    to: str = ""
    message: str                     # always <= 160 chars
    ts: datetime = Field(default_factory=now)


class TraceEntry(BaseModel):
    id: str = Field(default_factory=lambda: uid("trace"))
    run_id: str
    farm_id: str
    agent: str
    input_summary: str
    output_summary: str
    latency_ms: float
    output_tokens: int
    ts: datetime = Field(default_factory=now)


# Request bodies
class TaskPatch(BaseModel):
    status: TaskStatus


class EscalationResolve(BaseModel):
    approved: bool
    advice: str = ""
    resolved_by: str = "agronomist"
