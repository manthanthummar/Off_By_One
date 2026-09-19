from __future__ import annotations

from typing import Optional
from app.models.schemas import Action, ActionStatus, Farm, SmsAlert
from app.db.repository import Store, store


class SafetyGateError(Exception):
    pass


def needs_expert(action: Action) -> bool:
    return action.kind == "spray" or action.requires_expert_approval


def gate_ok(action: Action, st: Store = store) -> bool:
    """True if the action may move to notified/done."""
    if not needs_expert(action):
        return True
    return any(e.action_id == action.id and e.status == "approved" for e in st.escalations.values())


def set_action_status(action: Action, status: ActionStatus, st: Store = store) -> None:
    if status in ("notified", "done") and not gate_ok(action, st):
        raise SafetyGateError(
            f"Action {action.id} ({action.kind}) requires an approved expert Escalation before '{status}'."
        )
    action.status = status


def sms_text(text: str) -> str:
    text = " ".join(text.split())
    return text if len(text) <= 160 else text[:159].rstrip() + "…"


def send_sms(st: Store, farm: Farm, text: str, action_id: Optional[str] = None) -> SmsAlert:
    """Notifier: SMS-length feed (real gateway can be plugged in here)."""
    alert = SmsAlert(farm_id=farm.id, action_id=action_id, to=farm.phone, message=sms_text(text))
    st.alerts.append(alert)
    return alert
