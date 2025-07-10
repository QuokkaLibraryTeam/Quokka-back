import json
import uuid
import pathlib
import asyncio
from typing import List, Optional

from core.config import get_settings
from core.redis import rds, append_history, _meta, _hist, EXPIRE_SEC
from google import genai
from google.genai import types

# --- 설정 로드 및 클라이언트 초기화 ---
settings = get_settings()
client = genai.Client(api_key=settings.GEMINI_API_KEY,
                      http_options=types.HttpOptions(api_version="v1beta"))

# --- 미디어 경로 및 페르소나 ---
MEDIA_DIR = pathlib.Path("static/illustrations")
URL_PREFIX = "/static/illustrations/"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_PERSONA = """
너는 이제부터 유치원/초등학교 교사야. 아이를 가르치는 것처럼 문장을 구사해야 해.
* 말투는 어린이를 가르치는 것처럼 해맑게!
* 대답은 반드시 한국어로.
* 문장은 간단·직관적(초등학생 수준).
""".strip()

def _save_bytes(img_bytes: bytes, ext: str = ".png") -> str:
    name = f"{uuid.uuid4().hex}{ext}"
    path = MEDIA_DIR / name
    path.write_bytes(img_bytes)
    return f"{URL_PREFIX}{name}"

async def new_session(user_id: str, story_id: Optional[int]) -> str:
    key = f"{user_id}:{story_id or 'tmp'}:{uuid.uuid4().hex[:8]}"
    meta = {"user_id": user_id, "story_id": story_id, "status": "draft"}
    await rds.set(_meta(key), json.dumps(meta), ex=EXPIRE_SEC)
    await rds.expire(_hist(key), EXPIRE_SEC)
    return key

async def mark_done(key: str) -> None:
    await rds.persist(_hist(key))
    meta_raw = await rds.get(_meta(key))
    if meta_raw:
        meta = json.loads(meta_raw)
        meta["status"] = "done"
        await rds.set(_meta(key), json.dumps(meta))
        await rds.persist(_meta(key))

async def send_message(session_key: str, user_text: str) -> str:
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
    try:
        resp = await client.aio.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=f"다음 문장을 아이에게 보여줄 동화 그림으로 만들기에 적합하도록, 폭력적/선정적이지 않고 긍정적인 표현으로 바꿔줘: {prompt}"
        )
        return resp.text.strip() or prompt
    except Exception:
        return prompt

async def gen_two_images(
    prompt: str,
    retry: int = 0,
    max_retries: int = 3
) -> List[str]:
    if retry >= max_retries:
        return []

    image_prompt = f"""한 편의 지브리 애니메이션의 스틸컷처럼, 주제에 알맞는 분위기로 동화 삽화를 그려줘

    주제: {prompt}

    * 4:3 비율
    * 이미지 내 어떠한 글씨, 텍스트, 로고, 서명도 절대 금지"""

    config = types.GenerateContentConfig(response_modalities=["Text","Image"])
    tasks = [
        client.aio.models.generate_content(
            model="gemini-2.0-flash-preview-image-generation",
            contents=image_prompt,
            config=config
        ) for _ in range(2)
    ]
    responses = await asyncio.gather(*tasks, return_exceptions=True)
    urls, success_count = [], 0
    for resp in responses:
        if isinstance(resp, Exception):
            continue
        try:
            for part in resp.candidates[0].content.parts:
                if getattr(part, "inline_data", None) and getattr(part.inline_data, "data", None):
                    urls.append(_save_bytes(part.inline_data.data))
                    success_count += 1
        except Exception:
            pass

    if success_count < 2 and retry < max_retries:
        fixed = await _fix_prompt_with_llm(prompt)
        return await gen_two_images(fixed, retry+1, max_retries)

    return urls