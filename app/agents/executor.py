from __future__ import annotations

from fastapi import HTTPException
from app.models.schemas import Farm, Action, Task, Escalation, EscalationResolve, now
from app.db.repository import Store
from app.services.notifier import needs_expert, gate_ok, set_action_status, send_sms


class ExecutorAgent:
    name = "ExecutorAgent"

    def execute(self, farm: Farm, actions: list[Action], st: Store) -> dict[str, list]:
        out: dict[str, list] = {"tasks": [], "escalations": [], "alerts": []}
        for a in actions:
            if a.status in ("deferred", "skipped"):
                if not a.hold_notified and a.hold_reason in ("weather", "budget"):
                    a.hold_notified = True
                    out["alerts"].append(
                        send_sms(st, farm, f"FarmSense: {a.title} on hold. {a.rationale}", a.id)
                    )
                continue
            if a.status != "planned":
                continue

            if needs_expert(a) and not gate_ok(a, st):
                a.status = "awaiting_approval"
                if not any(
                    e.action_id == a.id and e.status == "pending" for e in st.escalations.values()
                ):
                    esc = Escalation(
                        farm_id=farm.id,
                        action_id=a.id,
                        reason=f"Chemical spray requires agronomist approval: {a.rationale}",
                    )
                    st.escalations[esc.id] = esc
                    out["escalations"].append(esc)
            else:
                set_action_status(a, "notified", st)  # gate re-checked here
                out["alerts"].append(
                    send_sms(
                        st,
                        farm,
                        f"FarmSense: {a.what} By {a.when:%d %b %H:%M}. Cost ~Rs{a.cost_inr:.0f}.",
                        a.id,
                    )
                )

            if st.task_for_action(a.id) is None:
                task = Task(
                    farm_id=farm.id,
                    action_id=a.id,
                    plot_id=a.plot_id,
                    kind=a.kind,
                    title=a.title,
                    due=a.when,
                    requires_expert_approval=needs_expert(a),
                )
                st.tasks[task.id] = task
                out["tasks"].append(task)
        return out

    def resolve_escalation(
        self, esc: Escalation, body: EscalationResolve, st: Store
    ) -> Escalation:
        if esc.status != "pending":
            raise HTTPException(409, f"Escalation already {esc.status}")
        esc.status = "approved" if body.approved else "rejected"
        esc.advice, esc.resolved_by, esc.resolved_at = body.advice, body.resolved_by, now()
        action = st.actions[esc.action_id]
        farm = st.farms[action.farm_id]
        if body.approved:
            if action.status == "awaiting_approval":
                set_action_status(action, "notified", st)  # gate now passes
                send_sms(st, farm, f"FarmSense: Spray approved. {action.what} {body.advice}", action.id)
        else:
            action.status, action.hold_reason = "skipped", "expert_rejected"
            action.rationale = f"Rejected by {body.resolved_by}. {body.advice}".strip()
            t = st.task_for_action(action.id)
            if t and t.status != "done":
                del st.tasks[t.id]
            send_sms(st, farm, f"FarmSense: Spray NOT approved. {body.advice}", action.id)
        return esc
