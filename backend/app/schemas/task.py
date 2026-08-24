from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"

class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Short summary of the task")
    description: Optional[str] = Field(None, max_length=2000, description="Detailed explanation of the task")

class TaskCreate(TaskBase):
    pass

class TaskResponse(TaskBase):
    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
