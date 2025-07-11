from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.params import Depends

from core.redis import connect_ws, broadcast, disconnect_ws
from sevices.websocket import authenticate

router = APIRouter()

@router.websocket("/{room_code}")
async def ws_endpoint(ws: WebSocket, room_code: str):

    user_id = await authenticate(ws)
    await ws.accept(subprotocol="jwt")

    await connect_ws(room_code, ws)
    await broadcast(room_code,{"type" : "notice", "text": f"{user_id}님이 방에 들어왔습니다."})
    try:
        while True:
            data = await ws.receive_json()
            await broadcast(room_code, data)
    except WebSocketDisconnect:
        pass
    finally:
        await disconnect_ws(room_code, ws)
        await broadcast(room_code, {"type": "notice", "text": f"{user_id}님이 방에 나갔습니다."})

