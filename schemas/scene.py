from __future__ import annotations
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class SceneBase(BaseModel):
    text: str = Field(..., description="장면(씬)의 본문")
    image_url: Optional[str] = Field(None, description="관련 이미지 URL")

class SceneCreate(SceneBase):
    """새 씬 추가용 입력 DTO"""
    pass

class SceneUpdate(BaseModel):
    text: Optional[str] = None
    image_url: Optional[str] = None