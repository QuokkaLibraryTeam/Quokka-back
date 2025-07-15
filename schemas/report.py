
import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, model_validator, ConfigDict


class ReportCreate(BaseModel):
    story_id: Optional[int] = None
    comment_id: Optional[int] = None
    reason: str = Field(..., min_length=1, max_length=300)

    @model_validator(mode="after")
    def _check_target(cls, values):
        if not values.get("story_id") and not values.get("comment_id"):
            raise ValueError("story_id 또는 comment_id 중 하나는 반드시 필요합니다.")
        return values

    model_config = ConfigDict(from_attributes=True)


class ReportOut(BaseModel):
    id: int
    reporter_id: uuid.UUID
    story_id: Optional[int]
    comment_id: Optional[int]
    reason: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)