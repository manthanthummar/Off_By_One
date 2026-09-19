from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Any, Optional
from fastapi import HTTPException
from sqlalchemy import select, delete

from app.db.session import SessionLocal, init_db
from app.models.orm import (
    FarmModel,
    SoilReadingModel,
    WeatherReadingModel,
    DroneReadingModel,
    RiskModel,
    PlanModel,
    ActionModel,
    TaskModel,
    EscalationModel,
    SmsAlertModel,
    TraceEntryModel,
)
from app.models.schemas import (
    Farm,
    Plot,
    SoilReading,
    WeatherReading,
    DroneReading,
    Risk,
    Plan,
    Action,
    Task,
    Escalation,
    SmsAlert,
    TraceEntry,
    ensure_utc,
    now,
)

log = logging.getLogger("farmsense.repo")


class Store:
    """SQLAlchemy-backed repository store preserving dictionary access and thread-safety."""
    MAX_HISTORY = 1000

    def __init__(self) -> None:
        self.lock = threading.RLock()
        # In-memory working caches synchronized with database
        self.farms: dict[str, Farm] = {}
        self.soil: dict[str, list[SoilReading]] = {}
        self.weather: dict[str, list[WeatherReading]] = {}
        self.drone: dict[str, list[DroneReading]] = {}
        self.risks: dict[str, Risk] = {}
        self.plans: dict[str, Plan] = {}
        self.actions: dict[str, Action] = {}
        self.tasks: dict[str, Task] = {}
        self.escalations: dict[str, Escalation] = {}
        self.alerts: list[SmsAlert] = []
        self.trace: list[TraceEntry] = []
        self._db_initialized = False

    def ensure_db(self) -> None:
        if not self._db_initialized:
            with self.lock:
                if not self._db_initialized:
                    init_db()
                    self._load_from_db()
                    self._db_initialized = True

    def _load_from_db(self) -> None:
        try:
            with SessionLocal() as db:
                # Load farms
                farms = db.scalars(select(FarmModel)).all()
                for fm in farms:
                    plots = [Plot(**p) if isinstance(p, dict) else p for p in (fm.plots or [])]
                    f = Farm(
                        id=fm.id, name=fm.name, owner=fm.owner or "", phone=fm.phone or "",
                        lat=fm.lat, lon=fm.lon, budget_inr=fm.budget_inr,
                        plots=plots or [Plot()]
                    )
                    self.farms[f.id] = f

                # Load risks
                risks = db.scalars(select(RiskModel)).all()
                for rm in risks:
                    r = Risk(
                        id=rm.id, farm_id=rm.farm_id, plot_id=rm.plot_id,
                        kind=rm.kind, severity=rm.severity, score=rm.score,  # type: ignore
                        summary=rm.summary, evidence=rm.evidence or {},
                        status=rm.status, created_at=ensure_utc(rm.created_at), updated_at=ensure_utc(rm.updated_at)  # type: ignore
                    )
                    self.risks[r.id] = r

                # Load actions
                actions = db.scalars(select(ActionModel)).all()
                for am in actions:
                    a = Action(
                        id=am.id, plan_id=am.plan_id or "", farm_id=am.farm_id, plot_id=am.plot_id,
                        risk_id=am.risk_id, kind=am.kind, title=am.title, what=am.what,  # type: ignore
                        when=ensure_utc(am.when), where=am.where_text or "", cost_inr=am.cost_inr,  # type: ignore
                        status=am.status, requires_expert_approval=am.requires_expert_approval,  # type: ignore
                        rationale=am.rationale or "", safety_notes=am.safety_notes or [],
                        hold_reason=am.hold_reason, hold_notified=am.hold_notified,  # type: ignore
                        deferred_until=ensure_utc(am.deferred_until)
                    )
                    self.actions[a.id] = a

                # Load plans
                plans = db.scalars(select(PlanModel)).all()
                for pm in plans:
                    plan_acts = [a for a in self.actions.values() if a.plan_id == pm.id]
                    p = Plan(
                        id=pm.id, farm_id=pm.farm_id, created_at=ensure_utc(pm.created_at),  # type: ignore
                        actions=plan_acts, total_cost_inr=pm.total_cost_inr,
                        budget_inr=pm.budget_inr, weather_rationale=pm.weather_rationale or [],
                        advice=pm.advice or "", advice_source=pm.advice_source or "offline"  # type: ignore
                    )
                    self.plans[p.id] = p

                # Load tasks
                tasks = db.scalars(select(TaskModel)).all()
                for tm in tasks:
                    t = Task(
                        id=tm.id, farm_id=tm.farm_id, action_id=tm.action_id,
                        plot_id=tm.plot_id, kind=tm.kind, title=tm.title,  # type: ignore
                        status=tm.status, due=ensure_utc(tm.due), requires_expert_approval=tm.requires_expert_approval,  # type: ignore
                        created_at=ensure_utc(tm.created_at), updated_at=ensure_utc(tm.updated_at)  # type: ignore
                    )
                    self.tasks[t.id] = t

                # Load escalations
                escalations = db.scalars(select(EscalationModel)).all()
                for em in escalations:
                    e = Escalation(
                        id=em.id, farm_id=em.farm_id, action_id=em.action_id,
                        reason=em.reason, status=em.status, advice=em.advice or "",  # type: ignore
                        resolved_by=em.resolved_by or "", created_at=ensure_utc(em.created_at),  # type: ignore
                        resolved_at=ensure_utc(em.resolved_at)
                    )
                    self.escalations[e.id] = e

                # Load alerts
                alerts = db.scalars(select(SmsAlertModel).order_by(SmsAlertModel.ts)).all()
                for am in alerts:
                    self.alerts.append(SmsAlert(
                        id=am.id, farm_id=am.farm_id, action_id=am.action_id,
                        to=am.to_phone or "", message=am.message, ts=ensure_utc(am.ts)  # type: ignore
                    ))

                # Load trace
                traces = db.scalars(select(TraceEntryModel).order_by(TraceEntryModel.ts)).all()
                for tr in traces:
                    self.trace.append(TraceEntry(
                        id=tr.id, run_id=tr.run_id, farm_id=tr.farm_id, agent=tr.agent,
                        input_summary=tr.input_summary, output_summary=tr.output_summary,
                        latency_ms=tr.latency_ms, output_tokens=tr.output_tokens, ts=ensure_utc(tr.ts)  # type: ignore
                    ))
        except Exception as exc:
            log.warning("Database load skipped or failed: %s", exc)

    def persist_all(self) -> None:
        """Persist in-memory state to database."""
        self.ensure_db()
        try:
            with SessionLocal() as db:
                # Merge farms
                for f in self.farms.values():
                    fm = db.get(FarmModel, f.id)
                    if not fm:
                        fm = FarmModel(id=f.id)
                        db.add(fm)
                    fm.name = f.name
                    fm.owner = f.owner
                    fm.phone = f.phone
                    fm.lat = f.lat
                    fm.lon = f.lon
                    fm.budget_inr = f.budget_inr
                    fm.plots = [p.model_dump() for p in f.plots]

                # Merge risks
                for r in self.risks.values():
                    rm = db.get(RiskModel, r.id)
                    if not rm:
                        rm = RiskModel(id=r.id)
                        db.add(rm)
                    rm.farm_id = r.farm_id
                    rm.plot_id = r.plot_id
                    rm.kind = r.kind
                    rm.severity = r.severity
                    rm.score = r.score
                    rm.summary = r.summary
                    rm.evidence = r.evidence
                    rm.status = r.status
                    rm.created_at = r.created_at
                    rm.updated_at = r.updated_at

                # Merge actions
                for a in self.actions.values():
                    am = db.get(ActionModel, a.id)
                    if not am:
                        am = ActionModel(id=a.id)
                        db.add(am)
                    am.plan_id = a.plan_id
                    am.farm_id = a.farm_id
                    am.plot_id = a.plot_id
                    am.risk_id = a.risk_id
                    am.kind = a.kind
                    am.title = a.title
                    am.what = a.what
                    am.when = a.when
                    am.where_text = a.where
                    am.cost_inr = a.cost_inr
                    am.status = a.status
                    am.requires_expert_approval = a.requires_expert_approval
                    am.rationale = a.rationale
                    am.safety_notes = a.safety_notes
                    am.hold_reason = a.hold_reason
                    am.hold_notified = a.hold_notified
                    am.deferred_until = a.deferred_until

                # Merge plans
                for p in self.plans.values():
                    pm = db.get(PlanModel, p.id)
                    if not pm:
                        pm = PlanModel(id=p.id)
                        db.add(pm)
                    pm.farm_id = p.farm_id
                    pm.created_at = p.created_at
                    pm.total_cost_inr = p.total_cost_inr
                    pm.budget_inr = p.budget_inr
                    pm.weather_rationale = p.weather_rationale
                    pm.advice = p.advice
                    pm.advice_source = p.advice_source

                # Merge tasks
                for t in self.tasks.values():
                    tm = db.get(TaskModel, t.id)
                    if not tm:
                        tm = TaskModel(id=t.id)
                        db.add(tm)
                    tm.farm_id = t.farm_id
                    tm.action_id = t.action_id
                    tm.plot_id = t.plot_id
                    tm.kind = t.kind
                    tm.title = t.title
                    tm.status = t.status
                    tm.due = t.due
                    tm.requires_expert_approval = t.requires_expert_approval
                    tm.created_at = t.created_at
                    tm.updated_at = t.updated_at

                # Merge escalations
                for e in self.escalations.values():
                    em = db.get(EscalationModel, e.id)
                    if not em:
                        em = EscalationModel(id=e.id)
                        db.add(em)
                    em.farm_id = e.farm_id
                    em.action_id = e.action_id
                    em.reason = e.reason
                    em.status = e.status
                    em.advice = e.advice
                    em.resolved_by = e.resolved_by
                    em.created_at = e.created_at
                    em.resolved_at = e.resolved_at

                db.commit()
        except Exception as exc:
            log.warning("Database persist error: %s", exc)

    def reset(self) -> None:
        self.ensure_db()
        with self.lock:
            self.farms.clear()
            self.soil.clear()
            self.weather.clear()
            self.drone.clear()
            self.risks.clear()
            self.plans.clear()
            self.actions.clear()
            self.tasks.clear()
            self.escalations.clear()
            self.alerts.clear()
            self.trace.clear()
            try:
                with SessionLocal() as db:
                    for model in (
                        TraceEntryModel, SmsAlertModel, EscalationModel, TaskModel,
                        ActionModel, PlanModel, RiskModel, DroneReadingModel,
                        WeatherReadingModel, SoilReadingModel, FarmModel
                    ):
                        db.execute(delete(model))
                    db.commit()
            except Exception as exc:
                log.warning("Database reset error: %s", exc)

    # -- helpers --------------------------------------------------------------
    def farm(self, farm_id: str) -> Farm:
        f = self.farms.get(farm_id)
        if not f:
            raise HTTPException(404, f"Farm '{farm_id}' not found")
        return f

    def _append(self, bucket: dict[str, list], farm_id: str, item: Any) -> None:
        lst = bucket.setdefault(farm_id, [])
        lst.append(item)
        if len(lst) > self.MAX_HISTORY:
            del lst[: len(lst) - self.MAX_HISTORY]

    def add_soil(self, r: SoilReading) -> None:
        self._append(self.soil, r.farm_id, r)
        try:
            with SessionLocal() as db:
                db.add(SoilReadingModel(
                    farm_id=r.farm_id, plot_id=r.plot_id, moisture_pct=r.moisture_pct,
                    nitrogen_ppm=r.nitrogen_ppm, ph=r.ph, temp_c=r.temp_c, ts=r.ts
                ))
                db.commit()
        except Exception as exc:
            log.debug("DB add_soil error: %s", exc)

    def add_weather(self, r: WeatherReading) -> None:
        self._append(self.weather, r.farm_id, r)
        try:
            with SessionLocal() as db:
                db.add(WeatherReadingModel(
                    farm_id=r.farm_id, temp_c=r.temp_c, humidity_pct=r.humidity_pct,
                    canopy_wet=r.canopy_wet, rain_24h_mm=r.rain_24h_mm, wind_kph=r.wind_kph,
                    evaporation_mm=r.evaporation_mm, forecast=r.forecast, ts=r.ts
                ))
                db.commit()
        except Exception as exc:
            log.debug("DB add_weather error: %s", exc)

    def add_drone(self, r: DroneReading) -> None:
        self._append(self.drone, r.farm_id, r)
        try:
            with SessionLocal() as db:
                db.add(DroneReadingModel(
                    farm_id=r.farm_id, plot_id=r.plot_id, ndvi=r.ndvi,
                    ndvi_prev=r.ndvi_prev, anomaly_score=r.anomaly_score,
                    anomaly_signature=r.anomaly_signature, ts=r.ts
                ))
                db.commit()
        except Exception as exc:
            log.debug("DB add_drone error: %s", exc)

    def latest_soil(self, farm_id: str) -> dict[str, SoilReading]:
        return {r.plot_id: r for r in self.soil.get(farm_id, [])}

    def latest_weather(self, farm_id: str) -> Optional[WeatherReading]:
        lst = self.weather.get(farm_id, [])
        return lst[-1] if lst else None

    def latest_drone(self, farm_id: str) -> tuple[dict[str, DroneReading], dict[str, DroneReading]]:
        latest: dict[str, DroneReading] = {}
        prev: dict[str, DroneReading] = {}
        for r in self.drone.get(farm_id, []):
            if r.plot_id in latest:
                prev[r.plot_id] = latest[r.plot_id]
            latest[r.plot_id] = r
        return latest, prev

    def farm_actions(self, farm_id: str) -> list[Action]:
        return [a for a in self.actions.values() if a.farm_id == farm_id]

    def task_for_action(self, action_id: str) -> Optional[Task]:
        return next((t for t in self.tasks.values() if t.action_id == action_id), None)

    def refresh_overdue(self) -> None:
        t_now = now()
        for t in self.tasks.values():
            t_due = ensure_utc(t.due) or t_now
            if t.status in ("pending", "in_progress") and t_due < t_now:
                t.status = "overdue"


store = Store()
