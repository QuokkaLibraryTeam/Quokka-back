# pip install openai aiohttp
import asyncio
import pathlib
import uuid
from typing import List

import aiohttp
import openai

from core.chat_manager import translate_to_english
from core.config import get_settings

# 저장 경로 및 URL 접두사 설정
MEDIA_DIR = pathlib.Path("static/illustrations")
URL_PREFIX = "/static/illustrations/"
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

# OpenAI API 키 설정
settings = get_settings()
openai.api_key = settings.OPENAI_API_KEY

# 원본 프롬프트 접두사 (비폭력·비선정적·부드러운 톤 유지)
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

async def _fix_prompt_with_llm(prompt: str) -> str:
    """
    ChatCompletion을 이용해 프롬프트를
    어린이용 긍정 표현으로 교정합니다.
    """
    try:
        resp = await openai.ChatCompletion.acreate(
            model="gpt-4-0613",
            messages=[
                {
                    "role": "system",
                    "content": "당신은 어린이용 동화 삽화 프롬프트 전문가입니다."
                },
                {
                    "role": "user",
                    "content": f"다음 문장을 아이에게 보여줄 동화 그림으로 만들기에 적합하도록, 폭력적/선정적이지 않고 긍정적인 표현으로 바꿔줘: {prompt}"
                }
            ],
            temperature=0.7,
            max_tokens=256,
            top_p=0.8
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return prompt

async def _download_and_save(session: aiohttp.ClientSession, url: str) -> str:
    """
    주어진 URL에서 이미지를 다운로드해
    MEDIA_DIR에 저장하고, 저장된 경로의 URL을 반환합니다.
    """
    try:
        async with session.get(url) as resp:
            img_bytes = await resp.read()
        name = f"{uuid.uuid4().hex}.png"
        path = MEDIA_DIR / name
        path.write_bytes(img_bytes)
        return f"{URL_PREFIX}{name}"
    except Exception:
        return ""

async def gen_two_images_with_dall(
    prompt: str,
    retry: int = 0,
    max_retries: int = 3
) -> List[str]:
    """
    DALL·E 3로 이미지 2장을 생성합니다.
    실패 시 _fix_prompt_with_llm으로 교정 후 재시도합니다.
    """
    if retry >= max_retries:
        return []

    # 원본 프롬프트에 그려달라는 지시 추가
    re_prompt = f"\n[그려줘]\n{prompt}"
    image_prompt = IMAGE_PROMPT_PREFIX + re_prompt
    translated_prompt = await translate_to_english(image_prompt)
    print("번역된 프롬프트:", translated_prompt)
    urls: List[str] = []
    try:
        # 이미지 2장 생성 요청
        response = await openai.Image.acreate(
            prompt=translated_prompt,
            n=2,
            size="1024x1024"  # DALL·E가 지원하는 사이즈 중 하나
        )
        image_urls = [item["url"] for item in response["data"]]

        # 병렬로 다운로드 및 저장
        async with aiohttp.ClientSession() as session:
            tasks = [_download_and_save(session, u) for u in image_urls]
            urls = await asyncio.gather(*tasks)
    except Exception:
        pass

    # 생성된 이미지가 2장 미만이면 프롬프트 교정 후 재귀 호출
    if len([u for u in urls if u]) < 2 and retry < max_retries:
        fixed = await _fix_prompt_with_llm(prompt)
        return await gen_two_images_with_dall(fixed, retry + 1, max_retries)

    return urls
