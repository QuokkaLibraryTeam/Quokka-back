from core.config import get_settings
import redis.asyncio as redis
import asyncio
import json
from typing import Any, Set
from fastapi import HTTPException, WebSocket

settings = get_settings()
rds = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
EXPIRE_SEC = 30 * 60
ROOMS_KEY = "rooms"
LOCAL_PEERS: dict[str, Set[WebSocket]] = {}
LISTENERS: dict[str, asyncio.Task] = {}


async def create_room() -> str:
    """새 룸 코드 생성 및 Redis SET 에 저장"""
    from secrets import choice
    from string import ascii_uppercase, digits

    def _gen_code(length=6):
        alphabet = ascii_uppercase + digits
        return "".join(choice(alphabet) for _ in range(length))

    code = _gen_code()
    while await rds.sismember(ROOMS_KEY, code):
        code = _gen_code()
    await rds.sadd(ROOMS_KEY, code)
    return code


async def broadcast(room_code: str, message: Any) -> None:
    """
    해당 룸으로 JSON-serializable 객체 발행.
    message: dict, list 등 JSON으로 변환 가능한 객체
    """
    if not await rds.sismember(ROOMS_KEY, room_code):
        raise HTTPException(status_code=404, detail="Room not found")
    payload = json.dumps(message)
    await rds.publish(f"room:{room_code}", payload)


async def ensure_listener(room_code: str) -> None:
    """Redis pub/sub 리스너 스타트 (한 인스턴스당 하나만)"""
    if room_code in LISTENERS:
        return

    async def _listener():
        pubsub = rds.pubsub()
        await pubsub.subscribe(f"room:{room_code}")
        try:
            async for msg in pubsub.listen():
                if msg["type"] != "message":
                    continue
                raw = msg["data"]  # Redis에서 온 문자열
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    # JSON이 아닌 경우, 문자열 그대로 감싸서 전달
                    obj = {"data": raw}

                dead: Set[WebSocket] = set()
                for ws in LOCAL_PEERS.get(room_code, set()):
                    try:
                        await ws.send_json(obj)
                    except Exception:
                        dead.add(ws)
                LOCAL_PEERS[room_code] -= dead
        finally:
            await pubsub.unsubscribe(f"room:{room_code}")

    LISTENERS[room_code] = asyncio.create_task(_listener())


async def connect_ws(room_code: str, ws: WebSocket) -> None:
    """WS 연결 수락 및 로컬 Peer 등록"""
    if not await rds.sismember(ROOMS_KEY, room_code):
        await ws.close(code=1008, reason="Invalid room code")
        return

    await ws.accept()
    peers = LOCAL_PEERS.setdefault(room_code, set())
    peers.add(ws)
    await ensure_listener(room_code)


async def disconnect_ws(room_code: str, ws: WebSocket) -> None:
    """WS 연결 해제 처리"""
    LOCAL_PEERS.get(room_code, set()).discard(ws)
    if not LOCAL_PEERS.get(room_code):
        task = LISTENERS.pop(room_code, None)
        if task:
            task.cancel()
        LOCAL_PEERS.pop(room_code, None)


def _meta(k: str) -> str:
    return f"chat:{k}:meta"


def _hist(k: str) -> str:
    return f"chat:{k}:hist"


async def append_history(key: str, sender: str, text: str) -> None:
    prefix = "U" if sender == "U" else "AI"
    await rds.rpush(_hist(key), f"{prefix}:{text}")
    await rds.expire(_hist(key), EXPIRE_SEC)
    await rds.expire(_meta(key), EXPIRE_SEC)
