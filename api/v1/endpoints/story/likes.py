from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from core.security import verify_token
from db.base import get_db
from schemas.like import LikeCount
from services.like import add_like, remove_like, count_likes, has_liked

router = APIRouter()


# ── POST ───────────────────
@router.post("/{story_id}/likes", status_code=status.HTTP_201_CREATED)
def like_story(
        request: Request,
        story_id: int,
        user_id: str = Depends(verify_token),
):
    db = request.state.db
    try:
        add_like(db, story_id=story_id, user_id=user_id)
        return {"message": "좋아요가 등록되었습니다."}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── DELETE ─────────────────
@router.delete("/{story_id}/likes")
def unlike_story(
        request: Request,
        story_id: int,
        user_id: str = Depends(verify_token),
):
    db = request.state.db
    try:
        remove_like(db, story_id=story_id, user_id=user_id)
        return {"message": "좋아요가 삭제되었습니다."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── GET ────────────────────
@router.get("/{story_id}/likes", response_model=LikeCount)
def get_like_count(story_id: int, db: Session = Depends(get_db)):
    return LikeCount(story_id=story_id, likes=count_likes(db, story_id=story_id))


@router.get("/{story_id}/likes/me")
def check_liked(
        request: Request,
        story_id: int,
        user_id: str = Depends(verify_token),
):
    db = request.state.db
    return {"liked": has_liked(db, story_id=story_id, user_id=user_id)}
