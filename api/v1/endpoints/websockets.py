from fastapi import APIRouter

from api.v1.endpoints.websocket import story

router = APIRouter()

router.include_router(story.router, prefix="/story")