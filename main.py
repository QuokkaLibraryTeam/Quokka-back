# app/main.py

from fastapi import FastAPI, Request
from api.v1.routers import router as v1_router  # 버전별 라우터
from core.config import get_settings
from fastapi.middleware.cors import CORSMiddleware

from db.base import get_db

app = FastAPI(
    title="quokkalib",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    gen = get_db()
    db = next(gen)
    try:
        request.state.db = db
        response = await call_next(request)
    finally:
        gen.close()
    return response

# 라우터 등록
app.include_router(v1_router, prefix="/api/v1")

# 루트 확인용
@app.get("/")
def root():
    return {"message": "API is alive"}
