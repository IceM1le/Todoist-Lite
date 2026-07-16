from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class TaskCreate(BaseModel):
    title: str = Field(..., max_length=100)
    description: str = Field(..., max_length=255)
    priority: int = Field(default=2, ge=1, le=4)
    is_done: bool = Field(default=False)
    due_date: datetime = Field(default=None)

    @field_validator('due_date', mode='before')
    @classmethod
    def ensure_timezone(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            try:
                v = datetime.fromisoformat(v)
            except ValueError:
                raise ValueError('Invalid datetime format. Use ISO 8601, e.g. "YYYY-MM-DDThh:mm:ss"')
        if v.tzinfo is None:
            return v.replace(tzinfo=timezone.utc)
        return v.astimezone(timezone.utc)


class TaskPatch(BaseModel):
    title: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    priority: Optional[int] = Field(None, ge=1, le=4)
    is_done: Optional[bool] = Field(None)
    due_date: Optional[datetime] = Field(None)


class TaskResponse(TaskCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    owner_id: int

class PaginatedTaskResponse(BaseModel):
    items: List[TaskResponse]
    total: int
    page: int
    limit: int
    pages: int