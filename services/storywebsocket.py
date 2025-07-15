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
from core.config import get_settings
from core.image_manager import gen_two_images
from core.image_manager_dall import gen_two_images_with_dall
from core.security import decode_token
from schemas.story import ClientStart, ClientAnswer, ClientChoice, ClientCmd
from services.scene import create_scene
from services.story import get_story_by_story_id


ILLUST_OK = "ILLUST_OK"
SCENE_OK  = "SCENE_OK"
WARNING = "WARNING"

# ────────────────────────────────────────────────
# 0. 공통 고정 블록
PROMPT_STATIC = """
[역할]
- 너는 유치원·초등학교 선생님이야. 밝고 친절하게 설명해.

[문체]
- 한국어만 사용해.
- 문장은 짧고 직관적으로 써.
- 이모티콘·이모지는 절대 쓰지 마.

[정보 요청 규칙]
- 질문은 한 번에 하나만.
- ‘QUESTION:’ 뒤에 질문 한 줄.
- 바로 이어서 ‘EXAMPLES:’ 아래 보기 예시 4줄(‘- ’로 시작).
- 예시는 짧게.
[필터링]
- 사용자의 응답이 부적절한 응답이라면 WARNING을 포함하여 대답해
"""
# ────────────────────────────────────────────────


# 1. 삽화 정보 수집용 프롬프트
def build_illust_info_prompt(topic: str, marker: str) -> str:
    return (
        PROMPT_STATIC
        + f"""
[목표]
- “{topic}” 동화를 위한 삽화 정보를 모은다.
- 정보가 모두 모이면 마지막 줄에 **{marker}** 를 붙인 뒤
  4:3 비율 삽화 설명문을 완성한다.

[정보 요청 형식]
QUESTION: 여기에 질문을 적어 주세요
EXAMPLES:
- 예시 1
- 예시 2
- 예시 3
- 예시 4
"""
    )


# 2. 씬 시놉시스 Q&A 프롬프트
def build_scene_synopsis_prompt(marker: str) -> str:
    return (
        PROMPT_STATIC
        + f"""
[목표]
- 삽화를 바탕으로 동화 한 씬을 풍부하게 묘사할 시놉시스를 완성한다.
- 정보가 충분하면 마지막 줄에 **{marker}** 만 남긴다.

[정보 요청 형식]
QUESTION: 여기에 질문을 적어 주세요
EXAMPLES:
- 예시 A
- 예시 B
- 예시 C
- 예시 D
"""
    )


STORY_5_LINES_PROMPT = """
[지시]
지금까지 만든 시놉시스를 바탕으로 동화 본문을 5줄만 써 줘.
- 숫자·머리표·특수기호 없이 한 줄에 한 문장만.
- 문장은 초등학생이 읽기 쉽게.
- 이모티콘 금지.
"""


# 4. 퀴즈 문제 출제 프롬프트
def build_quiz_question_prompt(title: str) -> str:
    return (
        PROMPT_STATIC
        + f"""
[목표]
- “{title}” 동화에 대한 초등학생용 퀴즈를 한 문제씩 낸다.

[출제 형식]
QUESTION: 문제를 한 문장으로
EXAMPLES:
- 보기 1
- 보기 2
- 보기 3
- 보기 4
"""
    )


# 5. 정답 피드백 프롬프트
def build_quiz_feedback_prompt(user_answer: str) -> str:
    return (
        PROMPT_STATIC
        + f"""
[상황]
내 답은 “{user_answer}”이야.

[지시]
- 맞았는지 틀렸는지 알려 줘.
- 이유를 한두 문장으로 설명해 줘.
"""
    )


class State(Enum):
    ILLUST_INFO    = auto()
    SCENE_SYNOPSIS = auto()
    ILLUST_WAIT    = auto()
    CHOICE_WAIT    = auto()
    DRAFT_REVIEW   = auto()
    FINISHED       = auto()
    QUIZ           = auto()
    EXTEND         = auto()

