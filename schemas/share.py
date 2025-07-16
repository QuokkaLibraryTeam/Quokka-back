import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from schemas.story import StoryOutWithDetail


class ShareCreate(BaseModel):
    tags: List[str]
    model_config = ConfigDict(from_attributes=True)

class TagsUpdate(BaseModel):
    tags: List[str]
    model_config = ConfigDict(from_attributes=True)

class ShareOut(BaseModel):
    id: int
    stories: StoryOutWithDetail
    tags: List[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ShareFilter(BaseModel):
    story_id: Optional[int] = None
    user_id: Optional[uuid.UUID] = None