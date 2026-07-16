from datetime import datetime

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(..., max_length=100)
    description: str = Field(..., max_length=255)
    priority: int = Field(default=2, ge=1, le=4)
    is_done: bool = Field(default=False)
    due_date: datetime = Field(default=None)


class TaskPatch(BaseModel):
    priority: int = Field(default=2, ge=1, le=4)
    is_done: bool = Field(default=False)
    due_date: datetime = Field(default=None)


class TaskResponse(TaskCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    owner_id: int
