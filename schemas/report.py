from pydantic import BaseModel, ConfigDict, root_validator, conint
from typing import Optional
from uuid import UUID
from datetime import datetime

class ReportCreate(BaseModel):
    story_id: Optional[conint(gt=0)] = None
    comment_id: Optional[conint(gt=0)] = None
    reason: str

    @root_validator
    def check_one_target(cls, values):
        sid, cid = values.get("story_id"), values.get("comment_id")
        if (sid is None and cid is None) or (sid is not None and cid is not None):
            raise ValueError("story_id 또는 comment_id 중 하나만 제공해야 합니다.")
        return values

    class Config:
        model_config = ConfigDict(from_attributes=True)

class ReportOut(BaseModel):
    id: int
    reporter_id: UUID
    story_id: Optional[int]
    comment_id: Optional[int]
    reason: str
    created_at: datetime

    class Config:
        model_config = ConfigDict(from_attributes=True)