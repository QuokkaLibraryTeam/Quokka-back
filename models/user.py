from __future__ import annotations
from datetime import datetime
from typing import List, Optional
import uuid

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import String, Integer, DateTime, ForeignKey
from db.base import Base

class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    google_id: Mapped[str] = mapped_column(String(64), index=True)
    nickname: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    stories: Mapped[List["Story"]] = relationship("Story", back_populates="user", cascade="all, delete-orphan")
    comments: Mapped[List['Comment']] = relationship("Comment", back_populates="user", cascade="all, delete-orphan")
    likes: Mapped[List['Like']] = relationship("Like", back_populates="user", cascade="all, delete-orphan")
    shares: Mapped[List['Share']] = relationship("Share", back_populates="user", cascade="all, delete-orphan")
    reports: Mapped[List['Report']] = relationship("Report", back_populates="reporter", cascade="all, delete-orphan")