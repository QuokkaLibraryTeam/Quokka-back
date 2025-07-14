import json
import uuid
from typing import List, Dict, Optional

from google.generativeai import GenerativeModel, ChatSession, configure

from core.config import get_settings
from core.redis import rds, append_history, _meta, _hist, EXPIRE_SEC

settings = get_settings()
configure(api_key=settings.GEMINI_API_KEY)

SYSTEM_PERSONA = """
[역할]
- 너는 유치원·초등학교 선생님이야. 아이들에게 설명하듯 밝고 친절하게 말해.

[언어]
- 반드시 한국어로만 대답해.

[말투·문체]
- 문장은 짧고 직관적으로 써. (유치원·초등학생이 바로 이해할 수준)
- 이모티콘‧이모지는 절대 사용하지 마.

[답변 형식]
- 항상 ‘정보를 알려주는’ 말투를 사용해.  (예: “~를 알려줄게”, “~를 설명해 줄게”)
- 사용자가 예시를 요구하면, 되묻지 말고 바로 쉬운 예시를 제시해.
- 부적절한 응답을 하면 그냥 적당히 순화해서 알아들어줘
""".strip()

model = GenerativeModel(
    settings.GEMINI_MODEL,
    system_instruction=SYSTEM_PERSONA,
)

active_chat_sessions: Dict[str, ChatSession] = {}

async def translate_to_english(text: str) -> str:
    """
    주어진 한글 문장을 영어로 번역하여 반환하는 함수
    """
    # 번역 전용 채팅 세션 시작
    translation_chat = model.start_chat(
        system_instruction="""
[역할]
- 당신은 전문 번역가야.
- 사용자가 입력한 한국어 문장을 정확한 영어로 번역해 줘.
- 번역 외 다른 설명은 절대 하지 마.
""".strip()
    )
    # 번역 요청 보내기
    response = await translation_chat.send_message_async(f"한국어 문장을 영어로 번역해줘: {text}")
    return response.text


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