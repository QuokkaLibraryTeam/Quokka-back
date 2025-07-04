from fastapi import APIRouter, Depends, HTTPException, Request
from starlette import status

from core.chat_manager import new_session
from core.security import verify_token, decode_token
from main import app
from schemas.story import StoryOut, StorysOut
from sevices.story import create_new_story, get_all_story

router = APIRouter()


@router.get("/{story_id}/chat")
def init_chat(story_id: int, user_id: str = Depends(verify_token)):
    session_key = new_session(user_id, story_id)
    return {"session_key": session_key}


@router.post("/", response_model=StoryOut)
def init_story(request: Request, title: str, user_id: str = Depends(verify_token)):
    db = request.state.db
    story = create_new_story(db, user_id, title)
    return story

@router.get("/",response_model=StorysOut)
def list_stories(request: Request):
    db = request.state.db
    stories = get_all_story(db)
    return {"stories" : stories}
