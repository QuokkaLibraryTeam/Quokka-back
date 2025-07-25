from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from core.security import verify_token
from db.base import get_db
from models.story import Story
from models.share import Share
from schemas.share import ShareCreate, ShareOut, TagsUpdate

router = APIRouter()

# 미리 지정된 태그 목록
PREDEFINED_TAGS = ["어드벤쳐", "판타지", "미스터리", "과학", "호러"]

@router.get(
    "/share/tags",
    response_model=List[str],
    status_code=200
)
def get_predefined_tags():
    """
    클라이언트에서 사용할 수 있는 미리 정의된 태그 목록 반환
    """
    return PREDEFINED_TAGS

@router.get(
    "/share/db-tags",
    response_model=List[str],
    status_code=200
)
def get_database_tags(
    db: Session = Depends(get_db)
):
    """
    DB에 저장된 모든 태그 조회 (중복 없이)
    """
    rows = db.query(func.unnest(Share.tags).label("tag")).distinct().all()
    return [row.tag for row in rows]

@router.get(
    "/share/stories/check/{story_id}",
    response_model=dict,
    status_code=200
)
def check_shared_story(
    story_id: int,
    db: Session = Depends(get_db)
):
    """
    특정 스토리가 공유(퍼블리싱) 중인지 확인
    """
    shared = db.query(Share).filter_by(story_id=story_id).first() is not None
    return {"shared": shared}

@router.post(
    "/share/stories/{story_id}",
    response_model=ShareOut,
    status_code=201
)
def publish_story(
    story_id: int,
    data: ShareCreate,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    # 소유자만 퍼블리싱 가능
    story = db.query(Story).filter_by(id=story_id, user_id=user_id).first()
    if not story:
        raise HTTPException(
            status_code=404,
            detail="Story not found or access denied"
        )
    # 태그 유효성 검증
    tags: List[str] = [t.strip() for t in data.tags if t.strip()]
    if not tags:
        raise HTTPException(
            status_code=400,
            detail="At least one valid tag must be provided"
        )
    share = db.query(Share).filter_by(story_id=story_id, user_id=user_id).first()
    if share:
        share.tags = tags
    else:
        share = Share(
            user_id=user_id,
            story_id=story_id,
            tags=tags,
            created_at=datetime.utcnow()
        )
        db.add(share)
    db.commit()
    db.refresh(share)
    return share

@router.patch(
    "/share/stories/{story_id}",
    response_model=ShareOut,
    status_code=200
)
def update_share_tags(
    story_id: int,
    data: ShareCreate,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    share = db.query(Share).filter_by(story_id=story_id, user_id=user_id).first()
    if not share:
        raise HTTPException(
            status_code=404,
            detail="Shared story not found or access denied"
        )
    tags: List[str] = [t.strip() for t in data.tags if t.strip()]
    if not tags:
        raise HTTPException(
            status_code=400,
            detail="At least one valid tag must be provided"
        )
    share.tags = tags
    db.commit()
    db.refresh(share)
    return share

@router.post(
    "/share/stories/{story_id}/tags",
    response_model=ShareOut,
    status_code=200
)
def add_tags_to_share(
    story_id: int,
    data: TagsUpdate,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    share = db.query(Share).filter_by(story_id=story_id, user_id=user_id).first()
    if not share:
        raise HTTPException(
            status_code=404,
            detail="Shared story not found or access denied"
        )
    # 중복 없이 추가
    new_tags = [t.strip() for t in data.tags if t.strip()]
    share.tags = list(dict.fromkeys(share.tags + new_tags))
    db.commit()
    db.refresh(share)
    return share

@router.delete(
    "/share/stories/{story_id}/tags",
    response_model=ShareOut,
    status_code=200
)
def remove_tags_from_share(
    story_id: int,
    data: TagsUpdate,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    share = db.query(Share).filter_by(story_id=story_id, user_id=user_id).first()
    if not share:
        raise HTTPException(
            status_code=404,
            detail="Shared story not found or access denied"
        )
    remove = {t.strip() for t in data.tags if t.strip()}
    share.tags = [t for t in share.tags if t not in remove]
    db.commit()
    db.refresh(share)
    return share

@router.delete(
    "/share/stories/{story_id}",
    status_code=204
)
def unpublish_story(
    story_id: int,
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db)
):
    share = db.query(Share).filter_by(story_id=story_id, user_id=user_id).first()
    if not share:
        raise HTTPException(
            status_code=404,
            detail="Shared story not found or access denied"
        )
    db.delete(share)
    db.commit()
    return

@router.get(
    "/shared/stories",
    response_model=List[ShareOut]
)
def list_shared_stories(
    tag: Optional[str] = Query(None, description="태그로 필터링"),
    db: Session = Depends(get_db)
):
    query = db.query(Share).options(
        joinedload(Share.story).joinedload(Story.scenes)
    )
    if tag:
        query = query.filter(Share.tags.any(tag))
    shares = query.all()
    return shares

@router.get(
    "/shared/stories/{story_id}",
    response_model=ShareOut
)
def get_shared_story(
    story_id: int,
    db: Session = Depends(get_db)
):
    share = db.query(Share).options(
        joinedload(Share.story).joinedload(Story.scenes)
    ).filter_by(story_id=story_id).first()
    if not share:
        raise HTTPException(
            status_code=404,
            detail="Shared story not found"
        )
    return share
