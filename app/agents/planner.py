from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional
from app.config import T, SEVERITY_RANK
from app.models.schemas import Farm, Risk, WeatherReading, Action, Plan, now
from app.db.repository import Store


class PlannerAgent:
    name = "PlannerAgent"

    # -- weather window -------------------------------------------------------
    @staticmethod
    def window(kind: str, weather: Optional[WeatherReading]) -> tuple[str, str]:
        """Return (verdict, reason); verdict in ok|skip|defer."""
        if weather is None:
            return "ok", ""
        rain, wind = weather.rain_24h_mm, weather.wind_kph
        if kind == "irrigate" and rain > T["rain_skip_irrigation_mm"]:
            return (
                "skip",
                f"{rain:.0f} mm rain forecast in 24h (> {T['rain_skip_irrigation_mm']:.0f} mm) - irrigation skipped.",
            )
        if kind == "fertilize" and rain >= T["rain_heavy_mm"]:
            return "defer", f"Heavy rain ({rain:.0f} mm/24h) would leach fertilizer - deferred 48h."
        if kind == "spray" and (rain > T["spray_max_rain_mm"] or wind > T["spray_max_wind_kph"]):
            return (
                "defer",
                f"Rain {rain:.0f} mm / wind {wind:.0f} kph unsafe for spraying - deferred 24h.",
            )
        return "ok", ""

    def reevaluate(
        self, actions: list[Action], weather: Optional[WeatherReading], st: Store
    ) -> list[str]:
        """Re-apply the weather window to live actions (auto-defer / auto-resume)."""
        notes: list[str] = []
        for a in actions:
            verdict, reason = self.window(a.kind, weather)
            if a.status in ("planned", "notified", "awaiting_approval") and verdict != "ok":
                a.status = "skipped" if verdict == "skip" else "deferred"
                a.hold_reason, a.hold_notified = "weather", False
                a.deferred_until = now() + timedelta(hours=48 if a.kind == "fertilize" else 24)
                a.rationale = reason
                t = st.task_for_action(a.id)
                if t and t.status == "pending":
                    del st.tasks[t.id]
                notes.append(f"{a.title}: {reason}")
            elif (
                a.status in ("deferred", "skipped")
                and a.hold_reason == "weather"
                and verdict == "ok"
            ):
                a.status, a.hold_reason, a.deferred_until = "planned", None, None
                a.rationale = "Weather window cleared - action resumed."
                notes.append(f"{a.title}: weather window cleared, resumed.")
        return notes

    # -- planning -------------------------------------------------------------
    def plan(
        self,
        farm: Farm,
        risks: list[Risk],
        weather: Optional[WeatherReading],
        existing: list[Action],
    ) -> Optional[Plan]:
        t0 = now()
        already = {a.risk_id for a in existing if a.status != "done"}
        committed = sum(
            a.cost_inr
            for a in existing
            if a.status in ("planned", "notified", "awaiting_approval", "done")
        )
        remaining = farm.budget_inr - committed
        area = {p.id: p.area_ha for p in farm.plots}

        candidates: list[Action] = []
        for r in sorted(
            (r for r in risks if r.status == "open" and r.id not in already),
            key=lambda r: -SEVERITY_RANK[r.severity],
        ):
            candidates.extend(self._candidates(r, area.get(r.plot_id, 1.0), t0))
        if not candidates:
            return None

        plan = Plan(farm_id=farm.id, budget_inr=farm.budget_inr)
        for a in candidates:
            a.plan_id = plan.id
            verdict, reason = self.window(a.kind, weather)
            if verdict == "skip":
                a.status, a.hold_reason, a.rationale = "skipped", "weather", reason
            elif verdict == "defer":
                a.status, a.hold_reason, a.rationale = "deferred", "weather", reason
                a.deferred_until = t0 + timedelta(hours=48 if a.kind == "fertilize" else 24)
            elif a.cost_inr > remaining:
                a.status, a.hold_reason = "skipped", "budget"
                a.rationale = (
                    f"Over budget (Rs{a.cost_inr:.0f} > remaining Rs{max(remaining, 0):.0f}) - skipped."
                )
            else:
                remaining -= a.cost_inr
            if reason:
                plan.weather_rationale.append(f"{a.title}: {reason}")
            plan.actions.append(a)

        plan.total_cost_inr = sum(a.cost_inr for a in plan.actions if a.status == "planned")
        if not plan.weather_rationale:
            plan.weather_rationale.append("Weather window clear for all planned actions.")
        return plan

    def _candidates(self, r: Risk, area: float, t0: datetime) -> list[Action]:
        base = dict(
            farm_id=r.farm_id,
            plot_id=r.plot_id,
            risk_id=r.id,
            where=f"{r.plot_id} ({area:g} ha)",
        )
        soon = t0 + timedelta(minutes=30)
        morning = (t0 + timedelta(days=1)).replace(
            hour=0, minute=30, second=0, microsecond=0
        )  # ~06:00 IST
        urgent = r.severity == "critical"
        out: list[Action] = []

        if r.kind == "water_stress":
            out.append(
                Action(
                    kind="irrigate",
                    title=f"Irrigate {r.plot_id}",
                    what=f"Irrigate {r.plot_id}: ~25 mm ({'urgent, now' if urgent else 'early morning'}).",
                    when=soon if urgent else morning,
                    cost_inr=250.0 * area,
                    rationale=f"{r.severity} water stress: {r.summary}",
                    safety_notes=["Irrigate early morning/evening to cut evaporation."],
                    **base,
                )
            )
        elif r.kind == "nutrient_deficiency":
            kg = 30.0 * area
            for i, days in enumerate((0, 14), start=1):
                out.append(
                    Action(
                        kind="fertilize",
                        title=f"Urea dose {i}/2 {r.plot_id}",
                        what=f"Apply urea {kg:.0f} kg (dose {i}/2, split-dose) on {r.plot_id}.",
                        when=morning + timedelta(days=days),
                        cost_inr=kg * 7.0 + 100.0,
                        rationale=f"{r.summary} Split dosing limits leaching/loss.",
                        safety_notes=["Apply on moist soil, not before heavy rain."],
                        **base,
                    )
                )
        elif r.kind in ("fungal_disease", "vegetation_decline"):
            out.append(
                Action(
                    kind="scout",
                    title=f"Scout {r.plot_id}",
                    what=f"Walk {r.plot_id}, inspect leaves/canopy, photograph symptoms.",
                    when=t0 + timedelta(hours=3 if r.severity in ("high", "critical") else 12),
                    cost_inr=50.0,
                    rationale=r.summary,
                    safety_notes=["Avoid scouting wet foliage to prevent spreading spores."],
                    **base,
                )
            )
            if r.kind == "fungal_disease" and SEVERITY_RANK[r.severity] >= SEVERITY_RANK["high"]:
                out.append(
                    Action(
                        kind="spray",
                        title=f"Fungicide spray {r.plot_id}",
                        what=f"Fungicide application on {r.plot_id} - ONLY after agronomist approval.",
                        when=morning,
                        cost_inr=450.0 * area,
                        requires_expert_approval=True,
                        rationale=f"{r.summary} Chemical - expert sign-off required.",
                        safety_notes=[
                            "Agronomist must approve product and dose.",
                            "Wear PPE (gloves, mask, long sleeves).",
                            "Do not spray in wind > 20 kph or rain within 6h.",
                            "Respect pre-harvest interval on the label.",
                        ],
                        **base,
                    )
                )
        return out
