import uuid

from fastapi import APIRouter, Request, HTTPException, status, Depends

from core.security import verify_token
from schemas.share import ShareOut, ShareCreate
from services.share import is_shared, publish, unpublish

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
    request: Request,
    user_id: uuid.UUID = Depends(verify_token)
):
    try:
        return publish(request.state.db,
                       story_id=story_id,
                       user_id=user_id,
                       data=data)
    except (PermissionError, ValueError) as e:
        raise HTTPException(400, str(e))

# ── 태그 PATCH ───────────────────────────────────────
@router.patch("/{story_id}/share", response_model=ShareOut)
def patch_story_tags(
    story_id: int,
    data: ShareCreate,
    request: Request,
    user_id: uuid.UUID = Depends(verify_token)
):
    try:
        return publish(request.state.db,
                          story_id=story_id,
                          user_id=user_id,
                          data=data)
    except (PermissionError, ValueError) as e:
        raise HTTPException(400, str(e))

# ── 언퍼블리시 ───────────────────────────────────────
@router.delete("/{story_id}/share", status_code=status.HTTP_204_NO_CONTENT)
def unpublish_story(story_id: int, request: Request, user_id: uuid.UUID = Depends(verify_token)):
    try:
        unpublish(request.state.db, story_id=story_id,
                  user_id=user_id)
    except PermissionError as e:
        raise HTTPException(404, str(e))
