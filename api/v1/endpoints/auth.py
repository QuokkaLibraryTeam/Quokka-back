from datetime import timedelta, datetime
import requests

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from sqlalchemy.orm import Session

from urllib.parse import urlencode

from core.security import create_access_token
from core.config import get_settings

from models.user import User
from db.base import get_db

router = APIRouter()
settings = get_settings()

class Token(BaseModel):
    access_token: str
    token_type: str

# @@ 현재 엔트포인트 :: localhost:8000/api/v1/auth/token

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    token = create_access_token(form_data.username, expires_delta=timedelta(minutes=10))
    return {"access_token": token, "token_type": "bearer"}

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
    # 1. code → access_token 교환
    token_res = requests.post(settings.GOOGLE_TOKEN_ENDPOINT, data={
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.REDIRECT_URL,
        "grant_type": "authorization_code",
    })
    print("🔴 token_res.status_code:", token_res.status_code)
    print("🔴 token_res.json():", token_res.json())

    if not token_res.ok:
        raise HTTPException(status_code=400, detail="토큰 요청 실패")

    access_token = token_res.json().get("access_token")

    # 2. access_token으로 사용자 정보 요청
    userinfo_res = requests.get(settings.GOOGLE_USERINFO_ENDPOINT, headers={
        "Authorization": f"Bearer {access_token}"
    })

    if not userinfo_res.ok:
        raise HTTPException(status_code=400, detail="사용자 정보 요청 실패")

    userinfo = userinfo_res.json()
    google_id = userinfo["id"]

    # 3. DB에 사용자 저장 또는 조회
    user = db.query(User).filter_by(google_id=google_id).first()
    if not user:
        user = User(
            google_id=google_id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_access_token(subject=str(user.id))

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": str(user.id),
    }