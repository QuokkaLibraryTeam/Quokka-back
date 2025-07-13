import asyncio
import pathlib
import uuid
from typing import List

from google import genai
from google.genai import types

from core.chat_manager import send_message
from core.config import get_settings

MEDIA_DIR = pathlib.Path("static/illustrations")
URL_PREFIX = "/static/illustrations/"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

settings = get_settings()
client = genai.Client(api_key=settings.GEMINI_API_KEY,
                      http_options=types.HttpOptions(api_version="v1beta"))

IMAGE_PROMPT_PREFIX = """
[스타일]
- 색감은 부드럽고 자연스러워야 해
- 4:3 비율로 그려

[금지 사항]
- 이미지 안에 글씨, 텍스트, 로고, 서명은 절대 넣지 마
- 과도한 필터나 노이즈를 넣지 마
- 이미지에 제발 글씨를 넣지 마

[목표]
- 어린이가 보는 동화 삽화를 만든다
"""

def _save_bytes(img_bytes: bytes, ext: str = ".png") -> str:
    name = f"{uuid.uuid4().hex}{ext}"
    path = MEDIA_DIR / name
    path.write_bytes(img_bytes)
    return f"{URL_PREFIX}{name}"

async def _fix_prompt_with_llm(prompt: str) -> str:
    try:
        resp = await send_message(str(uuid.uuid4()), f"다음 문장을 아이에게 보여줄 동화 그림으로 만들기에 적합하도록, 폭력적/선정적이지 않고 긍정적인 표현으로 바꿔줘: {prompt}")
        return resp
    except Exception:
        return prompt


async def gen_two_images(
        prompt: str,
        retry: int = 0,
        max_retries: int = 3
) -> List[str]:
    if retry >= max_retries:
        return []

    re_prompt = f"\n[그려줘]\n{prompt}"
    image_prompt = IMAGE_PROMPT_PREFIX + re_prompt

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