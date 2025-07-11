from pydantic import BaseModel, Field


class AuthResponse(BaseModel):
    access_token: str = Field(..., description="엑세스 토큰")
    token_type: str = Field(..., description="토큰 타입")
    user_id: str = Field(None, description="유저 아이디")
    nickname : str = Field(None, description="닉네임")

