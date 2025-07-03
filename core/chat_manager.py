from typing import Dict

import google.generativeai as genai
from core.config import get_settings

settings = get_settings()

# 모델은 프로세스당 1회만 로드
_model = genai.GenerativeModel(settings.GEMINI_MODEL)

# "user_id:story_id" → genai.Chat 세션
_sessions: Dict[str, genai.Chat] = {}


def make_key(user_id: str, story_id: int) -> str:
    return f"{user_id}:{story_id}"


def new_session(user_id: str, story_id: int) -> str:
    key = make_key(user_id, story_id)
    _sessions[key] = _model.start_chat(history=[])
    return key


def get_session(key: str) -> genai.Chat | None:
    return _sessions.get(key)
