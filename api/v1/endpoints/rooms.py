from fastapi import APIRouter, status,HTTPException

from core.redis import create_room, get_room_details, close_room_by_code

router = APIRouter()

@router.get("", status_code=status.HTTP_201_CREATED)
async def open_room_ws():
    room_code = await create_room()
    return {"room_code": room_code}

@router.get("/{room_code}")
async def get_room_info(room_code: str):
    room_details = await get_room_details(room_code)
    if room_details is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return room_details

@router.delete("/{room_code}")
async def close_room(room_code: str):
    success = await close_room_by_code(room_code)
    if not success:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"status": "success", "message": f"Room {room_code} has been scheduled for closing."}