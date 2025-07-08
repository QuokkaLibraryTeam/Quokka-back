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
    DATABASE_URL: str = Field(..., description="DB 연결 URL")

    SECRET_KEY: str = Field(..., description="JWT 시크릿 키")
    ALGORITHM: str = Field(..., description="JWT 알고리즘")
    EXPIRE_TIME: int = 60  # 분 단위

    GEMINI_MODEL: str = "gemini-2.0-flash"
    REDIS_URL: str = Field(..., description="Redis 연결 URL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # 미지정 필드 무시
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()
