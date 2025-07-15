import re
from typing import Tuple, List

from sqlalchemy.orm import Session

from crud.story import story_crud
from models.story import Story
from schemas.story import StoryCreate, StoryFilter


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

def get_all_story_by_filter(db: Session, filters: StoryFilter):
    stories = story_crud.get_multi_filtered(db, filter=filters)
    return stories

def get_all_stories_by_user_id(db: Session,user_id : str):
    stories = story_crud.get_all_by_user(db, user_id)
    return stories

def check_story_auth(db: Session, story_id: int, user_id: str):
    story = story_crud.get(db,story_id)
    if story is None:
        return False
    return str(story.user_id) == user_id

def get_story_by_story_id(db: Session, story_id: int):
    story = story_crud.get(db,story_id)
    if story is None:
        return False
    return story

def delete_story_by_story_id(db: Session, story_id: int):
    story = story_crud.get(db,story_id)
    if story is None:
        return False
    story_crud.remove(db,story_id)
    return True