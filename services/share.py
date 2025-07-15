from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from crud.share import share_crud
from crud.story import story_crud
from schemas.share import ShareCreate, ShareOut, TagsUpdate


# ── 내부 util ─────────────────────────────────────────
def _clean(tags: List[str]) -> List[str]:
    clean = [t.strip() for t in tags if t.strip()]
    if not clean:
        raise ValueError("태그를 1개 이상 입력하세요.")
    return clean


# ── C ────────────────────────────────────────────────
def publish(db: Session, *, story_id: int, user_id: str, data: ShareCreate) -> ShareOut:
    # 소유권 확인
    if not story_crud.get_one_filtered(db, filters=ShareCreate(tags=[]), id=story_id, user_id=user_id):
        raise PermissionError("Story not found or access denied")

    tags = _clean(data.tags)

    existing = share_crud.get_one_filtered(db, filters=ShareCreate(tags=[]),
                                           story_id=story_id, user_id=user_id)
    if existing:               # 이미 공유된 경우 → 태그 교체
        existing.tags = tags
        db.commit(); db.refresh(existing)
        return ShareOut.model_validate(existing)

    new = share_crud.create(db, obj_in=data,
                            user_id=user_id, story_id=story_id,
                            tags=tags, created_at=datetime.utcnow())
    return ShareOut.model_validate(new)


# ── U (PATCH) ────────────────────────────────────────
def patch_tags(db: Session, *, story_id: int, user_id: str, data: TagsUpdate) -> ShareOut:
    share = share_crud.get_one_filtered(db, filters=ShareCreate(tags=[]),
                                        story_id=story_id, user_id=user_id)
    if not share:
        raise PermissionError("Shared story not found or access denied")

    clean = _clean(data.tags)

    if data.operation == "replace":
        share.tags = clean
    elif data.operation == "add":
        share.tags = list(dict.fromkeys(share.tags + clean))
    elif data.operation == "remove":
        share.tags = [t for t in share.tags if t not in set(clean)]

    db.commit(); db.refresh(share)
    return ShareOut.model_validate(share)


# ── D ────────────────────────────────────────────────
def unpublish(db: Session, *, story_id: int, user_id: str):
    share = share_crud.get_one_filtered(db, filters=ShareCreate(tags=[]),
                                        story_id=story_id, user_id=user_id)
    if not share:
        raise PermissionError("Shared story not found or access denied")
    share_crud.remove(db, id=share.id)


# ── R ────────────────────────────────────────────────
def all_tags(db: Session):
    return share_crud.distinct_tags(db)

def is_shared(db: Session, story_id: int) -> bool:
    return share_crud.get_one_filtered(db, filters=ShareCreate(tags=[]),
                                       story_id=story_id) is not None

def list_shared(db: Session, tag: Optional[str] = None):
    return share_crud.filter_by_tag(db, tag) if tag else share_crud.get_all(db)

def get_shared(db: Session, story_id: int):
    share = share_crud.get_one_filtered(db, filters=ShareCreate(tags=[]), story_id=story_id)
    if not share:
        raise ValueError("Shared story not found")
    return share
