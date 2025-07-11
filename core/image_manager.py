import asyncio
import pathlib
import uuid
from typing import List

from google import genai
from google.genai import types

from core.config import get_settings

MEDIA_DIR = pathlib.Path("static/illustrations")
URL_PREFIX = "/static/illustrations/"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

settings = get_settings()
client = genai.Client(api_key=settings.GEMINI_API_KEY,
                      http_options=types.HttpOptions(api_version="v1beta"))


def _save_bytes(img_bytes: bytes, ext: str = ".png") -> str:
    name = f"{uuid.uuid4().hex}{ext}"
    path = MEDIA_DIR / name
    path.write_bytes(img_bytes)
    return f"{URL_PREFIX}{name}"

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

    config = types.GenerateContentConfig(response_modalities=["Text", "Image"])
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
        return await gen_two_images(fixed, retry + 1, max_retries)

    return urls