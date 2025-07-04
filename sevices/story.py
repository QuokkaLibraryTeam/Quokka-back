from sqlalchemy.orm import Session

from crud.story import story_crud
from models.story import Story
from schemas.story import StoryCreate


def create_new_story(
        db: Session,
        user_id: str,
        title: str,
) -> Story:
    story_in = StoryCreate(title=title)
    story = story_crud.create_story(
        db=db,
        obj_in=story_in,
        user_id=user_id,
    )
    return story


def get_all_story(db: Session):
    stories = story_crud.get_all(db)
    return stories
