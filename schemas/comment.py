from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ── 공통 ──────────────────────────────────────────────
class _CommentBase(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)


# ── 입력용 ────────────────────────────────────────────
class CommentCreate(_CommentBase):
    story_id: int


class CommentUpdate(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)


# ── 출력용 ────────────────────────────────────────────
class CommentOut(_CommentBase):
    id: int
    story_id: int
    user_nickname: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
