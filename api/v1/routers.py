from fastapi import APIRouter

router = APIRouter()

# 각각의 endpoint 라우터를 prefix 포함해 등록
# api_router.include_router(user.router, prefix="/users", tags=["Users"])
