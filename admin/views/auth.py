# admin/views/auth.py
from fastapi import APIRouter, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from core.config import get_settings
from core.security import create_access_token

settings = get_settings()
router = APIRouter()

@router.get("/admin/login", response_class=HTMLResponse)
async def login_form():
    return HTMLResponse("""
    <html><body>
      <h2>관리자 로그인</h2>
      <form method="post" action="/admin/login">
        <input name="username" placeholder="Username"/><br/>
        <input name="password" type="password" placeholder="Password"/><br/>
        <button type="submit">Login</button>
      </form>
    </body></html>
    """)

@router.post("/admin/login")
async def login(username: str = Form(...), password: str = Form(...)):
    if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
        token = create_access_token(subject=username)
        resp = RedirectResponse("/admin/dashboard", status_code=303)
        resp.set_cookie("access_token", token, httponly=True, samesite="lax", secure=False, path="/")
        return resp
    return HTMLResponse("Unauthorized", status_code=401)
