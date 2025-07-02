from fastapi import APIRouter

from api.v1.endpoints import websockets

router = APIRouter()

# 각각의 endpoint 라우터를 prefix 포함해 등록
# router.include_router(user.router, prefix="/users", tags=["Users"])

router.include_router(websockets.router,prefix="/ws",tags=["ws"])