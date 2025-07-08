from __future__ import annotations
from fastapi import APIRouter, WebSocket, Depends
from fastapi.exceptions import WebSocketException
from sqlalchemy.orm import Session

from db.base import get_db
from sevices.storywebsocket import StorybookService
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
        await service.authenticate(ws)
        await service.handle(ws)
    except WebSocketException as e:
        await ws.close(code=e.code)
