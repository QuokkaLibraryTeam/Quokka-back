from typing import List

from requests import Session
from sqlalchemy.orm import joinedload

from crud.base import CRUDBase
from models.comment import Comment
from schemas.comment import CommentCreate, CommentUpdate, CommentOut


class CRUDComment(CRUDBase[Comment, CommentCreate, CommentUpdate]):
    def get_multi_filtered(
            self,
            db: Session,
            filters,
            *,
            skip: int = 0,
            limit: int = 100,
    ) -> List[CommentOut]:
        query = db.query(self.model).options(joinedload(Comment.user))
        query = self._apply_filters(query, filters)
        results = query.offset(skip).limit(limit).all()

        return [
            CommentOut(
                id=comment.id,
                text=comment.text,
                user_nickname=comment.user.nickname,
                story_id=comment.story_id,
                created_at=comment.created_at,
                updated_at=comment.updated_at,
            )
            for comment in results
        ]

comment_crud = CRUDComment(Comment)
