from fastapi import WebSocketException
from starlette.websockets import WebSocket

from core.security import decode_token


async def authenticate(ws: WebSocket):
    subs = ws.scope.get("subprotocols", [])
    if len(subs) != 2 or subs[0] != "jwt":
        raise WebSocketException(code=1008)
    try:
        user_id = decode_token(subs[1])
    except Exception:
        raise WebSocketException(code=1008)
    return user_id
