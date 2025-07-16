from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Body
from starlette import status

from api.v1.endpoints.story import comments, likes, shares
from core.chat_manager import new_session
from core.security import verify_token, optional_user_id
from schemas.story import StoriesOut, StoryFilter, StoryOutWithDetail
from services.share import is_shared
from services.story import check_story_auth, get_story_by_story_id, \
    get_all_story_by_filter, delete_story_by_story_id, create_new_story

router = APIRouter()
router.include_router(comments.router, tags=["comment"])
router.include_router(likes.router, tags=["like"])
router.include_router(shares.router, tags=["share"])

@router.get("/{story_id}/chat",tags=["story"])
async def open_chat_ws(request: Request, story_id: int, user_id: str = Depends(verify_token)):
    db = request.state.db
    if not get_story_by_story_id(db, story_id).original and not check_story_auth(db, story_id, user_id):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    session_key = await new_session(user_id, story_id)
    return {"session_key": session_key}


@router.get("/", response_model=StoriesOut,tags=["story"])
def list_stories(request: Request, filters: StoryFilter = Depends()):
    db = request.state.db
    stories = get_all_story_by_filter(db, filters)
    return {"stories": stories}

@router.get("/{story_id}", response_model=StoryOutWithDetail,tags=["story"])
def get_story(
    request: Request,
    story_id: int,
    user_id: Optional[str] = Depends(optional_user_id),
):
    db = request.state.db

    story = get_story_by_story_id(db, story_id)
    if story is None:
        raise HTTPException(status_code=404, detail="Story not found")

    if is_shared(db, story_id):
        return story

    if user_id is None or str(story.user_id) != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied for private story"
        )
    print(story)
    return story

@router.delete("/{story_id}",tags=["story"])
def delete_story(story_id:int,request: Request, user_id: str = Depends(verify_token)):
    db = request.state.db
    if not check_story_auth(db, story_id, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="해당 스토리에 접근할 권한이 없습니다."
        )
    return delete_story_by_story_id(db, story_id)

@router.post("", response_model=StoryOutWithDetail,tags=["story"])
def init_story(request: Request, title: str = Body(..., embed=True), user_id: str = Depends(verify_token)):
    db = request.state.db
    story = create_new_story(db, user_id, title)
    return story