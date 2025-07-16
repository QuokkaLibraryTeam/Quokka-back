# crud/share.py
from typing import List
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from crud.base import CRUDBase
from models.share import Share
from schemas.share import ShareCreate, ShareCreate, ShareOut  # Update 스키마 없음

class CRUDShare(CRUDBase[Share, ShareCreate, ShareCreate]):
    def distinct_tags(self, db: Session) -> List[str]:
        rows = db.query(func.unnest(Share.tags).label("tag")).distinct().all()
        return [row.tag for row in rows]

    def filter_by_tag(self, db: Session, tag: str):
        return db.query(Share).filter(Share.tags.any(tag)).all()

    def get_with_story(self, db: Session, share_id: int) -> ShareOut:
        share = (
            db.query(Share)
            .options(joinedload(Share.story))
            .filter(Share.id == share_id)
            .first()
        )

        if not share:
            raise ValueError("해당 공유 항목을 찾을 수 없습니다.")

        return ShareOut.model_validate(share)

share_crud = CRUDShare(Share)


