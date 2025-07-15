# crud/share.py
from typing import List
from sqlalchemy import func
from sqlalchemy.orm import Session

from crud.base import CRUDBase
from models.share import Share
from schemas.share import ShareCreate, ShareCreate  # Update 스키마 없음

class CRUDShare(CRUDBase[Share, ShareCreate, ShareCreate]):
    def distinct_tags(self, db: Session) -> List[str]:
        rows = db.query(func.unnest(Share.tags).label("tag")).distinct().all()
        return [row.tag for row in rows]

    def filter_by_tag(self, db: Session, tag: str):
        return db.query(Share).filter(Share.tags.any(tag)).all()

share_crud = CRUDShare(Share)


