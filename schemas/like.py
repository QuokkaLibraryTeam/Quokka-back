from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class ReportCreate(BaseModel):
    story_id: Optional[UUID]
    comment_id: Optional[int]
    reason: str
