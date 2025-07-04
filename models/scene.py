from __future__ import annotations        # forward-ref 타이핑
from datetime import datetime
from typing import List

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, ForeignKey

from db.base import Base

class Scene(Base):
    __tablename__ = "scenes"
    id:        Mapped[int] = mapped_column(primary_key=True)
    story_id:  Mapped[int] = mapped_column(ForeignKey("stories.id", ondelete="CASCADE"))
    order_idx: Mapped[int] = mapped_column(Integer)   # 0,1,2… 계속 증가
    text:      Mapped[str] = mapped_column(String)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at = mapped_column(default=datetime.utcnow)

    story: Mapped["Story"] = relationship(back_populates="scenes")