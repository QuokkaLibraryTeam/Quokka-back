import asyncio
from enum import Enum, auto
from typing import List, Tuple

from fastapi import WebSocket, WebSocketException

from core.chat_manager import (
    send_message,
    gen_two_images,
    append_history,
    mark_done,
    rds,
    _meta
)
from core.security import decode_token
from schemas.story import ClientStart, ClientAnswer, ClientChoice, ClientCmd
from sevices.scene import create_scene

ILLUST_OK = "__ILLUST_OK__"
SCENE_OK   = "__SCENE_OK__"


class State(Enum):
    ILLUST_INFO    = auto()
    SCENE_SYNOPSIS = auto()
    ILLUST_WAIT    = auto()
    CHOICE_WAIT    = auto()
    DRAFT_REVIEW   = auto()
    FINISHED       = auto()


class StorybookService:
    def __init__(self, session_key: str):
        self.session_key = session_key
        self.state       = State.ILLUST_INFO
        self.img_task: asyncio.Task = None  # type: ignore
        self.urls: List[str] = []
        self.chosen_url: str = ""
        self.synopsis: str   = ""

    async def authenticate(self, ws: WebSocket):
        subs = ws.scope.get("subprotocols", [])
        if len(subs) != 2 or subs[0] != "jwt":
            raise WebSocketException(code=1008)
        try:
            user_id = decode_token(subs[1])
        except Exception:
            raise WebSocketException(code=1008)
        if self.session_key.split(":")[0] != user_id:
            raise WebSocketException(code=1008)

        # Redis에 세션 메타가 존재하는지 확인
        if not await rds.exists(_meta(self.session_key)):
            raise WebSocketException(code=1008)

    async def handle(self, ws: WebSocket):
        await ws.accept(subprotocol="jwt")

        start: ClientStart = await ws.receive_json()
        if start.get("type") != "start":
            raise WebSocketException(code=1003)
        topic = start["text"]

        while True:
            if   self.state is State.ILLUST_INFO:    await self._illust_info_loop(ws, topic)
            elif self.state is State.SCENE_SYNOPSIS: await self._scene_synopsis_loop(ws)
            elif self.state is State.ILLUST_WAIT:    await self._wait_for_images(ws)
            elif self.state is State.CHOICE_WAIT:    await self._handle_choice(ws)
            elif self.state is State.DRAFT_REVIEW:   await self._review_draft(ws)

            if self.state is State.FINISHED:
                await ws.close()
                break

    async def _illust_info_loop(self, ws: WebSocket, topic: str):
        prompt = (
            f"{topic} 동화를 위한 삽화를 만들 거야.\n\n"
            "## 정보 요청 형식\n"
            "LLM이 부족한 정보를 요청할 때는 반드시 아래 형식으로만 답해주세요.\n\n"
            "QUESTION: 여기에 질문을 적어주세요\n"
            "EXAMPLES:\n"
            "- 예시 1\n"
            "- 예시 2\n"
            "- 예시 3\n"
            "- 예시 4\n\n"
            f"정보가 충분하면, 지금까지의 모든 묘사를 종합해서 하나의 완성된 그림 설명 문장으로 요약하고, "
            f"그 뒤에 **{ILLUST_OK}** 를 붙여서 끝내세요."
        )

        # send_message 하나로 요청 + 히스토리 관리
        txt = await send_message(self.session_key, prompt)

        while True:
            if ILLUST_OK in txt:
                illust_prompt = txt.replace(ILLUST_OK, "").strip()
                if illust_prompt:
                    self.img_task = asyncio.create_task(gen_two_images(illust_prompt))
                    self.state = State.SCENE_SYNOPSIS
                else:
                    self.state = State.ILLUST_INFO
                return

            q, ex = self._parse_q_examples(txt)
            await ws.send_json({"type": "question", "text": q, "examples": ex})

            ans: ClientAnswer = await ws.receive_json()
            txt = await send_message(self.session_key, ans["text"])

    async def _scene_synopsis_loop(self, ws: WebSocket):
        prompt = (
            "동화 한 씬을 풍부하게 묘사할 시놉시스를 삽화에 이어서 만들자.\n\n"
            "## 정보 요청 형식\n"
            "LLM이 부족한 맥락을 더 물어야 할 때는 반드시 아래 형식으로만 답해주세요.\n\n"
            "QUESTION: 여기에 질문을 적어주세요\n"
            "EXAMPLES:\n"
            "- 예시 A\n"
            "- 예시 B\n"
            "- 예시 C\n"
            "- 예시 D\n\n"
            f"시놉시스 작성이 완료되면 **{SCENE_OK}** 으로만 끝내주세요."
        )

        txt = await send_message(self.session_key, prompt)

        while True:
            if SCENE_OK in txt:
                self.synopsis = txt.replace(SCENE_OK, "").strip()
                self.state = State.ILLUST_WAIT
                return

            q, ex = self._parse_q_examples(txt)
            await ws.send_json({"type": "question", "text": q, "examples": ex})

            ans: ClientAnswer = await ws.receive_json()
            txt = await send_message(self.session_key, ans["text"])

    async def _wait_for_images(self, ws: WebSocket):
        while True:
            if self.img_task and self.img_task.done():
                self.urls = self.img_task.result()
                await ws.send_json({"type": "illustration", "urls": self.urls})
                self.state = State.CHOICE_WAIT
                return
            await asyncio.sleep(0.3)

    async def _handle_choice(self, ws: WebSocket):
        choice: ClientChoice = await ws.receive_json()
        if choice.get("type") != "choice":
            raise WebSocketException(code=1003)
        self.chosen_url = self.urls[choice["index"]]
        await ws.send_json({
            "type": "draft",
            "synopsis": self.synopsis,
            "image": self.chosen_url
        })
        self.state = State.DRAFT_REVIEW

    async def _review_draft(self, ws: WebSocket):
        cmd: ClientCmd = await ws.receive_json()
        if cmd.get("type") == "accept":
            scene_id = create_scene(
                ws.state.db,
                self.session_key.split(":")[1],
                self.synopsis,
                self.chosen_url
            )
            await ws.send_json({"type": "final", "story_id": scene_id})
            await mark_done(self.session_key)
            self.state = State.FINISHED
        elif cmd.get("type") == "retry":
            self.state = State.SCENE_SYNOPSIS
        else:
            raise WebSocketException(code=1003)

    def _parse_q_examples(self, txt: str) -> Tuple[str, List[str]]:
        lines = [line.strip() for line in txt.splitlines() if line.strip()]
        question = ""
        examples: List[str] = []

        for line in lines:
            if line.upper().startswith("QUESTION:"):
                question = line[len("QUESTION:"):].strip()
                break
        try:
            idx = [line.upper().strip() for line in lines].index("EXAMPLES:")
            for example_line in lines[idx + 1:]:
                if example_line.startswith("-"):
                    examples.append(example_line[1:].strip())
                else:
                    break
        except ValueError:
            pass

        return question, examples
