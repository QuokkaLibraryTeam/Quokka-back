from fastapi import APIRouter, Depends, HTTPException, Request
from starlette import status

from core.chat_manager import new_session
from core.security import verify_token, decode_token
from schemas.story import StoryOut, StoriesOut, StoryOutWithDetail
from sevices.story import create_new_story, get_all_story, check_story_auth, get_story_by_story_id

router = APIRouter()

@router.get("/{story_id}/chat")
async def init_chat(request: Request, story_id: int, user_id: str = Depends(verify_token)):
    db = request.state.db
    if not get_story_by_story_id(db, story_id).original and not check_story_auth(db, story_id, user_id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    session_key = await new_session(user_id, story_id)
    return {"session_key": session_key}

@router.get("/originals", response_model=StoriesOut)
def get_originals(request: Request):
    db = request.state.db
    stories = get_all_story(db)
    resp = [story for story in stories if story.original]
    return {"stories": resp}

@router.get("/", response_model=StoriesOut)
def list_stories(request: Request):
    db = request.state.db
    stories = get_all_story(db)
    return {"stories": stories}
