from typing import List, Optional

from fastapi import APIRouter, Request, HTTPException, Query, status

from schemas.share import ShareOut, ShareCreate, TagsUpdate
from services.share import all_tags, is_shared, publish, patch_tags, unpublish

router = APIRouter()
PREDEFINED_TAGS = ["어드벤쳐", "판타지", "미스터리", "과학", "호러"]


# ── 퍼블리시 여부 ─────────────────────────────────────
@router.get("/{story_id}/share/me")
def check_shared(story_id: int, request: Request):
    return {"shared": is_shared(request.state.db, story_id)}

# ── 퍼블리시 ──────────────────────────────────────────
@router.post("/{story_id}/share", response_model=ShareOut,
             status_code=status.HTTP_201_CREATED)
def publish_story(
    story_id: int,
    data: ShareCreate,
    request: Request
):
    try:
        return publish(request.state.db,
                       story_id=story_id,
                       user_id=request.state.user_id,
                       data=data)
    except (PermissionError, ValueError) as e:
        raise HTTPException(400, str(e))

# ── 태그 PATCH ───────────────────────────────────────
@router.patch("/{story_id}/share", response_model=ShareOut)
def patch_story_tags(
    story_id: int,
    data: TagsUpdate,
    request: Request
):
    try:
        return patch_tags(request.state.db,
                          story_id=story_id,
                          user_id=request.state.user_id,
                          data=data)
    except (PermissionError, ValueError) as e:
        raise HTTPException(400, str(e))

# ── 언퍼블리시 ───────────────────────────────────────
@router.delete("/{story_id}/share", status_code=status.HTTP_204_NO_CONTENT)
def unpublish_story(story_id: int, request: Request):
    try:
        unpublish(request.state.db, story_id=story_id,
                  user_id=request.state.user_id)
    except PermissionError as e:
        raise HTTPException(404, str(e))
