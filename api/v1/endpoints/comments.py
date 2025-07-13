from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from datetime import datetime

from db.base import get_db
from models.comment import Comment
from models.story import Story
from models.user import User
from schemas.comment import CommentCreate, CommentOut, CommentUpdate
from typing import List
from core.security import verify_token

router = APIRouter()

@router.post("/community/comment")
def post_comment(
    data: CommentCreate,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)):

    # 스토리 존재 여부 확인
    story = db.query(Story).filter_by(id=data.story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # 리뷰 생성
    comment = Comment(
        story_id=data.story_id,
        user_id=user_id,
        text=data.text,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return {"message": "리뷰이 성공적으로 등록되었습니다.", "comment_id": comment.id}

@router.get("/community/comment/{story_id}", response_model=List[CommentOut])
def get_comments(story_id: int, db: Session = Depends(get_db)):
    # 스토리 존재 여부 확인
    story = db.query(Story).filter_by(id=story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # 리뷰 목록 조회
    comments = (
        db.query(Comment)
        .options(joinedload(Comment.user))
        .filter_by(story_id=story_id)
        .order_by(Comment.updated_at.asc()) # 수정 시간 오름차순
        .all()
    )

    return [
        CommentOut(
            id=comment.id,
            user_id=comment.user.nickname,
            text=comment.text,
            created_at=comment.updated_at
        )
        for comment in comments
    ]

@router.put("/community/comment/{comment_id}")
def update_comment(
    comment_id: int,
    data: CommentUpdate,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    comment = db.query(Comment).filter_by(id=comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, details="리뷰를 찾을 수 없습니다.")
    
    # 본인 것만.
    if str(comment.user_id) != user_id:
        raise HTTPException(status_code=403, details="본인의 리뷰만 수정 가능합니다.")
    
    comment.text = data.text
    comment.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(comment)

    return {
        "message": "리뷰가 수정되었습니다.",
        "comment_id": comment.id
    }

@router.delete("/community/comment/{comment_id}")
def delete_comment(
    comment_id: int,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    comment = db.query(Comment).filter_by(id=comment_id).first()
    if not comment:
        raise HTTPException(status_code=404, detail="리뷰를 찾을 수 없습니다.")

    if str(comment.user_id) != user_id:
        raise HTTPException(status_code=403, detail="삭제 권한이 없습니다")

    db.delete(comment)
    db.commit()

    return {
        "message": "리뷰가 삭제되었습니다.",
        "comment_id": comment_id
    }