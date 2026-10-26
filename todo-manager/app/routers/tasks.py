"""HTTP endpoints for tasks."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db
from ..models import Priority, Status

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def _get_or_404(db: Session, task_id: int):
    task = crud.get_task(db, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    return task


@router.post("", response_model=schemas.TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(data: schemas.TaskCreate, db: Session = Depends(get_db)):
    """Create a new task."""
    return crud.create_task(db, data)


@router.get("", response_model=schemas.TaskList)
def list_tasks(
    status: Optional[Status] = Query(None, description="Filter by status"),
    priority: Optional[Priority] = Query(None, description="Filter by priority"),
    q: Optional[str] = Query(None, description="Search in title and description"),
    overdue: Optional[bool] = Query(None, description="true = only overdue tasks"),
    sort_by: schemas.SortField = schemas.SortField.created_at,
    order: schemas.SortOrder = schemas.SortOrder.desc,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List tasks with filtering, search, sorting and pagination."""
    total, items = crud.list_tasks(db, status, priority, q, overdue, sort_by, order, limit, offset)
    return {"total": total, "limit": limit, "offset": offset, "items": items}


# NOTE: must be declared before "/{task_id}" so "stats" isn't parsed as an ID.
@router.get("/stats", response_model=schemas.TaskStats)
def task_stats(db: Session = Depends(get_db)):
    """Summary counts by status and priority, plus number of overdue tasks."""
    return crud.get_stats(db)


@router.get("/{task_id}", response_model=schemas.TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Get a single task by ID."""
    return _get_or_404(db, task_id)


@router.patch("/{task_id}", response_model=schemas.TaskOut)
def update_task(task_id: int, data: schemas.TaskUpdate, db: Session = Depends(get_db)):
    """Partially update a task. Send only the fields you want to change."""
    task = _get_or_404(db, task_id)
    return crud.update_task(db, task, data)


@router.post("/{task_id}/complete", response_model=schemas.TaskOut)
def complete_task(task_id: int, db: Session = Depends(get_db)):
    """Shortcut: mark a task as completed."""
    task = _get_or_404(db, task_id)
    return crud.update_task(db, task, schemas.TaskUpdate(status=Status.completed))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Delete a task."""
    task = _get_or_404(db, task_id)
    crud.delete_task(db, task)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
