from __future__ import annotations

import time
from typing import Any, Optional
from app.models.schemas import Risk, TraceEntry, uid, now
from app.db.repository import Store, store
from app.agents.detection import RiskDetectionAgent
from app.agents.planner import PlannerAgent
from app.agents.executor import ExecutorAgent
from app.agents.advisor import LLMAdvisor


class Orchestrator:
    def __init__(self, st: Store) -> None:
        self.st = st
        self.detector = RiskDetectionAgent()
        self.planner = PlannerAgent()
        self.executor = ExecutorAgent()
        self.advisor = LLMAdvisor()

    def _trace(
        self,
        run_id: str,
        farm_id: str,
        agent: str,
        inp: str,
        out: str,
        t0: float,
        toks: Optional[int] = None,
    ):
        self.st.trace.append(
            TraceEntry(
                run_id=run_id,
                farm_id=farm_id,
                agent=agent,
                input_summary=inp,
                output_summary=out,
                latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                output_tokens=toks if toks is not None else max(1, len(out) // 4),
            )
        )

    def run(self, farm_id: str, use_llm: bool = True) -> dict[str, Any]:
        st = self.st
        with st.lock:
            farm = st.farm(farm_id)
            run_id = uid("run")
            weather = st.latest_weather(farm_id)
            soil = st.latest_soil(farm_id)
            drone, drone_prev = st.latest_drone(farm_id)

            # 0) weather-window re-evaluation of live actions (auto-defer / auto-resume)
            t0 = time.perf_counter()
            notes = self.planner.reevaluate(st.farm_actions(farm_id), weather, st)
            self._trace(
                run_id,
                farm_id,
                "PlannerAgent.reevaluate",
                f"{len(st.farm_actions(farm_id))} live actions, rain24h={weather.rain_24h_mm if weather else 'n/a'}mm",
                f"{len(notes)} weather changes",
                t0,
            )

            # 1) detect + upsert risks (resolve risks whose condition disappeared)
            t0 = time.perf_counter()
            detected = self.detector.detect(farm, soil, weather, drone, drone_prev)
            open_now: list[Risk] = []
            seen: set[tuple[str, str]] = set()
            for r in detected:
                key = (r.plot_id, r.kind)
                seen.add(key)
                existing = next(
                    (
                        x
                        for x in st.risks.values()
                        if x.farm_id == farm_id and (x.plot_id, x.kind) == key and x.status == "open"
                    ),
                    None,
                )
                if existing:
                    existing.severity, existing.score = r.severity, r.score
                    existing.summary, existing.evidence, existing.updated_at = (
                        r.summary,
                        r.evidence,
                        now(),
                    )
                    open_now.append(existing)
                else:
                    st.risks[r.id] = r
                    open_now.append(r)
            for x in st.risks.values():
                if x.farm_id == farm_id and x.status == "open" and (x.plot_id, x.kind) not in seen:
                    x.status, x.updated_at = "resolved", now()
            self._trace(
                run_id,
                farm_id,
                self.detector.name,
                f"soil={len(soil)} plots, weather={'yes' if weather else 'no'}, drone={len(drone)} plots",
                f"{len(open_now)} open risks: "
                + ", ".join(f"{r.kind}/{r.severity}" for r in open_now),
                t0,
            )

            # 2) plan
            t0 = time.perf_counter()
            plan = self.planner.plan(farm, open_now, weather, st.farm_actions(farm_id))
            if plan:
                st.plans[plan.id] = plan
                for a in plan.actions:
                    st.actions[a.id] = a
            self._trace(
                run_id,
                farm_id,
                self.planner.name,
                f"{len(open_now)} risks, budget Rs{farm.budget_inr:.0f}",
                f"{len(plan.actions) if plan else 0} actions, Rs{plan.total_cost_inr if plan else 0:.0f} planned",
                t0,
            )

            # 3) execute (planned actions incl. resumed ones)
            t0 = time.perf_counter()
            to_run = [
                a
                for a in st.farm_actions(farm_id)
                if a.status == "planned"
                or (a.status in ("deferred", "skipped") and not a.hold_notified)
            ]
            result = self.executor.execute(farm, to_run, st)
            self._trace(
                run_id,
                farm_id,
                self.executor.name,
                f"{len(to_run)} actions",
                f"{len(result['tasks'])} tasks, {len(result['escalations'])} escalations, "
                f"{len(result['alerts'])} SMS",
                t0,
            )

            # 4) advise
            t0 = time.perf_counter()
            if use_llm:
                advice, source, toks = self.advisor.advise(
                    farm, open_now, st.farm_actions(farm_id)
                )
            else:
                advice = self.advisor.template(farm, open_now, st.farm_actions(farm_id))
                source, toks = "offline", max(1, len(advice) // 4)
            if plan:
                plan.advice, plan.advice_source = advice, source  # type: ignore[assignment]
            self._trace(
                run_id,
                farm_id,
                self.advisor.name,
                f"{len(open_now)} risks",
                f"[{source}] {advice[:120]}",
                t0,
                toks,
            )

            # Persist state
            st.persist_all()

            return {
                "run_id": run_id,
                "farm_id": farm_id,
                "risks": open_now,
                "plan": plan,
                "tasks": result["tasks"],
                "escalations": result["escalations"],
                "alerts": result["alerts"],
                "weather_changes": notes,
                "advice": advice,
                "advice_source": source,
            }


orchestrator = Orchestrator(store)
