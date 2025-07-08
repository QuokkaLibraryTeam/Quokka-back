from fastapi import APIRouter, Request, Depends, Path, HTTPException
from starlette import status

from core.security import verify_token
from schemas.story import StoryOutWithDetail, StoriesOut
from sevices.story import get_all_story, get_all_stories_by_user_id, create_new_story, get_story_by_story_id, \
    delete_story_by_story_id, check_story_auth

router = APIRouter()

@router.get("/me/stories",response_model=StoriesOut)
def list_stories_by_user(request: Request,user_id: str = Depends(verify_token)):
    db = request.state.db
    stories = get_all_stories_by_user_id(db,user_id)
    return {"stories" : stories}

@router.post("/me/stories", response_model=StoryOutWithDetail)
def init_story(request: Request, title: str, user_id: str = Depends(verify_token)):
    db = request.state.db
    story = create_new_story(db, user_id, title)
    return story

@router.get("/me/stories/{story_id}", response_model=StoryOutWithDetail)
def get_story(story_id:int, request: Request, user_id: str = Depends(verify_token)):
    db = request.state.db
    if not check_story_auth(db, story_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 스토리에 접근할 권한이 없습니다."
        )
    story = get_story_by_story_id(db, story_id)
    return story

@router.delete("/me/stories/{story_id}")
def delete_story(story_id:int,request: Request, user_id: str = Depends(verify_token)):
    db = request.state.db
    if not check_story_auth(db, story_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 스토리에 접근할 권한이 없습니다."
        )
    return delete_story_by_story_id(db, story_id)


