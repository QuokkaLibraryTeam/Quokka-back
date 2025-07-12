from fastapi_admin.app import app as admin_app
from fastapi_admin.resources import Field, Model
from fastapi_admin.providers.login import UsernamePasswordProvider, Provider, AuthException

from starlette.requests import Request
from starlette.middleware.authentication import AuthenticationMiddleware
from starlette.authentication import requires, AuthCredentials, SimpleUser
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.future import select

from models.user import User
from models.story import Story
from models.comment import Comment
from models.like import Like
from models.report import Report
from db.base import get_async_session

from fastapi_admin.widgets import displays, inputs
from fastapi_admin.resources import Link

from core.config import get_settings
from core.security import decode_token

settings = get_settings()

# 예시 비동기 DB 세션 (필요시 수정)
engine = create_async_engine(settings.DATABASE_URL, future=True)
session_maker = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def create_admin():
    await admin_app.configure(
        logo_url="https://fastapi-admin.github.io/img/logo.svg",
        template_folders=[],
        database=engine,
        admin_model=User,
        session_maker=session_maker,
        login_provider=JWTLoginProvider(admin_model=User), # 커스텀으로 변경함 (OAuth2 사용)
        resources=[
            Model(User),
            Model(Story, fields=[
                "id",
                "title",
                Field(name="like_count", label="Likes", display=displays.Text(), getter=lambda obj: len(obj.likes)),
                Field(name="comment_count", label="Comments", display=displays.Text(), getter=lambda obj: len(obj.comments)),
            ]),
            Model(Comment),
            Model(Like),
            Model(Report),
        ]
    )

# OAuth2를 이용한 커스텀 LoginProvider (이거 없으면 유저 테이블 다 바꿔야함)
class JWTLoginProvider(Provider):
    async def login(self, request: Request) -> User:
        form = await request.form()
        jwt_token = form.get("password")  # 비밀번호 필드에 JWT token을 대신 입력
        try:
            user_id = decode_token(jwt_token)
        except:
            raise AuthException("유효한 토큰이 아닙니다.")

        async with get_async_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

        if not user:
            raise AuthException("사용자를 찾을 수 없습니다.")

        if str(user.id) not in settings.ADMIN_UUID:
            raise AuthException("관리자가 아닙니다.")

        return user