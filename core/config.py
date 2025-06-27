from pydantic import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "quokkalib"
    DEBUG: bool = True
    GEMINI_API_KEY: str
    DATABASE_URL: str = "sqlite:///./test.db"

    class Config:
        env_file = ".env"  # .env 파일에서 값 불러오기


settings = Settings()  # 전역 설정 객체
