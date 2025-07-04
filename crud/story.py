# crud/story.py
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from crud.base import CRUDBase
from models.story import Story
from schemas.story import (
    StoryCreate,  # title
    StoryUpdate,  # title | None
)


class CRUDStory(CRUDBase[Story, StoryCreate, StoryUpdate]):
    def create_story(
            self,
            db: Session,
            obj_in: StoryCreate,
            user_id: str,
    ) -> Story:
        story = Story(user_id=user_id, title=obj_in.title)
        db.add(story)
        db.commit()
        db.refresh(story)
        return story

    def get_by_user(
            self,
            db: Session,
            user_id: str,
            *,
            skip: int = 0,
            limit: int = 100,
    ) -> List[Story]:
        return (
            db.query(Story)
            .filter(Story.user_id == user_id)
            .order_by(Story.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_with_scenes(
            self,
            db: Session,
            id: int,
    ) -> Optional[Story]:
        return (
            db.query(Story)
            .options(joinedload(Story.scenes))
            .filter(Story.id == id)
            .first()
        )


# 싱글턴 인스턴스
story_crud = CRUDStory(Story)
