from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

class SceneBase(BaseModel):
    text: str = Field(..., description="장면(씬)의 본문")
    story_id: int = Field(..., description="스토리 ID")
    image_url: Optional[str] = Field(None, description="관련 이미지 URL")

    model_config = ConfigDict(extra="ignore")


class SceneCreate(SceneBase):
    """새 씬 추가용 입력 DTO"""
    pass


class SceneUpdate(BaseModel):
    text: Optional[str] = Field(None, description="장면(씬)의 본문")
    image_url: Optional[str] = Field(None, description="관련 이미지 URL")

    model_config = ConfigDict(extra="ignore")
