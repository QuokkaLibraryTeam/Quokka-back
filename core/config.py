from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "quokkalib"
    DEBUG: bool = True
    GEMINI_API_KEY: str
    DATABASE_URL: str = "sqlite:///./database.db"

    SECRET_KEY :str = "your_secret_key"
    ALGORITHM :str = "HS256"
    EXPIRE_TIME : int = 30                          # 분 단위

    GEMINI_MODEL: str = "gemini-2.0-flash"

    class Config:
        env_file = ".env"  # .env 파일에서 값 불러오기

@lru_cache
def get_settings() -> Settings:
    return Settings()
