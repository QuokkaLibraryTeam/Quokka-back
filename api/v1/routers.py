from fastapi import APIRouter

from api.v1.endpoints import websockets, users, auth, rooms, stories, shares, reports

router = APIRouter()

# 각각의 endpoint 라우터를 prefix 포함해 등록
# router.include_router(user.router, prefix="/users", tags=["Users"])

router.include_router(websockets.router,prefix="/ws",tags=["ws"])
router.include_router(users.router,prefix="/users",tags=["users"])
router.include_router(stories.router, prefix="/stories")
router.include_router(auth.router,prefix="/auth",tags=["auth"])
router.include_router(rooms.router,prefix="/rooms",tags=["rooms"])
router.include_router(shares.router,prefix="/shares")
router.include_router(reports.router,prefix="/reports",tags=["reports"])