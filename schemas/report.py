from pydantic import BaseModel, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime

class ReportCreate(BaseModel):
    story_id: Optional[int]
    comment_id: Optional[int]
    reason: str

class ReportOut(BaseModel):
    id: int
    reporter_id: UUID
    story_id: Optional[int]
    comment_id: Optional[int]
    reason: str
    created_at: datetime

    class Config:
        model_config = ConfigDict(from_attributes=True)