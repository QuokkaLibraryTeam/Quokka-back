from __future__ import annotations
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from db.base import Base

from story import Story
from user import User

class Share(Base):
    __tablename__ = "shares"

    id: Mapped[int] = mapped_column(primary_key=True)
    story_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("stories.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    story: Mapped[Story] = relationship("Story", back_populates="shares")
    user: Mapped[User] = relationship("User", back_populates="shares")