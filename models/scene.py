from __future__ import annotations
from datetime import datetime
from typing import List

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, DateTime, ForeignKey, Sequence

from db.base import Base

order_idx_seq = Sequence('scene_order_idx_seq', start=0, increment=1,minvalue=0)


class Scene(Base):
    __tablename__ = "scenes"

    id: Mapped[int] = mapped_column(primary_key=True)
    story_id: Mapped[int] = mapped_column(ForeignKey("stories.id", ondelete="CASCADE"))
    order_idx: Mapped[int] = mapped_column(
        Integer,
        order_idx_seq,
        server_default=order_idx_seq.next_value(),
        nullable=False
    )
    text: Mapped[str] = mapped_column(String)
    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False
    )

    story: Mapped["Story"] = relationship(back_populates="scenes")
