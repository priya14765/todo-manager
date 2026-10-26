"""Pydantic schemas: request validation and response shapes."""
import enum
from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator

from .models import Priority, Status


class SortField(str, enum.Enum):
    created_at = "created_at"
    due_date = "due_date"
    title = "title"
    priority = "priority"


class SortOrder(str, enum.Enum):
    asc = "asc"
    desc = "desc"


def _clean_title(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("title cannot be blank")
    return value


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=100, examples=["Finish internship project"])
    description: Optional[str] = Field(None, max_length=1000)
    priority: Priority = Priority.medium
    status: Status = Status.pending
    due_date: Optional[date] = Field(None, description="Format: YYYY-MM-DD")

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: str) -> str:
        return _clean_title(v)

    @field_validator("due_date")
    @classmethod
    def due_date_not_in_past(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v < date.today():
            raise ValueError("due_date cannot be in the past")
        return v


class TaskUpdate(BaseModel):
    """All fields optional: send only what you want to change (PATCH)."""

    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    priority: Optional[Priority] = None
    status: Optional[Status] = None
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, v: Optional[str]) -> Optional[str]:
        return _clean_title(v) if v is not None else v


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str]
    priority: Priority
    status: Status
    due_date: Optional[date]
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def is_overdue(self) -> bool:
        return (
            self.due_date is not None
            and self.status != Status.completed
            and self.due_date < date.today()
        )


class TaskList(BaseModel):
    total: int
    limit: int
    offset: int
    items: List[TaskOut]


class TaskStats(BaseModel):
    total: int
    overdue: int
    by_status: dict
    by_priority: dict
