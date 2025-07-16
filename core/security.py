from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from core.config import get_settings

settings = get_settings()

bearer_scheme = HTTPBearer(auto_error=False)

def create_access_token(subject: str,
                        expires_delta: Optional[timedelta] = None) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + (expires_delta or timedelta(minutes=settings.EXPIRE_TIME)),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str) -> str:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        return payload.get("sub") or ""
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)
) -> str:
    token = credentials.credentials  # Bearer 다음의 토큰 문자열
    return decode_token(token)

def verify_admin(user_id: str = Depends(verify_token)):
    if user_id not in settings.ADMIN_UUID:
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    
    return user_id

def optional_user_id(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Optional[str]:
    if credentials is None:
        return None
    try:
        token = credentials.credentials
        return decode_token(token)
    except Exception:
        return None