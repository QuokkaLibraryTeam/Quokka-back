from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "quokkalib"
    DEBUG: bool = True
    GEMINI_API_KEY: str
    DATABASE_URL: str

    SECRET_KEY :str
    ALGORITHM :str
    EXPIRE_TIME : int = 30                          # 분 단위

    GEMINI_MODEL: str = "gemini-2.0-flash"

    class Config:
        env_file = ".env"

@lru_cache
def get_settings() -> Settings:
    return Settings()
