from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class CommentCreate(BaseModel):
    story_id: UUID
    text: str

class CommentOut(BaseModel):
    id: int
    story_id: UUID
    user_id: UUID
    text: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class CommentUpdate(BaseModel):
    text: str