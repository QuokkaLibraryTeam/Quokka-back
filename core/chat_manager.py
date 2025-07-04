import json
import uuid
from typing import Dict, List

import google.generativeai as genai
import redis

from core.config import get_settings

settings = get_settings()
rds = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

EXPIRE_SEC = 30 * 60                   # 초안 상태 동안 자동 삭제
model = genai.GenerativeModel(settings.GEMINI_MODEL)

def _meta(k: str) -> str: return f"chat:{k}:meta"
def _hist(k: str) -> str: return f"chat:{k}:hist"

async def new_session(user_id: str, story_id: int | None) -> str:
    """
    • story_id 가 None 이면 임시 세션(tmp)로 만든다.
    • return: session_key
    """
    key = f"{user_id}:{story_id or 'tmp'}:{uuid.uuid4().hex[:8]}"
    meta = {"user_id": user_id, "story_id": story_id, "status": "draft"}
    await rds.set(_meta(key), json.dumps(meta), ex=EXPIRE_SEC)
    return key


async def get_session(key: str):
    """
    Redis 히스토리를 읽어 Chat 인스턴스를 복원.
    없으면 None
    """
    hist_raw: List[str] = await rds.lrange(_hist(key), 0, -1)
    if hist_raw is None:
        return None

    history = [
        {"role": "user" if h.startswith("U:") else "model",
         "parts": [h[2:]]}
        for h in hist_raw
    ]
    return model.start_chat(history=history)


async def append_history(key: str, sender: str, text: str) -> None:
    await rds.rpush(_hist(key), f"{sender}:{text}")
    await rds.expire(_hist(key), EXPIRE_SEC)
    await rds.expire(_meta(key), EXPIRE_SEC)


async def mark_done(key: str) -> None:
    """
    시놉시스가 완성됐을 때 호출:
    • TTL 제거 → 영구 보존
    • status="done" 으로 업데이트
    """
    await rds.persist(_hist(key))
    meta = json.loads(await rds.get(_meta(key)))
    meta["status"] = "done"
    await rds.set(_meta(key), json.dumps(meta))
    await rds.persist(_meta(key))
