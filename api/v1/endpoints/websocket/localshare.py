from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Depends
from sqlalchemy.orm import Session

import db
from core.redis import connect_ws, broadcast, disconnect_ws, rds, _users_key, close_room_by_code, get_room_details
from db.base import get_db
from sevices.user import get_user_by_id
from sevices.websocket import authenticate
router = APIRouter()


@router.websocket("/{room_code}")
async def ws_endpoint(ws: WebSocket, room_code: str,db: Session = Depends(get_db)):
    # 실제로는 authenticate 함수가 user_id를 반환해야 합니다.
    # 예: user_id = await authenticate(ws)
    user_id = "anonymous_user"  # 임시 사용자 ID
    try:

        user_id = await authenticate(ws)
        await ws.accept(subprotocol="jwt")
    except Exception as e:
        # 인증 실패 처리
        await ws.close(code=4001, reason=f"Authentication failed: {e}")
        return
    user = get_user_by_id(db, user_id)
    # connect_ws가 방 존재 여부를 확인하므로, 여기서는 바로 호출
    await connect_ws(room_code, ws, user_id)
    await broadcast(room_code, {"type": "notice", "text": f"{user.nickname}님이 방에 들어왔습니다."})

    try:
        while True:
            data = await ws.receive_json()
            # 메시지에 사용자 정보 추가
            data_to_broadcast = {"user_id": user_id, **data}
            await broadcast(room_code, data_to_broadcast)
    except WebSocketDisconnect:
        # 클라이언트 연결 종료 시 처리
        pass
    finally:
        # disconnect_ws 호출 시 user_id 전달
        await disconnect_ws(room_code, ws, user_id)
        await broadcast(room_code, {"type": "notice", "text": f"{user.nickname}님이 방에 나갔습니다."})


@router.get("/rooms/{room_code}")
async def get_room_info(room_code: str):
    room_details = await get_room_details(room_code)
    if room_details is None:
        raise HTTPException(status_code=404, detail="Room not found")
    return room_details


@router.delete("/rooms/{room_code}")
async def close_room(room_code: str):
    success = await close_room_by_code(room_code)
    if not success:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"status": "success", "message": f"Room {room_code} has been scheduled for closing."}