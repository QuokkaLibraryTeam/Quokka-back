from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from db.base import get_db
from core.security import verify_token
from models.like import Like
from models.story import Story

router = APIRouter()

@router.post("/community/like/{story_id}")
def like_story(
    story_id: int,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    # 스토리 존재 여부 확인
    story = db.query(Story).filter_by(id=story_id).first()
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    # 이미 좋아요 했는지 확인
    existing_like = db.query(Like).filter_by(user_id=user_id, story_id=story_id).first()
    if existing_like:
        raise HTTPException(status_code=400, detail="이미 좋아요를 눌렀습니다")

    # 좋아요 등록
    like = Like(user_id=user_id, story_id=story_id, created_at=datetime.utcnow())
    db.add(like)
    db.commit()

    return {
        "message": "좋아요가 등록되었습니다."
    }

@router.delete("/community/like/{story_id}")
def unlike_story(
    story_id: int,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    like = db.query(Like).filter_by(user_id=user_id, story_id=story_id).first()
    if not like:
        raise HTTPException(status_code=404, detail="좋아요를 누른 적이 없습니다")

    db.delete(like)
    db.commit()

    return {
        "message": "좋아요가 삭제되었습니다."
    }

# 좋아요 개수 확인
@router.get("/community/like/{story_id}")
def count_likes(story_id: int, db: Session = Depends(get_db)):
    count = db.query(Like).filter_by(story_id=story_id).count()
    return {
        "story_id": story_id, 
        "likes": count
    }