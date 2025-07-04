import json
import uuid
from typing import Dict, List, Optional
import os, uuid, pathlib
import google.generativeai as genai
import redis

from core.config import get_settings

settings = get_settings()
rds = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

EXPIRE_SEC = 30 * 60
_model = genai.GenerativeModel(settings.GEMINI_MODEL)
_img_model = genai.GenerativeModel("gemini-2.0-image")

MEDIA_DIR = pathlib.Path("static/illustrations")
URL_PREFIX = "/static/illustrations/"

MEDIA_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PERSONA = """
너는 이제부터 유치원/초등학교 교사야. 아이를 가르치는것처럼 문장을 구사해야해
* 말투는 어린이를 가르치는것처럼 해맑게!
* 대답은 반드시 한국어로.
* 문장은 간단·직관적(초등학생 수준).
"""

def _meta(k: str) -> str: return f"chat:{k}:meta"
def _hist(k: str) -> str: return f"chat:{k}:hist"

def new_session(user_id: str, story_id: Optional[int]) -> str:
    """
    story_id 가 None → 임시 세션(tmp).
    Redis에 메타·빈 히스토리를 저장하고 30 분 TTL.
    반환: session_key
    """
    key  = f"{user_id}:{story_id or 'tmp'}:{uuid.uuid4().hex[:8]}"
    meta = {"user_id": user_id, "story_id": story_id, "status": "draft"}

    with rds.pipeline() as pipe:
        pipe.set(_meta(key), json.dumps(meta), ex=EXPIRE_SEC)
        pipe.rpush(_hist(key), *[])
        pipe.expire(_hist(key), EXPIRE_SEC)
        pipe.execute()

    return key


def get_session(key: str):
    """
    Redis 히스토리를 읽어 genai.Chat 인스턴스 복원.
    • 히스토리가 없고 메타도 없으면 None
    • SYSTEM_PERSONA 를 항상 맨 앞에 넣어 반환
    """
    hist_raw: List[str] = rds.lrange(_hist(key), 0, -1)

    if not hist_raw:
        if not rds.exists(_meta(key)):
            return None
        hist_raw = []

    # TTL 연장 (접속 시점마다 30 분)
    rds.expire(_meta(key), EXPIRE_SEC)
    rds.expire(_hist(key), EXPIRE_SEC)

    history = [{"role": "system", "parts": [SYSTEM_PERSONA]}] + [
        {
            "role": "user" if h.startswith("U:") else "model",
            "parts": [h[2:]],
        }
        for h in hist_raw
    ]

    return _model.start_chat(history=history)


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


def _save_bytes(img_bytes: bytes, ext: str = ".png") -> str:
    name = f"{uuid.uuid4().hex}{ext}"
    path = MEDIA_DIR / name
    path.write_bytes(img_bytes)
    return f"{URL_PREFIX}{name}"

def gen_two_images(prompt: str) -> List[str]:
    vision_resp = _img_model.generate_content(
        prompt,
        generation_config={"num_images": 2, "image_format": "png"}  # num_images 지원 가정
    )

    images: List[bytes] = [
        part.file_data for part in vision_resp.candidates[0].content.parts
        if hasattr(part, "file_data")
    ][:2]

    urls: List[str] = [_save_bytes(b) for b in images]
    return urls
