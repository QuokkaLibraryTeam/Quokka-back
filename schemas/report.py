from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class ReportCreate(BaseModel):
    story_id: Optional[UUID]
    comment_id: Optional[int]
    reason: str

class ReportOut(BaseModel):
    id: int
    reporter_id: UUID
    story_id: Optional[UUID]
    comment_id: Optional[int]
    reason: str
    created_at: datetime

    class Config:
        orm_mode = True