settings = get_settings()
class StorybookService:
    def __init__(self, session_key: str):
        self.available_cmd = ["quiz", "scene"]
        self.session_key = session_key
        self.state       = State.ILLUST_INFO
        self.img_task: asyncio.Task | None = None
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

        topic = "" if start.get("type") == "quiz" else start["text"]
        if start.get("type") == "quiz":
            self.state = State.QUIZ

        while True:
            if   self.state is State.ILLUST_INFO:    await self._illust_info_loop(ws, topic)
            elif self.state is State.SCENE_SYNOPSIS: await self._scene_synopsis_loop(ws)
            elif self.state is State.ILLUST_WAIT:    await self._wait_for_images(ws)
            elif self.state is State.CHOICE_WAIT:    await self._handle_choice(ws)
            elif self.state is State.DRAFT_REVIEW:   await self._review_draft(ws)
            elif self.state is State.QUIZ:           await self._quiz_loop(ws)
            elif self.state is State.EXTEND:         await self._illust_info_loop(ws,"이제 다음 씬을 만들 준비를 해야해. 똑같은 방법으로 씬을 만들어내면 돼 \n")

            if self.state is State.FINISHED:
                await ws.close()
                break

    # ────────────────────────────────────────────
    # ILLUST_INFO 단계
    async def _illust_info_loop(self, ws: WebSocket, topic: str):
        prompt = build_illust_info_prompt(topic, ILLUST_OK)
        await append_history(self.session_key, "AI", prompt)
        txt = await send_message(self.session_key, prompt)
        await append_history(self.session_key, "AI", txt)

        while True:
            if WARNING in txt:
                await ws.send_json({"type": "rejected", "text": "", "examples": []})
                return
            if ILLUST_OK in txt:
                illust_prompt = txt.replace(ILLUST_OK, "").strip()
                if illust_prompt:
                    if not settings.USING_DALL:
                        self.img_task = asyncio.create_task(gen_two_images(illust_prompt))
                    else:
                        self.img_task = asyncio.create_task(gen_two_images_with_dall(illust_prompt))
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

    # ────────────────────────────────────────────
    # SCENE_SYNOPSIS 단계
    async def _scene_synopsis_loop(self, ws: WebSocket):
        prompt = build_scene_synopsis_prompt(SCENE_OK)
        await append_history(self.session_key, "AI", prompt)
        txt = await send_message(self.session_key, prompt)
        await append_history(self.session_key, "AI", txt)

        while True:
            if WARNING in txt:
                await ws.send_json({"type": "rejected", "text": "", "examples": []})
                return

            if SCENE_OK in txt:
                await append_history(self.session_key, "AI", STORY_5_LINES_PROMPT)
                txt = await send_message(self.session_key, STORY_5_LINES_PROMPT)
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

    # ────────────────────────────────────────────
    # 일러스트 생성 대기
    async def _wait_for_images(self, ws: WebSocket):
        while True:
            if self.img_task and self.img_task.done():
                self.urls = self.img_task.result()
                await ws.send_json({"type": "illustration", "urls": self.urls})
                self.state = State.CHOICE_WAIT
                return
            await asyncio.sleep(0.3)

    # ────────────────────────────────────────────
    # 사용자가 일러스트 선택
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

    # ────────────────────────────────────────────
    # 초안 검토
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
            self.state = State.ILLUST_INFO
        else:
            raise WebSocketException(code=1003)

    # ────────────────────────────────────────────
    # QUIZ 단계
    async def _quiz_loop(self, ws: WebSocket):
        title = get_story_by_story_id(ws.state.db, int(self.session_key.split(":")[1])).title
        prompt = build_quiz_question_prompt(title)
        await append_history(self.session_key, "AI", prompt)
        txt = await send_message(self.session_key, prompt)
        await append_history(self.session_key, "AI", txt)

        while True:
            q, ex = self._parse_q_examples(txt)
            await ws.send_json({"type": "question", "text": q, "examples": ex})

            ans: ClientAnswer = await ws.receive_json()
            feedback_prompt = build_quiz_feedback_prompt(ans["text"])
            txt = await send_message(self.session_key, feedback_prompt)
            await ws.send_json({"type": "feedback", "text": txt})

            next_prompt = "다음 문제를 이어서 내 줘."
            txt = await send_message(self.session_key, next_prompt)
            await append_history(self.session_key, "U", ans["text"])
            await append_history(self.session_key, "AI", txt)

    # ────────────────────────────────────────────
    # QUESTION / EXAMPLES 파싱
    def _parse_q_examples(self, txt: str) -> Tuple[str, List[str]]:
        lines = [line.strip() for line in txt.splitlines() if line.strip()]
        question = ""
        examples: List[str] = []

        for line in lines:
            line = re.sub(r"\*", "", line)
            if line.upper().startswith("QUESTION:"):
                question = line[len("QUESTION:"):].strip()
                break
        try:
            idx = [l.upper() for l in lines].index("EXAMPLES:")
            for example_line in lines[idx + 1:]:
                if example_line.startswith("-"):
                    examples.append(example_line[1:].strip())
                else:
                    break
        except ValueError:
            pass

        return question, examples
