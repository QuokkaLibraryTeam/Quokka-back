from pydantic import BaseModel, ConfigDict, model_validator, conint
from typing import Optional
from uuid import UUID
from datetime import datetime

class ReportCreate(BaseModel):
    # 1 이상의 정수만 허용, 기본값 None
    story_id: Optional[conint(gt=0)]   = None
    comment_id: Optional[conint(gt=0)] = None
    reason: str

    @model_validator(mode="after")
    def check_one_target(self):
        # 둘 다 None 이거나 둘 다 값이 있을 수 없도록
        if (self.story_id is None) == (self.comment_id is None):
            raise ValueError("story_id 또는 comment_id 중 하나만 제공해야 합니다.")
        return self

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