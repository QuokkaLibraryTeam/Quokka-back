from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from schemas.scene import SceneCreate


class StoryBase(BaseModel):
    title: str

class StoryCreate(StoryBase):
    pass

class StoryUpdate(BaseModel):
    title: Optional[str] = None   # 제목만 부분 수정  # 전체 교체 or None


class SceneOut(BaseModel):
    id: int
    order_idx: int
    text: str

    class Config:
        orm_mode = True

class StoryOut(BaseModel):
    id: int
    user_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    scenes: List[SceneOut]

    class Config:
        orm_mode = True

class StorysOut(BaseModel):
    stories : List[StoryOut]

    class Config:
        orm_mode = True