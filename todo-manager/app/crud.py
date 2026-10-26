"""Database operations (kept separate from the HTTP layer)."""
from datetime import date
from typing import Optional

from sqlalchemy import case, func, or_, select
from sqlalchemy.orm import Session

from . import models, schemas
from .models import Priority, Status, Task


def create_task(db: Session, data: schemas.TaskCreate) -> Task:
    task = Task(**data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task(db: Session, task_id: int) -> Optional[Task]:
    return db.get(Task, task_id)


def list_tasks(
    db: Session,
    status: Optional[Status] = None,
    priority: Optional[Priority] = None,
    q: Optional[str] = None,
    overdue: Optional[bool] = None,
    sort_by: schemas.SortField = schemas.SortField.created_at,
    order: schemas.SortOrder = schemas.SortOrder.desc,
    limit: int = 20,
    offset: int = 0,
):
    stmt = select(Task)

    if status is not None:
        stmt = stmt.where(Task.status == status)
    if priority is not None:
        stmt = stmt.where(Task.priority == priority)
    if q:
        pattern = f"%{q}%"
        stmt = stmt.where(or_(Task.title.ilike(pattern), Task.description.ilike(pattern)))
    if overdue is True:
        stmt = stmt.where(Task.due_date < date.today(), Task.status != Status.completed)

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))

    if sort_by == schemas.SortField.priority:
        column = case((Task.priority == Priority.high, 3), (Task.priority == Priority.medium, 2), else_=1)
    else:
        column = getattr(Task, sort_by.value)
    stmt = stmt.order_by(column.asc() if order == schemas.SortOrder.asc else column.desc(), Task.id.asc())

    items = db.scalars(stmt.limit(limit).offset(offset)).all()
    return total, items


def update_task(db: Session, task: Task, data: schemas.TaskUpdate) -> Task:
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        # title/priority/status can't be NULL, so ignore explicit nulls for them
        if value is None and field in ("title", "priority", "status"):
            continue
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


def delete_task(db: Session, task: Task) -> None:
    db.delete(task)
    db.commit()


def get_stats(db: Session) -> dict:
    by_status = {s.value: 0 for s in Status}
    by_priority = {p.value: 0 for p in Priority}

    for status, count in db.execute(select(Task.status, func.count()).group_by(Task.status)):
        by_status[status.value] = count
    for priority, count in db.execute(select(Task.priority, func.count()).group_by(Task.priority)):
        by_priority[priority.value] = count

    overdue = db.scalar(
        select(func.count()).select_from(Task).where(
            Task.due_date < date.today(), Task.status != Status.completed
        )
    )
    return {
        "total": sum(by_status.values()),
        "overdue": overdue or 0,
        "by_status": by_status,
        "by_priority": by_priority,
    }
