from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from sqlalchemy import Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[int] = mapped_column(primary_key=True)
    story_id: Mapped[int] = mapped_column(ForeignKey("stories.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    stories: Mapped["Story"] = relationship("Story", back_populates="comments")
    user: Mapped["User"] = relationship("User", back_populates="comments")
    reports: Mapped[List["Report"]] = relationship("Report", back_populates="comment", cascade="all, delete-orphan")
