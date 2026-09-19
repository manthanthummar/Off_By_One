from __future__ import annotations

from datetime import datetime
from typing import Any
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

JSONType = JSON().with_variant(JSONB, "postgresql")


class FarmModel(Base):
    __tablename__ = "farms"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    owner: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(64), default="")
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lon: Mapped[float | None] = mapped_column(Float, nullable=True)
    budget_inr: Mapped[float] = mapped_column(Float, default=5000.0)
    plots: Mapped[list[dict[str, Any]]] = mapped_column(JSONType, default=list)


class SoilReadingModel(Base):
    __tablename__ = "soil_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    farm_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    plot_id: Mapped[str] = mapped_column(String(64), default="plot-1")
    moisture_pct: Mapped[float] = mapped_column(Float, nullable=False)
    nitrogen_ppm: Mapped[float | None] = mapped_column(Float, nullable=True)
    ph: Mapped[float | None] = mapped_column(Float, nullable=True)
    temp_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class WeatherReadingModel(Base):
    __tablename__ = "weather_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    farm_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    temp_c: Mapped[float | None] = mapped_column(Float, nullable=True)
    humidity_pct: Mapped[float] = mapped_column(Float, nullable=False)
    canopy_wet: Mapped[bool] = mapped_column(Boolean, default=False)
    rain_24h_mm: Mapped[float] = mapped_column(Float, default=0.0)
    wind_kph: Mapped[float] = mapped_column(Float, default=0.0)
    evaporation_mm: Mapped[float] = mapped_column(Float, default=0.0)
    forecast: Mapped[list[dict[str, Any]]] = mapped_column(JSONType, default=list)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class DroneReadingModel(Base):
    __tablename__ = "drone_readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    farm_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    plot_id: Mapped[str] = mapped_column(String(64), default="plot-1")
    ndvi: Mapped[float] = mapped_column(Float, nullable=False)
    ndvi_prev: Mapped[float | None] = mapped_column(Float, nullable=True)
    anomaly_score: Mapped[float] = mapped_column(Float, default=0.0)
    anomaly_signature: Mapped[str] = mapped_column(String(255), default="")
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class RiskModel(Base):
    __tablename__ = "risks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    farm_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    plot_id: Mapped[str] = mapped_column(String(64), nullable=False)
    kind: Mapped[str] = mapped_column(String(64), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONType, default=dict)
    status: Mapped[str] = mapped_column(String(32), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PlanModel(Base):
    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    farm_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    total_cost_inr: Mapped[float] = mapped_column(Float, default=0.0)
    budget_inr: Mapped[float] = mapped_column(Float, default=0.0)
    weather_rationale: Mapped[list[str]] = mapped_column(JSONType, default=list)
    advice: Mapped[str] = mapped_column(Text, default="")
    advice_source: Mapped[str] = mapped_column(String(32), default="offline")


class ActionModel(Base):
    __tablename__ = "actions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    plan_id: Mapped[str] = mapped_column(String(64), index=True, default="")
    farm_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    plot_id: Mapped[str] = mapped_column(String(64), nullable=False)
    risk_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    what: Mapped[str] = mapped_column(Text, nullable=False)
    when: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    where_text: Mapped[str] = mapped_column(String(255), default="")
    cost_inr: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="planned")
    requires_expert_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    rationale: Mapped[str] = mapped_column(Text, default="")
    safety_notes: Mapped[list[str]] = mapped_column(JSONType, default=list)
    hold_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hold_notified: Mapped[bool] = mapped_column(Boolean, default=False)
    deferred_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TaskModel(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    farm_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    action_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    plot_id: Mapped[str] = mapped_column(String(64), nullable=False)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    due: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    requires_expert_approval: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class EscalationModel(Base):
    __tablename__ = "escalations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    farm_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    action_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    advice: Mapped[str] = mapped_column(Text, default="")
    resolved_by: Mapped[str] = mapped_column(String(128), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class SmsAlertModel(Base):
    __tablename__ = "sms_alerts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    farm_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    action_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    to_phone: Mapped[str] = mapped_column(String(64), default="")
    message: Mapped[str] = mapped_column(String(160), nullable=False)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class TraceEntryModel(Base):
    __tablename__ = "trace_entries"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    farm_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    agent: Mapped[str] = mapped_column(String(64), nullable=False)
    input_summary: Mapped[str] = mapped_column(Text, default="")
    output_summary: Mapped[str] = mapped_column(Text, default="")
    latency_ms: Mapped[float] = mapped_column(Float, default=0.0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
