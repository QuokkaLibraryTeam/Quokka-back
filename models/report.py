from __future__ import annotations
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.ext.hybrid import hybrid_property
from db.base import Base

class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    # 신고 대상에 따라 동화나 리뷰 둘 중 하나의 필드만 채워짐
    story_id: Mapped[Optional[int]] = mapped_column(ForeignKey("stories.id"), nullable=True)
    comment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("comments.id"), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    reporter: Mapped["User"] = relationship("User", back_populates="reports")
    story: Mapped[Optional["Story"]] = relationship("Story", back_populates="reports")
    comment: Mapped[Optional["Comment"]] = relationship("Comment", back_populates="reports")

    @hybrid_property
    def target_type(self) -> str:
        if self.story_id is not None:
            return "Story"
        if self.comment_id is not None:
            return "Comment"
        return "Unknown"