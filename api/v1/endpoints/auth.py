from datetime import datetime
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import RedirectResponse

from core.config import get_settings
from core.security import create_access_token, verify_token
from db.base import get_db
from models.user import User

router = APIRouter()
settings = get_settings()

@router.get("/login")
async def login():
    query = urlencode({
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.REDIRECT_URL,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/userinfo.profile",
        "access_type": "offline",
        "prompt": "consent",
    })
        
    return {"auth_url": f"{settings.GOOGLE_AUTH_ENDPOINT}?{query}"}

@router.get("/callback")
def callback(code: str, db: Session = Depends(get_db)):
    # [1] code to access_token 교환
    token_res = requests.post(settings.GOOGLE_TOKEN_ENDPOINT, data={
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.REDIRECT_URL,
        "grant_type": "authorization_code",
    })

    if not token_res.ok:
        raise HTTPException(status_code=400, detail="토큰 요청 실패")

    access_token = token_res.json().get("access_token")

    # [2] access_token으로 사용자 정보 요청
    userinfo_res = requests.get(settings.GOOGLE_USERINFO_ENDPOINT, headers={
        "Authorization": f"Bearer {access_token}"
    })

    if not userinfo_res.ok:
        raise HTTPException(status_code=400, detail="사용자 정보 요청 실패")

    userinfo = userinfo_res.json()
    google_id = userinfo["id"]
    nickname = userinfo.get("name")  # 구글 프로필 상의 닉네임을 그대로 가져옴

    # 3. DB에 사용자 저장 또는 조회
    user = db.query(User).filter_by(google_id=google_id).first()
    if not user:
        user = User(
            google_id=google_id,
            nickname=nickname,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(subject=str(user.id))
    print(access_token)
    frontend_callback_url = f"http://localhost:3000/auth/callback?access_token={access_token}&nickname={nickname}"

    return RedirectResponse(url=frontend_callback_url)

# 토큰 유효성 검사 (현재 로그인한 사용자 정보 조회)
@router.get("/me")
async def me(
    user_id: str = Depends(verify_token),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "user_id": user.id,
        "google_id": user.google_id,
        "created_at": user.created_at.isoformat(),
    }