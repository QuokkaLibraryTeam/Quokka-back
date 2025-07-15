from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from crud.comment import comment_crud
from crud.story import story_crud
from schemas.comment import CommentCreate, CommentUpdate, CommentOut


# ── C ────────────────────────────────────────────────────────────────
def create_comment(db: Session, *, data: CommentCreate, user_id: str) -> CommentOut:
    if not story_crud.get(db, id=data.story_id):
        raise ValueError("Story not found")

    db_comment = comment_crud.create(
        db,
        obj_in=data,
        user_id=user_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    return db_comment


# ── R ────────────────────────────────────────────────────────────────
def get_comments_by_story(db: Session, *, story_id: int) -> List[CommentOut]:
    if not story_crud.get(db, id=story_id):
        raise ValueError("Story not found")
    comments = comment_crud.get_multi_filtered(
        db,
        filters=CommentCreate(story_id=story_id, text=""),
        skip=0,
        limit=1000,
    )
    comments.sort(key=lambda c: c.updated_at)
    return comments


# ── U ────────────────────────────────────────────────────────────────
def update_comment(
        db: Session, *, comment_id: int, data: CommentUpdate, user_id: str
) -> CommentOut:
    db_comment = comment_crud.get(db, id=comment_id)
    if not db_comment:
        raise ValueError("Comment not found")
    if str(db_comment.user_id) != user_id:
        raise PermissionError("Forbidden")

    db_comment = comment_crud.update(
        db, db_obj=db_comment, obj_in=data.copy(update={"updated_at": datetime.utcnow()})
    )
    return db_comment


# ── D ────────────────────────────────────────────────────────────────
def delete_comment(db: Session, *, comment_id: int, user_id: str) -> None:
    db_comment = comment_crud.get(db, id=comment_id)
    if not db_comment:
        raise ValueError("Comment not found")
    if str(db_comment.user_id) != user_id:
        raise PermissionError("Forbidden")
    comment_crud.remove(db, id=comment_id)
