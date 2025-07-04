from fastapi import APIRouter, Request, Depends

from core.security import verify_token
from schemas.story import StorysOut, StoryOutWithDetail
from sevices.story import get_all_story, get_all_stories_by_user_id, create_new_story

router = APIRouter()

@router.get("/me/stories",response_model=StorysOut)
def list_stories_by_user(request: Request,user_id: str = Depends(verify_token)):
    db = request.state.db
    stories = get_all_stories_by_user_id(db,user_id)
    return {"stories" : stories}

@router.post("/me/stories", response_model=StoryOutWithDetail)
def init_story(request: Request, title: str, user_id: str = Depends(verify_token)):
    db = request.state.db
    story = create_new_story(db, user_id, title)
    return story