# app/main.py

from fastapi import FastAPI
from api.v1.routers import router as v1_router  # 버전별 라우터
from core.config import settings                # 환경 설정 불러오기
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="quokkalib",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(v1_router, prefix="/api/v1")

# 루트 확인용
@app.get("/")
def root():
    return {"message": "API is alive"}
