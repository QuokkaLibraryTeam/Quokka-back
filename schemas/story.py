from __future__ import annotations

import uuid
from datetime import datetime
from typing import List, Optional, TypedDict

from pydantic import BaseModel, Field, ConfigDict


class StoryBase(BaseModel):
    title: str


class StoryCreate(StoryBase):
    pass


class StoryUpdate(BaseModel):
    title: Optional[str] = None


class SceneOut(BaseModel):
    id: int
    order_idx: int
    text: str
    image_url : str

    # Pydantic v2: ORM 모델의 속성 기반 매핑 허용
    model_config = ConfigDict(from_attributes=True)


class StoryOutWithDetail(BaseModel):
    id: int
    user_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: Optional[datetime]
    scenes: List[SceneOut]

    model_config = ConfigDict(from_attributes=True)


class StoryOut(BaseModel):
    id: int
    model_config = ConfigDict(from_attributes=True)


class StoriesOut(BaseModel):
    stories: List[StoryOut]
    model_config = ConfigDict(from_attributes=True)


class StoriesOutWithDetail(BaseModel):
    stories: List[StoryOutWithDetail]
    model_config = ConfigDict(from_attributes=True)

class ClientStart(TypedDict):
    type: str
    text: str


class ClientAnswer(TypedDict):
    type: str
    text: str


class ClientChoice(TypedDict):
    type: str
    text: int


class ClientCmd(TypedDict):
    type: str

class StoryFilter(BaseModel):
    original: Optional[bool] = Field(
        False,description="기존 전래동화 여부"
    )
