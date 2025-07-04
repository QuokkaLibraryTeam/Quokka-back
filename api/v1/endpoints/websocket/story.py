# api/v1/endpoints/websocket/synopsis.py
from typing import List, TypedDict

from fastapi import APIRouter, WebSocket, status
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import WebSocketException

from core.chat_manager import get_session, append_history, mark_done
from core.security import decode_token          # JWT → user_id

router = APIRouter()

DONE_TOKEN = "__OK__"


class ClientStart(TypedDict):
    type: str
    topic: str


class ClientAnswer(TypedDict):
    type: str
    text: str


@router.websocket("/ws/chat/{session_key}")
async def websocket_chat(ws: WebSocket, session_key: str):
    subs: List[str] = ws.scope.get("subprotocols", [])
    if len(subs) != 2 or subs[0] != "jwt":
        await ws.close(1008); return

    try:
        subject = decode_token(subs[1])
    except WebSocketException:
        await ws.close(1008); return

    uid, *_ = session_key.split(":")
    if uid != subject:
        await ws.close(1008); return

    session = await get_session(session_key)
    if not session:
        await ws.close(1008); return

    await ws.accept(subprotocol="jwt")

    start: ClientStart = await ws.receive_json()
    if start.get("type") != "start":
        await ws.close(1003); return
    topic = start["topic"]

    first_prompt = (
        f"{topic} 시놉시스를 작성해 주세요. "
        f"추가 정보가 필요하면 질문하고, "
        f"완성되면 '{DONE_TOKEN}' 토큰으로 끝내 주세요."
    )
    await append_history(session_key, "U", first_prompt)
    resp = await run_in_threadpool(session.send_message, first_prompt)
    await append_history(session_key, "AI", resp.text)

    try:
        while True:
            text = resp.text.strip()

            if DONE_TOKEN in text:
                synopsis = text.replace(DONE_TOKEN, "").strip()
                await ws.send_json({"type": "done", "synopsis": synopsis})
                await mark_done(session_key)
                break

            await ws.send_json({"type": "question", "text": text})

            answer: ClientAnswer = await ws.receive_json()
            if answer.get("type") != "answer":
                await ws.close(1003); return
            user_reply = answer["text"]

            await append_history(session_key, "U", user_reply)
            resp = await run_in_threadpool(session.send_message, user_reply)
            await append_history(session_key, "AI", resp.text)

    finally:
        await ws.close()
