from __future__ import annotations
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, ForeignKey, Column

from db.base import Base


class Story(Base):
    __tablename__ = "stories"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = Column(Integer, ForeignKey("users.id"))
    user: Mapped[str] = relationship("User", back_populates="stories")

    title: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        default=None,
        onupdate=datetime.utcnow,
        nullable=True
    )

    scenes: Mapped[List["Scene"]] = relationship(
        back_populates="story",
        order_by="(Scene.order_idx, Scene.id)",
        cascade="all, delete-orphan",
    )

    comments: Mapped[List["Comment"]] = relationship(
        back_populates="story",
        cascade="all, delete-orphan",
    )

    likes: Mapped[List["Like"]] = relationship(
        back_populates="story",
        cascade="all, delete-orphan",
    )

    shares: Mapped[List["Share"]] = relationship(
        back_populates="story",
        cascade="all, delete-orphan",
    )