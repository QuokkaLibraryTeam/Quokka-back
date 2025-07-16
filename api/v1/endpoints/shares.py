from typing import List, Optional

from fastapi import APIRouter, Request, Query

from schemas.share import ShareOut
from services.share import list_shared, all_tags

router = APIRouter()

PREDEFINED_TAGS = ["어드벤쳐", "판타지", "미스터리", "과학", "호러"]

@router.get("/tags", response_model=List[str],tags=["tags"])
def get_database_tags(request: Request):
    db = request.state.db
    return PREDEFINED_TAGS+all_tags(db)

@router.get("/", response_model=List[ShareOut],tags=["share"])
def list_shared_stories(
    request: Request,
    tag: Optional[str] = Query(None, description="태그로 필터링"),
):
    db = request.state.db
    return list_shared(db, tag=tag)