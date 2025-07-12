import json
import uuid
from typing import List, Dict, Optional

from google.generativeai import GenerativeModel, ChatSession, configure

from core.config import get_settings
from core.redis import rds, append_history, _meta, _hist, EXPIRE_SEC

settings = get_settings()
configure(api_key=settings.GEMINI_API_KEY)

SYSTEM_PERSONA = """
너는 이제부터 유치원/초등학교 교사야. 아이를 가르치는 것처럼 문장을 구사해야 해.
* 무조건 정보 요청 형식을 지켜줘
* 말투는 어린이를 가르치는 것처럼 해맑게!
* 대답은 반드시 한국어로.
* 이모티콘은 일절 넣지마.
* 문장은 간단·직관적(초등학생,유치원 수준).
* 내가 예시를 들라고 하면 절대로 질문에 질문으로 예시를 들지 마.
""".strip()

model = GenerativeModel(
    settings.GEMINI_MODEL,
    system_instruction=SYSTEM_PERSONA,
)

active_chat_sessions: Dict[str, ChatSession] = {}


async def new_session(user_id: str, story_id: Optional[int]) -> str:
    key = f"{user_id}:{story_id or 'tmp'}:{uuid.uuid4().hex[:8]}"
    meta = {"user_id": user_id, "story_id": story_id, "status": "draft"}
    await rds.set(_meta(key), json.dumps(meta), ex=EXPIRE_SEC)
    await rds.expire(_hist(key), EXPIRE_SEC)
    return key


async def mark_done(key: str) -> None:
    if key in active_chat_sessions:
        chat = active_chat_sessions[key]

        await rds.delete(_hist(key))
        for message in chat.history:
            role = "U" if message.role == "user" else "AI"
            text = message.parts[0].text
            await append_history(key, role, text)

        del active_chat_sessions[key]

    await rds.persist(_hist(key))
    meta_raw = await rds.get(_meta(key))
    if meta_raw:
        meta = json.loads(meta_raw)
        meta["status"] = "done"
        await rds.set(_meta(key), json.dumps(meta))
        await rds.persist(_meta(key))


async def send_message(session_key: str, user_text: str) -> str:
    if session_key not in active_chat_sessions:
        hist_raw: List[str] = await rds.lrange(_hist(session_key), 0, -1)

        history_for_gemini = []
        for entry in hist_raw:
            role, text = entry.split(":", 1)
            gemini_role = "user" if role == "U" else "model"
            history_for_gemini.append({"role": gemini_role, "parts": [text]})

        chat = model.start_chat(history=history_for_gemini)
        active_chat_sessions[session_key] = chat
    else:
        chat = active_chat_sessions[session_key]

    response = await chat.send_message_async(user_text)

    return response.text