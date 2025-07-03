from fastapi import APIRouter, Depends, HTTPException
from starlette import status

from core.chat_manager import new_session
from core.security import verify_token, decode_token
from main import app

router = APIRouter()

@router.post("/chat/init")
def init_chat(user_id: str = Depends(verify_token)):
    
    session_key = new_session(user_id, story_id)
    return {"session_key": session_key}

