# core/chat_manager.py

import json
import uuid
import pathlib
import asyncio
from typing import List, Optional

import redis.asyncio as redis
from core.config import get_settings

from google import genai
from google.genai import types

# --- 설정 로드 ---
settings = get_settings()

# --- 클라이언트 초기화 ---
# Redis 클라이언트 (비동기)
EXPIRE_SEC = 30 * 60
rds = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)

# Gemini API 클라이언트
client = genai.Client(api_key=settings.GEMINI_API_KEY,
                      http_options=types.HttpOptions(api_version="v1beta"))

# --- 상수 및 헬퍼 함수 ---
MEDIA_DIR = pathlib.Path("static/illustrations")
URL_PREFIX = "/static/illustrations/"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PERSONA = """
너는 이제부터 유치원/초등학교 교사야. 아이를 가르치는 것처럼 문장을 구사해야 해.
* 말투는 어린이를 가르치는 것처럼 해맑게!
* 대답은 반드시 한국어로.
* 문장은 간단·직관적(초등학생 수준).
""".strip()


def _meta(k: str) -> str: return f"chat:{k}:meta"


def _hist(k: str) -> str: return f"chat:{k}:hist"


def _save_bytes(img_bytes: bytes, ext: str = ".png") -> str:
    name = f"{uuid.uuid4().hex}{ext}"
    path = MEDIA_DIR / name
    path.write_bytes(img_bytes)
    return f"{URL_PREFIX}{name}"


# --- 세션 및 히스토리 관리 ---
async def new_session(user_id: str, story_id: Optional[int]) -> str:
    key = f"{user_id}:{story_id or 'tmp'}:{uuid.uuid4().hex[:8]}"
    meta = {"user_id": user_id, "story_id": story_id, "status": "draft"}
    async with rds.pipeline() as pipe:
        pipe.set(_meta(key), json.dumps(meta), ex=EXPIRE_SEC)
        pipe.expire(_hist(key), EXPIRE_SEC)
        await pipe.execute()
    return key


async def append_history(key: str, sender: str, text: str) -> None:
    prefix = "U" if sender == "U" else "AI"
    await rds.rpush(_hist(key), f"{prefix}:{text}")
    await rds.expire(_hist(key), EXPIRE_SEC)
    await rds.expire(_meta(key), EXPIRE_SEC)


async def mark_done(key: str) -> None:
    await rds.persist(_hist(key))
    meta_raw = await rds.get(_meta(key))
    meta = json.loads(meta_raw)
    meta["status"] = "done"
    await rds.set(_meta(key), json.dumps(meta))
    await rds.persist(_meta(key))


# --- 텍스트 및 이미지 생성 ---
async def send_message(session_key: str, user_text: str) -> str:
    """
    시스템 페르소나와 Redis 히스토리를 기반으로 대화 응답을 생성하고 기록합니다.
    """
    hist_raw: List[str] = await rds.lrange(_hist(session_key), 0, -1)

    conversation = SYSTEM_PERSONA + "\n\n"
    for entry in hist_raw:
        role, txt = entry.split(":", 1)
        conversation += f"{'사용자' if role == 'U' else 'AI'}: {txt}\n"
    conversation += f"사용자: {user_text}\nAI:"

    resp = await client.aio.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=conversation
    )
    answer = resp.text or ""

    await append_history(session_key, "U", user_text)
    await append_history(session_key, "AI", answer)
    return answer


async def _fix_prompt_with_llm(prompt: str) -> str:
    """LLM을 사용하여 안전하고 긍정적인 프롬프트로 수정합니다."""
    try:
        resp = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=f"다음 문장을 아이에게 보여줄 동화 그림으로 만들기에 적합하도록, 폭력적/선정적이지 않고 긍정적인 표현으로 바꿔줘: {prompt}"
        )
        return resp.text.strip() or prompt
    except Exception as e:
        print(f"LLM 프롬프트 수정 중 오류 발생: {e}")
        return prompt


async def gen_two_images(
        prompt: str,
        retry: int = 0,
        max_retries: int = 1
) -> List[str]:
    """이미지 두 장을 생성하고, 실패 시 LLM으로 프롬프트를 수정하여 재시도합니다."""
    if retry >= max_retries:
        print(f"[gen_two_images] 최대 재시도 횟수({max_retries}) 초과. 이미지 생성 최종 실패.")
        return []

    image_prompt = f"동화 일러스트 스타일의 그림 글씨 없이 그림만 줘: {prompt}"
    print(f"[gen_two_images] 요청 프롬프트 (재시도 {retry}): {image_prompt!r}")

    config = types.GenerateContentConfig(
        response_modalities=["Text", "Image"]
    )

    tasks = [
        client.aio.models.generate_content(
            model="gemini-2.0-flash-preview-image-generation",
            contents=image_prompt,
            config=config,
        ) for _ in range(2)
    ]
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    urls, success_count = [], 0
    for resp in responses:
        if isinstance(resp, Exception):
            print(f"[gen_two_images] ⚠️ API 예외 발생: {resp}")
            continue

        try:
            parts = resp.candidates[0].content.parts
            image_found_in_parts = False
            for part in parts:
                if hasattr(part, 'inline_data') and hasattr(part.inline_data, 'data') and part.inline_data.data:
                    urls.append(_save_bytes(part.inline_data.data))
                    success_count += 1
                    image_found_in_parts = True
                    print(f"✅ 이미지 저장 성공 (크기: {len(part.inline_data.data)} 바이트)")

            if not image_found_in_parts:
                print(f"❌ 이미지 없음, 텍스트 응답: {getattr(resp, 'text', 'N/A')!r}")

        except (AttributeError, IndexError) as e:
            print(f"❌ 응답 파싱 오류: {e}. 받은 텍스트: {getattr(resp, 'text', 'N/A')!r}")

    if success_count < 2 and retry < max_retries:
        print(f"[gen_two_images] 일부 또는 전체 이미지 생성 실패. 프롬프트를 수정하여 재시도합니다.")
        fixed_prompt = await _fix_prompt_with_llm(prompt)
        return await gen_two_images(fixed_prompt, retry + 1, max_retries)

    return urls