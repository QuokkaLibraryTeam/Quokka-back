
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class LikeCreate(BaseModel):
    story_id: int


class LikeOut(BaseModel):
    story_id: int
    user_id: uuid.UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class LikeCount(BaseModel):
    story_id: int
    likes: int

class LikeFilter(BaseModel):
    story_id: int
    user_id: uuid.UUID