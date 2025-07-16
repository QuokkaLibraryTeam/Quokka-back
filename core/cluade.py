# core/clova_utils.py
import requests

from core.config import get_settings

settings = get_settings()

def send_clova_chat(
    text: str,
    temperature: float = 0.7,
    max_tokens: int = 1024,
    top_p: float = 0.8,
    top_k: int = 0,
    repetition_penalty: float = 1.1,
    include_ai_filters: bool = True,
    seed: int = 0,
    stop: list[str] | None = None,
) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "너는 지금부터 유치원/초등학교 교사야. "
                "다음 동화 문맥을 더 풍부하고 자연스럽게 다듬어줘, "
                "어려운 단어가 있으면 순화해서 주고, 오직 동화 본문만 출력해줘."
            )
        },
        {"role": "user", "content": text}
    ]
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json",
        "Authorization": f"Bearer {settings.NAVER_CLOVA_API_KEY}",
        "X-NCP-CLOVASTUDIO-REQUEST-ID": "234416a647264cb29bf8e3d3b68cdc22",
    }
    payload = {
        "messages": messages,
        "temperature": temperature,
        "maxTokens": max_tokens,
        "topP": top_p,
        "topK": top_k,
        "repetitionPenalty": repetition_penalty,
        "includeAiFilters": include_ai_filters,
        "seed": seed,
        "stop": stop or []
    }

    resp = requests.post("https://clovastudio.stream.ntruss.com/testapp/v3/chat-completions/HCX-005", headers=headers, json=payload)
    resp.raise_for_status()

    # API가 JSON으로 결과를 주는 경우
    try:
        data = resp.json()
        return data["result"]["message"]["content"]
    except ValueError:
        # JSON이 아닐 경우, 원문 텍스트 리턴
        return resp.text