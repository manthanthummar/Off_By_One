from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, HTTPException

from app.models.schemas import Task, TaskPatch, now
from app.db.repository import store
from app.services.notifier import set_action_status, SafetyGateError

tasks_router = APIRouter(tags=["tasks"])


def _filter(items: list, farm_id: Optional[str]) -> list:
    return [i for i in items if farm_id is None or i.farm_id == farm_id]


def _tasks(farm_id: Optional[str], status: Optional[str]) -> list[Task]:
    store.refresh_overdue()
    items = _filter(list(store.tasks.values()), farm_id)
    return [t for t in items if status is None or t.status == status]


@tasks_router.get("/tasks", response_model=list[Task])
def all_tasks(
    farm_id: Optional[str] = None, status: Optional[str] = None
) -> list[Task]:
    return _tasks(farm_id, status)


@tasks_router.patch("/tasks/{task_id}", response_model=Task)
def patch_task(task_id: str, body: TaskPatch) -> Task:
    with store.lock:
        task = store.tasks.get(task_id)
        if not task:
            raise HTTPException(404, "Task not found")
        action = store.actions[task.action_id]
        if body.status == "done":
            if action.status in ("deferred", "skipped"):
                raise HTTPException(409, "Action is on hold; it cannot be completed.")
            try:
                set_action_status(action, "done", store)  # safety gate
            except SafetyGateError as exc:
                raise HTTPException(409, str(exc))
        task.status, task.updated_at = body.status, now()
        store.persist_all()
        return task
