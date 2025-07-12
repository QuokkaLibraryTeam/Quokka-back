# app/main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from core.config import get_settings
from core.security import decode_token
from db.base import Base, engine, get_db
from admin.setup import setup_admin
from admin.views.auth import router as auth_router
from api.v1.routers import router as v1_router
import os

from core.config import get_settings

settings = get_settings()

from db.base import get_db
from db.base import Base, engine
app = FastAPI(
    title="quokkalib",
    version="1.0.1"
)

# DB 초기화
Base.metadata.create_all(bind=engine)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1) SQLAdmin UI (prefix=/admin/dashboard)
setup_admin(app, engine)

# 2) 커스텀 로그인 라우터 (/admin/login)
app.include_router(auth_router)

# 3) Illustration 정적 파일
app.mount("/illustrations", StaticFiles(directory="static/illustrations"), name="illustrations")

# 4) DB 세션 미들웨어
@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    gen = get_db(); db = next(gen)
    try:
        request.state.db = db
        return await call_next(request)
    finally:
        gen.close()

# 5) /admin/* 보호 미들웨어
@app.middleware("http")
async def admin_auth_middleware(request: Request, call_next):
    path = request.url.path

    # 로그인 폼(/admin/login) 예외
    # SQLAdmin UI는 /admin/dashboard 이하로 동작하니 그것도 예외로 둡니다
    if path.startswith("/admin") and not (
        path == "/admin/login" or path.startswith("/admin/dashboard")
    ):
        token = request.cookies.get("access_token")
        if not token:
            return RedirectResponse("/admin/login")
        try:
            user = decode_token(token)
            if user != settings.ADMIN_USERNAME:
                return RedirectResponse("/admin/login")
        except:
            return RedirectResponse("/admin/login")

    return await call_next(request)

# 6) Illustration 파일 제공
@app.get("/illustrations/{filename:path}", response_class=FileResponse)
async def get_illustration(filename: str):
    base = os.path.abspath("static/illustrations")
    path = os.path.abspath(os.path.join(base, filename))
    if not path.startswith(base) or not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path)

# 7) API v1
app.include_router(v1_router, prefix="/api/v1")

@app.get("/")
def root():
    return {"message": "API is alive"}
