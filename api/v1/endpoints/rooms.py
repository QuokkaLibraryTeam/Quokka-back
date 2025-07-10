from fastapi import APIRouter, status

from core.redis import create_room

router = APIRouter()

@router.post("", status_code=status.HTTP_201_CREATED)
async def post_room():
    room_code = await create_room()
    return {"room_code": room_code}
