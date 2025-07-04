import re
from typing import Tuple, List

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

def get_all_stories_by_user_id(db: Session,user_id : str):
    stories = story_crud.get_all_by_user(db, user_id)
    return stories

def check_story_auth(db: Session, story_id: int, user_id: str):
    story = story_crud.get(db,story_id)
    if story is None:
        return False
    return story.user_id == user_id


_QUESTION_RE = re.compile(r"QUESTION:\s*(.+)", re.I)
_EXAMPLE_RE = re.compile(r"^\s*[-–]\s*(.+)", re.M)

def parse_q_examples(text: str) -> Tuple[str, List[str]]:
    q_match = _QUESTION_RE.search(text)
    question = q_match.group(1).strip() if q_match else text.strip()
    examples = _EXAMPLE_RE.findall(text)[:4]
    return question, examples