from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    PROJECT_NAME: str = "quokkalib"
    DEBUG: bool = True
    ALLOWED_ORIGINS: List[str] = Field(
        default_factory=lambda: ["*"],
        description="허용할 CORS origins"
    )

    GEMINI_API_KEY: str = Field(..., description="Gemini API 키")
    NAVER_CLOVA_API_KEY: str = Field(..., description="클로바 API 키")
    DATABASE_URL: str = Field(..., description="DB 연결 URL")

    SECRET_KEY: str = Field(..., description="JWT 시크릿 키")
    ALGORITHM: str = Field(..., description="JWT 알고리즘")
    EXPIRE_TIME: int = 60  # 분 단위

    GEMINI_MODEL: str = "gemini-2.0-flash"
    NAVER_CLOVA_API_URL: str = Field(..., description="클로바 API url")
    REDIS_URL: str = Field(..., description="Redis 연결 URL")

    # OAuth 관련
    GOOGLE_CLIENT_ID: str = Field(..., description="OAuth google 클라이언트")
    GOOGLE_CLIENT_SECRET: str = Field(..., description="OAuth 비밀키")
    REDIRECT_URL: str = Field(..., description="OAuth 리다이렉트 URL")
    GOOGLE_AUTH_ENDPOINT: str = Field(..., description="OAuth 엔드포인트")
    GOOGLE_USERINFO_ENDPOINT: str = Field(..., description="OAuth 유저 엔드포인트")
    GOOGLE_TOKEN_ENDPOINT: str = Field(..., description="OAuth callback 핸들러 code to access_token")

    # 관리자
    ADMIN_USERNAME: str = Field(..., description="관리자 ID")
    ADMIN_PASSWORD: str = Field(..., description="관리자 PW")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # 미지정 필드 무시
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()
