import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from crud.like import like_crud
from crud.story import story_crud
from schemas.like import LikeCreate, LikeFilter


# ── C ────────────────────────────────────────────────
def add_like(db: Session, *, story_id: int, user_id: uuid.UUID) -> None:
    # 스토리 존재 검증
    if not story_crud.get(db, id=story_id):
        raise ValueError("Story not found")

    # 중복 좋아요 방지
    if like_crud.get_one_filtered(
        db, filters=LikeFilter(story_id=story_id,user_id=user_id),  # story_id 필터만
    ):
        raise ValueError("이미 좋아요를 눌렀습니다")

    like_crud.create(
        db,
        obj_in=LikeCreate(story_id=story_id),
        user_id=user_id,
        created_at=datetime.utcnow(),
    )


# ── D ────────────────────────────────────────────────
def remove_like(db: Session, *, story_id: int, user_id: uuid.UUID) -> None:
    like = like_crud.get_one_filtered(db, filters=LikeFilter(story_id=story_id,user_id=user_id))
    if not like or str(like.user_id) != user_id:
        raise ValueError("좋아요를 누른 적이 없습니다")
    like_crud.remove(db, id=like.id)


# ── R ────────────────────────────────────────────────
def count_likes(db: Session, *, story_id: int) -> int:
    return db.query(like_crud.model).filter_by(story_id=story_id).count()


def has_liked(db: Session, *, story_id: int, user_id: str) -> bool:
    return (
        db.query(like_crud.model)
        .filter_by(story_id=story_id, user_id=user_id)
        .count()
        > 0
    )
