from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from starlette import status

from core.security import verify_token
from db.base import get_db
from schemas.comment import CommentUpdate, CommentOut, CommentCreateModel
from services.comment import update_comment, delete_comment, create_comment, get_comments_by_story

router = APIRouter()

# ── PUT ──────────────────────────────────────────────────────────────
@router.put("/comments/{comment_id}")
def put_comment(
    comment_id: int,
    data: CommentUpdate,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    try:
        result = update_comment(db, comment_id=comment_id, data=data, user_id=user_id)
        return {"message": "리뷰가 수정되었습니다.", "comment_id": result.id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


# ── DELETE ───────────────────────────────────────────────────────────
@router.delete("/comments/{comment_id}")
def delete_comment_endpoint(
    comment_id: int,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    try:
        delete_comment(db, comment_id=comment_id, user_id=user_id)
        return {"message": "리뷰가 삭제되었습니다.", "comment_id": comment_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

@router.post("/{story_id}/comments", status_code=status.HTTP_201_CREATED)
def post_comment(
    request: Request,
    story_id: int,
    data: CommentCreateModel,
    user_id: str = Depends(verify_token),
):
    db = request.state.db
    try:
        result = create_comment(db,story_id, model=data, user_id=user_id)
        return {"message": "리뷰가 성공적으로 등록되었습니다.", "comment_id": result.id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{story_id}/comments", response_model=List[CommentOut])
def list_comments(request: Request,story_id: int):
    db = request.state.db
    try:
        return get_comments_by_story(db, story_id=story_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))