from fastapi import APIRouter, Depends, HTTPException, Request
from starlette import status

from core.chat_manager import new_session
from core.security import verify_token, decode_token
from main import app
from schemas.story import StoryOut, StorysOut, StoryOutWithDetail
from sevices.story import create_new_story, get_all_story, check_story_auth

router = APIRouter()


@router.post("/{story_id}/chat")
def init_chat(request: Request, story_id: int, user_id: str = Depends(verify_token)):
    db = request.state.db
    if not check_story_auth(db, story_id, user_id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    session_key = new_session(user_id, story_id)
    return {"session_key": session_key}


@router.get("/", response_model=StorysOut)
def list_stories(request: Request):
    db = request.state.db
    stories = get_all_story(db)
    return {"stories": stories}
