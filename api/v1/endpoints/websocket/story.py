from typing import List

from fastapi import APIRouter, WebSocket, status, WebSocketException
from fastapi.concurrency import run_in_threadpool

from core.chat_manager import get_session
from core.security import decode_token

router = APIRouter()

@router.websocket("/ws/chat/{session_key}")
async def websocket_chat(ws: WebSocket, session_key: str):
    requested: List[str] = ws.scope.get("subprotocols", [])
    if len(requested) != 2 or requested[0] != "jwt":
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    token = requested[1]
    try:
        subject = decode_token(token)
    except WebSocketException:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    uid, *_ = session_key.split(":")
    if uid != subject:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    session = get_session(session_key)
    if not session:
        await ws.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    await ws.accept(subprotocol="jwt")

    try:
        while True:
            prompt = await ws.receive_text()
            resp = await run_in_threadpool(session.send_message, prompt)
            await ws.send_text(resp.text)
    finally:
        await ws.close()
