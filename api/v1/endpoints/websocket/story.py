from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from main import app

router = APIRouter()


@app.websocket("/synopsis")
async def story_synopsis(websocket: WebSocket):
    await websocket.accept()

