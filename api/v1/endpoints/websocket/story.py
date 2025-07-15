from __future__ import annotations
from fastapi import APIRouter, WebSocket, Depends
from fastapi.exceptions import WebSocketException
from sqlalchemy.orm import Session

from db.base import get_db
from services.storywebsocket import StorybookService
from services.websocket import authenticate

router = APIRouter()

@router.websocket("/{session_key}")
async def storybook_ws(
    ws: WebSocket,
    session_key: str,
    db: Session = Depends(get_db)
):
    service = StorybookService(session_key)
    ws.state.db = db
    try:
        user_id = await authenticate(ws)
        if session_key.split(":")[0] != user_id:
            raise WebSocketException(code=1008)
        await service.handle(ws)
    except WebSocketException as e:
        await ws.close(code=e.code)


