# schemas/share.py
from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict
from schemas.story import StoryOutWithDetail


class ShareCreate(BaseModel):
    tags: List[str]

    model_config = ConfigDict(from_attributes=True)


class ShareOut(BaseModel):
    id: int
    story: StoryOutWithDetail   # 퍼블리시된 동화 상세
    tags: List[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
