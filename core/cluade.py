import os
import anthropic
from core.chat_manager import append_history
from core.config import get_settings

settings = get_settings()
client = anthropic.Client(api_key=settings.CLAUDE_API_KEY)

async def refine_with_claude_sonnet35(text: str) -> str:

    resp = client.completions.create(
        model=settings.CLAUDE_MODEL,
        prompt=(
            f"{anthropic.HUMAN_PROMPT}"
            f"너는 지금부터 유치원/초등학교 교사야. 다음 동화 문맥을 더 풍부하고 자연스럽게 다듬어줘,"
            f"유치원/초등학교한테 어려운 단어가 있으면 순화해서 주면 돼. 응답은 다른거 필요 없고 동화만 주면 돼:\n\n"
            f"{text}\n\n"
            f"{anthropic.AI_PROMPT}"
        ),
        max_tokens_to_sample=1024,
        temperature=0.7,
    )
    refined = resp.completion.strip()
    return refined
