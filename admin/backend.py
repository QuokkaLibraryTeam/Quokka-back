from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse

from core.config import get_settings
from core.security import create_access_token, decode_token

settings = get_settings()

class AdminSimpleAuth(AuthenticationBackend):
    def __init__(self, secret_key: str):
        super().__init__(secret_key=secret_key)

    async def login(self, request: Request):
        # GET: 로그인 폼
        if request.method == "GET":
            return HTMLResponse("""
<html>
<head><title>Admin Login</title></head>
<body>
  <h2>관리자 로그인</h2>
  <form action="/admin/login" method="post">
    <label>Username: <input name="username" /></label><br/>
    <label>Password: <input name="password" type="password" /></label><br/>
    <button type="submit">Login</button>
  </form>
</body>
</html>
""")

        # POST: 자격 증명 검사 후, HTML 메타 리다이렉트
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
            token = create_access_token(subject=username)
            print(f"[DEBUG] login success: issuing token={token}")

            # 쿠키 세팅 + 메타 리프레시로 안전하게 리다이렉트
            response = HTMLResponse("""
<html>
<head>
  <meta http-equiv="refresh" content="0;url=/admin" />
</head>
<body></body>
</html>
""")
            response.set_cookie(
                key="access_token",
                value=token,
                httponly=True,
                path="/",
                max_age=60 * 60 * 2,
                samesite="lax",
                secure=False
            )
            return response

        # 로그인 실패 시 다시 폼으로
        print(f"[DEBUG] login failed for username={username}")
        return RedirectResponse(url="/admin/login", status_code=303)

    async def logout(self, request: Request):
        print("[DEBUG] logging out, deleting cookie")
        response = RedirectResponse(url="/admin/login", status_code=303)
        response.delete_cookie("access_token", path="/")
        return response

    async def authenticate(self, request: Request) -> bool:
        token = request.cookies.get("access_token")
        print(f"[DEBUG] authenticate: token from cookie={token!r}")
        if not token:
            return False
        try:
            user = decode_token(token)
            valid = user == settings.ADMIN_USERNAME
            print(f"[DEBUG] authenticate: decoded user={user!r}, valid={valid}")
            return valid
        except Exception as e:
            print(f"[DEBUG] authenticate: decode error={e}")
            return False

from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import Response

# admin/backend.py

from sqladmin.authentication import AuthenticationBackend
from starlette.requests import Request
from starlette.responses import RedirectResponse

class DummyAuth(AuthenticationBackend):
    def __init__(self, secret_key: str):
        super().__init__(secret_key=secret_key)

    async def login(self, request: Request):
        return Response(status_code=404)

    async def logout(self, request: Request):
        # 쿠키 삭제 후 /admin/login 으로 보내줍니다
        response = RedirectResponse(url="/admin/login", status_code=303)
        response.delete_cookie("access_token", path="/")
        return response

    async def authenticate(self, request: Request) -> bool:
        return True
