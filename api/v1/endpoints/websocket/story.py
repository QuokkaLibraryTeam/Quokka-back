from __future__ import annotations
import asyncio, re
from enum import Enum, auto
from typing import List, Tuple, TypedDict

from fastapi import APIRouter, WebSocket
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import WebSocketException

from core.security import decode_token
from core.chat_manager import (
    get_session, append_history, mark_done, gen_two_images
)
from sevices.scene import create_scene
from sevices.story import parse_q_examples

class State(Enum):
    ILLUST_INFO   = auto()
    SCENE_SYNOPSIS = auto()
    ILLUST_WAIT   = auto()
    CHOICE_WAIT   = auto()
    DRAFT_REVIEW  = auto()
    FINISHED      = auto()

ILLUST_OK = "__ILLUST_OK__"
SCENE_OK  = "__SCENE_OK__"

class ClientStart(TypedDict):  type: str; topic: str
class ClientAnswer(TypedDict): type: str; text: str
class ClientChoice(TypedDict): type: str; index: int
class ClientCmd(TypedDict):    type: str                 # accept / retry

router = APIRouter()

@router.websocket("/{session_key}")
async def storybook_ws(ws: WebSocket, session_key: str):
    """
    1) 삽화에 필요한 최소 정보(Q&A) → __ILLUST_OK__
    2) Gemini Vision 으로 삽화 2장 비동기 생성
    3) 동시에 ‘한 씬 시놉시스’ Q&A → __SCENE_OK__
    4) 삽화 2장 url 전달 → 사용자가 1장 선택
    5) 시놉시스 + 선택 삽화 초본 제시 → accept / retry
    6) accept → DB 저장·세션 영구화 / retry → 3번으로 되돌아감
    """

    # 인증
    subs: List[str] = ws.scope.get("subprotocols", [])
    if len(subs) != 2 or subs[0] != "jwt":
        await ws.close(1008); return
    try:
        user_id = decode_token(subs[1])
    except WebSocketException:
        await ws.close(1008); return
    if session_key.split(":")[0] != user_id:
        await ws.close(1008); return
    session = await get_session(session_key)
    if not session:
        await ws.close(1008); return
    await ws.accept(subprotocol="jwt")

    # start 메시지
    start: ClientStart = await ws.receive_json()
    if start.get("type") != "start":
        await ws.close(1003); return
    topic = start["topic"]

    state = State.ILLUST_INFO
    img_task: asyncio.Task | None = None
    urls: List[str] = []
    chosen_url: str = ""
    synopsis: str = ""

    while True:
        # 삽화 최소정보
        if state is State.ILLUST_INFO:
            prompt = (
                f"{topic} 동화를 위한 삽화를 만들 거야.\n"
                f"부족한 정보가 있으면 'QUESTION / EXAMPLES' 형식으로 묻고, "
                f"충분하면 '{ILLUST_OK}' 로 끝내."
            )
            resp = await run_in_threadpool(session.send_message, prompt)
            while True:
                txt = resp.text.strip()
                if ILLUST_OK in txt:
                    illust_prompt = txt.replace(ILLUST_OK, "").strip()
                    img_task = asyncio.create_task(
                        run_in_threadpool(gen_two_images, illust_prompt)
                    )
                    state = State.SCENE_SYNOPSIS
                    break
                q, ex = parse_q_examples(txt)
                await ws.send_json({"type":"question","text":q,"examples":ex})
                ans: ClientAnswer = await ws.receive_json()
                await append_history(session_key, "U", ans["text"])
                resp = await run_in_threadpool(session.send_message, ans["text"])
                await append_history(session_key, "AI", resp.text)

        # 장면 시놉시스
        elif state is State.SCENE_SYNOPSIS:
            prompt = (
                "동화 한 씬을 풍부하게 묘사할 시놉시스를 만들자.\n"
                f"필요하면 질문해, 완료되면 '{SCENE_OK}' 로 끝내."
            )
            resp = await run_in_threadpool(session.send_message, prompt)
            while True:
                txt = resp.text.strip()
                if SCENE_OK in txt:
                    synopsis = txt.replace(SCENE_OK, "").strip()
                    state = State.ILLUST_WAIT
                    break
                q, ex = parse_q_examples(txt)
                await ws.send_json({"type":"question","text":q,"examples":ex})
                ans: ClientAnswer = await ws.receive_json()
                await append_history(session_key, "U", ans["text"])
                resp = await run_in_threadpool(session.send_message, ans["text"])
                await append_history(session_key, "AI", resp.text)

        # 이미지 생성 대기
        elif state is State.ILLUST_WAIT:
            if img_task and img_task.done():
                urls = img_task.result()   # 2장 url
                await ws.send_json({"type":"illustration","urls":urls})
                state = State.CHOICE_WAIT
            else:
                await asyncio.sleep(0.3)

        # 사용자 선택
        elif state is State.CHOICE_WAIT:
            choice: ClientChoice = await ws.receive_json()
            if choice.get("type") != "choice":
                await ws.close(1003); return
            chosen_url = urls[choice["index"]]
            await ws.send_json({"type":"draft","synopsis":synopsis,"image":chosen_url})
            state = State.DRAFT_REVIEW

        # 초본 검토
        elif state is State.DRAFT_REVIEW:
            cmd: ClientCmd = await ws.receive_json()
            if cmd["type"] == "accept":
                story_id = create_scene(user_id, synopsis, chosen_url)
                await ws.send_json({"type":"final","story_id":story_id})
                await mark_done(session_key)
                state = State.FINISHED
            elif cmd["type"] == "retry":
                state = State.SCENE_SYNOPSIS
            else:
                await ws.close(1003); return

        # 종료
        if state is State.FINISHED:
            await ws.close(); break
