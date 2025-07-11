from fastapi import APIRouter

from api.v1.endpoints.websocket import story, localshare

router = APIRouter()

router.include_router(story.router, prefix="/story")
router.include_router(localshare.router, prefix="/localshare")