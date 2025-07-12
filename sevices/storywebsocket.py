import asyncio
import re
from enum import Enum, auto
from typing import List, Tuple

from fastapi import WebSocket, WebSocketException

from core.chat_manager import (
    send_message,
    append_history,
    mark_done,
    rds,
    _meta
)
from core.cluade import send_clova_chat
from core.image_manager import gen_two_images
from core.security import decode_token
from schemas.story import ClientStart, ClientAnswer, ClientChoice, ClientCmd
from sevices.scene import create_scene
from sevices.story import get_story_by_story_id

ILLUST_OK = "ILLUST_OK"
SCENE_OK   = "SCENE_OK"


class State(Enum):
    ILLUST_INFO    = auto()
    SCENE_SYNOPSIS = auto()
    ILLUST_WAIT    = auto()
    CHOICE_WAIT    = auto()
    DRAFT_REVIEW   = auto()
    FINISHED       = auto()
    QUIZ           = auto()


class StorybookService:
    def __init__(self, session_key: str):
        self.available_cmd = ["quiz", "scene"]
        self.session_key = session_key
        self.state       = State.ILLUST_INFO
        self.img_task: asyncio.Task = None  # type: ignore
        self.urls: List[str] = []
        self.chosen_url: str = ""
        self.synopsis: str   = ""

    async def handle(self, ws: WebSocket):
        if not await rds.exists(_meta(self.session_key)):
            raise WebSocketException(code=1008)

        await ws.accept(subprotocol="jwt")

        start: ClientStart = await ws.receive_json()
        await append_history(self.session_key, "U", start.get("text", ""))
        if start.get("type") not in self.available_cmd:
            raise WebSocketException(code=1008)

        if start.get("type") == "quiz":
            self.state = State.QUIZ
            topic = ""

        else:
            topic = start["text"]

        while True:
            if   self.state is State.ILLUST_INFO:    await self._illust_info_loop(ws, topic)
            elif self.state is State.SCENE_SYNOPSIS: await self._scene_synopsis_loop(ws)
            elif self.state is State.ILLUST_WAIT:    await self._wait_for_images(ws)
            elif self.state is State.CHOICE_WAIT:    await self._handle_choice(ws)
            elif self.state is State.DRAFT_REVIEW:   await self._review_draft(ws)
            elif self.state is State.QUIZ:           await self._quiz_loop(ws)

            if self.state is State.FINISHED:
                await ws.close()
                break

    async def _illust_info_loop(self, ws: WebSocket, topic: str):
        prompt = (
            f"{topic} 동화를 위한 삽화를 만들 거야.\n\n 질문은 무조건 하나씩 해줘, 예시가 너무 길지 않게 주의 해줘"
            "## 정보 요청 형식\n"
            "QUESTION: 여기에 질문을 적어주세요\n"
            "EXAMPLES:\n"
            "- 예시 1\n"
            "- 예시 2\n"
            "- 예시 3\n"
            "- 예시 4\n\n"
            f"정보가 충분하면, 완성된 그림 설명에 **{ILLUST_OK}** 를 붙여서 끝내세요."
        )
        await append_history(self.session_key, "AI", prompt)
        txt = await send_message(self.session_key, prompt)
        await append_history(self.session_key, "AI", txt)
        while True:
            print(txt)
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
            await append_history(self.session_key, "U", ans["text"])
            txt = await send_message(self.session_key, ans["text"])
            await append_history(self.session_key, "AI", txt)

    async def _scene_synopsis_loop(self, ws: WebSocket):
        prompt = (
            "동화 한 씬을 풍부하게 묘사할 시놉시스를 삽화에 이어서 만들자.\n\n"
            "## 정보 요청 형식\n"
            "QUESTION: 여기에 질문을 적어주세요\n"
            "EXAMPLES:\n"
            "- 예시 A\n"
            "- 예시 B\n"
            "- 예시 C\n"
            "- 예시 D\n\n"
            f"완료되면 **{SCENE_OK}** 으로만 끝내주세요."
        )
        await append_history(self.session_key, "AI", prompt)
        txt = await send_message(self.session_key, prompt)
        await append_history(self.session_key, "AI", txt)

        while True:
            if SCENE_OK in txt:
                prompt2 = (
                    f"지금까지 너와 내가 만든 시놉시스를 통해 7줄의 동화를 만들어줘, 다른거 표기하지 말고, 오직 동화만 써서 줘, 숫자 나열도 필요 없어"
                )
                await append_history(self.session_key, "AI", prompt2)
                txt = await send_message(self.session_key, prompt2)
                refined_txt = send_clova_chat(txt)
                await append_history(self.session_key, "AI", txt)
                self.synopsis = refined_txt
                self.state = State.ILLUST_WAIT
                return

            q, ex = self._parse_q_examples(txt)
            await ws.send_json({"type": "question", "text": q, "examples": ex})

            ans: ClientAnswer = await ws.receive_json()
            await append_history(self.session_key, "U", ans["text"])
            txt = await send_message(self.session_key, ans["text"])
            await append_history(self.session_key, "AI", txt)

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
        await append_history(self.session_key, "U", choice["text"])
        self.chosen_url = self.urls[choice["text"]]
        await ws.send_json({
            "type": "draft",
            "synopsis": self.synopsis,
            "image": self.chosen_url
        })
        self.state = State.DRAFT_REVIEW

    async def _review_draft(self, ws: WebSocket):
        cmd: ClientCmd = await ws.receive_json()
        await append_history(self.session_key, "U", cmd.get("type", ""))
        if cmd.get("type") == "accept":
            scene_id = create_scene(
                ws.state.db,
                self.session_key.split(":")[1],
                self.synopsis,
                self.chosen_url
            )
            await ws.send_json({"type": "final"})
            await append_history(self.session_key, "AI", "final")
            await mark_done(self.session_key)
            self.state = State.FINISHED
        elif cmd.get("type") == "retry":
            self.state = State.SCENE_SYNOPSIS
        else:
            raise WebSocketException(code=1003)

    async def _quiz_loop(self, ws: WebSocket):
        topic = get_story_by_story_id(ws.state.db,int(self.session_key.split(":")[1])).title

        prompt = (
            f"{topic}라는 동화에 대한 퀴즈를 하나씩 내줘 초등학생 수준으로... 질문과 선지 4개를 제공 해. 양식대로 질문을 제공해"
            "## 정보 요청 형식\n"
            "QUESTION: 여기에 질문을 적어주세요\n"
            "EXAMPLES:\n"
            "- 예시 A\n"
            "- 예시 B\n"
            "- 예시 C\n"
            "- 예시 D\n\n"
            "위 양식을 꼭 지켜, 예시는 -로 구분해, ** 빼"
        )
        await append_history(self.session_key, "AI", prompt)
        txt = await send_message(self.session_key, prompt)
        await append_history(self.session_key, "AI", txt)
        print(txt)
        while True:
            q, ex = self._parse_q_examples(txt)
            await ws.send_json({"type": "question", "text": q, "examples": ex})

            ans: ClientAnswer = await ws.receive_json()
            prompt = (
                f"내 답은 :{ans['text']}"
                "내 답에 대해 피드백을 해줘"
            )
            txt = await send_message(self.session_key, prompt)
            await ws.send_json({"type": "feedback", "text": txt})
            prompt = (
                f"고마워 이제 다음 퀴즈 똑같이 이어가줘"
            )
            txt = await send_message(self.session_key, prompt)
            await append_history(self.session_key, "U", ans["text"])
            await append_history(self.session_key, "AI", txt)

    def _parse_q_examples(self, txt: str) -> Tuple[str, List[str]]:
        lines = [line.strip() for line in txt.splitlines() if line.strip()]
        question = ""
        examples: List[str] = []

        for line in lines:
            line = re.sub(r"\*","",line)
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
