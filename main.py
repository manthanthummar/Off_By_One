"""
FarmSense Root Entrypoint.
Re-exports the application and models from the modular app package.
"""
from __future__ import annotations

import os
from app.main import app
from app.config import settings, T, SEVERITY_RANK, SEVERITY_SCORE
from app.models.schemas import (
    Severity,
    ActionKind,
    ActionStatus,
    TaskStatus,
    Plot,
    Farm,
    SoilReading,
    WeatherReading,
    DroneReading,
    Risk,
    Action,
    Plan,
    Task,
    Escalation,
    SmsAlert,
    TraceEntry,
    TaskPatch,
    EscalationResolve,
    now,
    uid,
)
from app.db.repository import store, Store
from app.services.notifier import (
    SafetyGateError,
    needs_expert,
    gate_ok,
    set_action_status,
    sms_text,
    send_sms,
)
from app.agents.detection import RiskDetectionAgent
from app.agents.planner import PlannerAgent
from app.agents.executor import ExecutorAgent
from app.agents.advisor import LLMAdvisor
from app.agents.orchestrator import Orchestrator, orchestrator
from app.services.mqtt import mqtt_service, ingest_payload
from app.services.weather import fetch_open_meteo

__all__ = [
    "app",
    "settings",
    "T",
    "SEVERITY_RANK",
    "SEVERITY_SCORE",
    "Severity",
    "ActionKind",
    "ActionStatus",
    "TaskStatus",
    "Plot",
    "Farm",
    "SoilReading",
    "WeatherReading",
    "DroneReading",
    "Risk",
    "Action",
    "Plan",
    "Task",
    "Escalation",
    "SmsAlert",
    "TraceEntry",
    "TaskPatch",
    "EscalationResolve",
    "now",
    "uid",
    "store",
    "Store",
    "SafetyGateError",
    "needs_expert",
    "gate_ok",
    "set_action_status",
    "sms_text",
    "send_sms",
    "RiskDetectionAgent",
    "PlannerAgent",
    "ExecutorAgent",
    "LLMAdvisor",
    "Orchestrator",
    "orchestrator",
    "mqtt_service",
    "ingest_payload",
    "fetch_open_meteo",
]

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=False)
