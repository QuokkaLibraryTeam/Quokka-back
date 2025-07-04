from __future__ import annotations
from datetime import datetime
from typing import List

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, ForeignKey

from db.base import Base

class Story(Base):
    __tablename__ = "stories"
    id:       Mapped[int]  = mapped_column(primary_key=True)
    user_id:  Mapped[str]  = mapped_column(String(64), index=True)
    title:    Mapped[str]  = mapped_column(String(255))
    created_at = mapped_column(default=datetime.utcnow)
    updated_at = mapped_column(onupdate=datetime.utcnow)
    # 1:N
    scenes: Mapped[list["Scene"]] = relationship(
        back_populates="story",
        order_by="(Scene.order_idx, Scene.id)",
        cascade="all, delete-orphan",
    )