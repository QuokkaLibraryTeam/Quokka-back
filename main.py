# app/main.py

from fastapi import FastAPI, Request
from starlette.staticfiles import StaticFiles

from api.v1.routers import router as v1_router  # 버전별 라우터
from core.config import get_settings
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import os
import models


from db.base import get_db
from db.base import Base, engine
app = FastAPI(
    title="quokkalib",
    version="1.0.1"
)

Base.metadata.create_all(bind=engine)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/illustrations",
    StaticFiles(directory="static/illustrations"),
    name="illustrations"
)

# app.mount(
#     "/admin",
#     admin_app
# )

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

@app.get(
    "/illustrations/{filename:path}",
    response_class=FileResponse,
    include_in_schema=True,
    summary="Illustration 이미지 반환",
    description="static/illustrations 폴더 내 이미지를 파일로 반환합니다."
)
async def get_illustration(filename: str):
    base = os.path.abspath("static/illustrations")
    path = os.path.abspath(os.path.join(base, filename))
    # 디렉터리 벗어남 방지
    if not path.startswith(base):
        raise HTTPException(status_code=400, detail="Invalid path")
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(path, media_type="image/*")
# 라우터 등록
app.include_router(v1_router, prefix="/api/v1")

# 루트 확인용
@app.get("/")
def root():
    return {"message": "API is alive"}

# # 비동기 초기화 (어드민 페이지)
# @app.on_evnet("startup")
# async def on_startup():
#     await create_admin()