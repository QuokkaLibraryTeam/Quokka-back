from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List

from schemas.story import StoryOutWithDetail

class ShareCreate(BaseModel):
    tags: List[str]
    model_config = ConfigDict(from_attributes=True)

class TagsUpdate(BaseModel):
    tags: List[str]
    model_config = ConfigDict(from_attributes=True)

class ShareOut(BaseModel):
    id: int
    story: StoryOutWithDetail
    tags: List[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
