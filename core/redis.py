from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.params import Depends
import json
from typing import Any, Set, List, Dict, Optional

# 기존 redis.py 또는 core/redis.py 파일의 내용
# --------------------------------------------------------------------------
# get_settings, rds, EXPIRE_SEC, etc. 초기 설정은 기존과 동일하다고 가정합니다.
# 이 예제에서는 설명을 위해 필요한 변수들을 직접 정의합니다.

from core.config import get_settings
import redis.asyncio as redis
import asyncio

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
    # 방이 존재하는지 확인하는 로직은 호출하는 쪽에서 처리하거나, 여기서 유지할 수 있습니다.
    # if not await rds.sismember(ROOMS_KEY, room_code):
    #     # 방이 막 닫힌 경우에도 마지막 메시지는 보내야 하므로 이 검사를 완화할 수 있습니다.
    #     print(f"Warning: Broadcasting to a potentially closed room {room_code}")
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
                raw = msg["data"]
                try:
                    obj = json.loads(raw)
                except json.JSONDecodeError:
                    obj = {"data": raw}

                # 방 닫기 메시지를 받으면 로컬의 모든 웹소켓 연결 종료
                if obj.get("type") == "close_room":
                    peers_to_close = LOCAL_PEERS.get(room_code, set()).copy()
                    for ws in peers_to_close:
                        await ws.close(code=1012, reason="Room closed by server")
                    continue # 로컬 피어 정리 후 다음 메시지 대기

                dead: Set[WebSocket] = set()
                for ws in LOCAL_PEERS.get(room_code, set()):
                    try:
                        await ws.send_json(obj)
                    except Exception:
                        dead.add(ws)
                if room_code in LOCAL_PEERS:
                    LOCAL_PEERS[room_code] -= dead
        finally:
            await pubsub.unsubscribe(f"room:{room_code}")

    LISTENERS[room_code] = asyncio.create_task(_listener())


# --- ✨ 변경된 함수 ---
def _users_key(room_code: str) -> str:
    """방의 사용자 목록을 저장하는 Redis 키"""
    return f"room:{room_code}:users"

async def connect_ws(room_code: str, ws: WebSocket, user_id: str) -> None:
    """WS 연결 수락 및 로컬/Redis Peer 등록"""
    if not await rds.sismember(ROOMS_KEY, room_code):
        await ws.close(code=1008, reason="Invalid room code")
        return

    peers = LOCAL_PEERS.setdefault(room_code, set())
    peers.add(ws)
    await rds.sadd(_users_key(room_code), user_id) # Redis에 사용자 추가
    await ensure_listener(room_code)


async def disconnect_ws(room_code: str, ws: WebSocket, user_id: str) -> None:
    """WS 연결 해제 및 로컬/Redis Peer 정리"""
    LOCAL_PEERS.get(room_code, set()).discard(ws)
    await rds.srem(_users_key(room_code), user_id) # Redis에서 사용자 제거

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


async def get_room_details(room_code: str) -> Optional[Dict[str, Any]]:
    """
    방의 상세 정보를 조회하는 서비스 로직.
    방이 없으면 None을 반환합니다.
    """
    if not await rds.sismember(ROOMS_KEY, room_code):
        return None

    users_task = rds.smembers(_users_key(room_code))
    history_task = rds.lrange(_hist(room_code), 0, -1)
    users, raw_history = await asyncio.gather(users_task, history_task)

    history: List[Dict[str, str]] = []
    for item in raw_history:
        try:
            sender, text = item.split(":", 1)
            history.append({"sender": sender, "text": text})
        except ValueError:
            history.append({"sender": "System", "text": item})

    return {
        "room_code": room_code,
        "users": list(users),
        "history": history,
    }


async def close_room_by_code(room_code: str) -> bool:
    """
    방을 닫는 서비스 로직.
    성공 시 True, 방이 없으면 False를 반환합니다.
    """
    if not await rds.sismember(ROOMS_KEY, room_code):
        return False

    await broadcast(room_code, {"type": "close_room", "text": "방이 관리자에 의해 종료되었습니다."})

    async with rds.pipeline(transaction=True) as pipe:
        pipe.srem(ROOMS_KEY, room_code)
        pipe.delete(_users_key(room_code), _hist(room_code), _meta(room_code))
        await pipe.execute()

    return True