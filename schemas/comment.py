from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID

class CommentCreate(BaseModel):
    story_id: int
    text: str

class CommentOut(BaseModel):
    id: int
    story_id: int
    user_id: UUID
    text: str
    created_at: datetime
    updated_at: datetime

    class Config:
        model_config = ConfigDict(from_attributes=True)

class CommentUpdate(BaseModel):
    text: str