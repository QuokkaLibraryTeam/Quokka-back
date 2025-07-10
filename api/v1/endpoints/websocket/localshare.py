from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.redis import connect_ws, broadcast, disconnect_ws

router = APIRouter()

@router.websocket("/{room_code}")
async def ws_endpoint(ws: WebSocket, room_code: str):
    await connect_ws(room_code, ws)
    try:
        while True:
            data = await ws.receive_json()
            await broadcast(room_code, data)
    except WebSocketDisconnect:
        pass
    finally:
        await disconnect_ws(room_code, ws)
