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
    <!DOCTYPE html>
    <html lang="ko">
    <head>
      <meta charset="UTF-8" />
      <title>관리자 로그인</title>
      <style>
        /* 전역 box-sizing */
        html, body {
          width: 100%;
          height: 100%;
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }
        *, *::before, *::after {
          box-sizing: inherit;
        }

        /* 화면 전체 중앙 정렬 컨테이너 */
        .container {
          display: flex;
          justify-content: center;
          align-items: center;
          width: 100%;
          height: 100vh;
          background: #f5f7fa;
        }

        /* 로그인 카드 */
        .login-card {
          width: 360px;
          max-width: 90%;
          margin: 0 auto;
          padding: 2rem;
          background: #ffffff;
          border-radius: 8px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .login-card h2 {
          margin: 0 0 1.5rem;
          text-align: center;
          color: #333;
        }

        /* 입력창·버튼 */
        .login-card input,
        .login-card button {
          width: 100%;
          padding: 0.75rem;
          margin: 0.5rem 0;
          font-size: 1rem;
          border-radius: 4px;
          border: 1px solid #ccd0d5;
        }
        .login-card button {
          background: #4a90e2;
          border: none;
          color: #fff;
          cursor: pointer;
          transition: background 0.2s ease;
        }
        .login-card button:hover {
          background: #357ab8;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="login-card">
          <h2>관리자 로그인</h2>
          <form method="post" action="/admin/login">
            <input name="username" type="text" placeholder="Username" required />
            <input name="password" type="password" placeholder="Password" required />
            <button type="submit">Login</button>
          </form>
        </div>
      </div>
    </body>
    </html>
    """)

@router.post("/admin/login")
async def login(username: str = Form(...), password: str = Form(...)):
    if username == settings.ADMIN_USERNAME and password == settings.ADMIN_PASSWORD:
        token = create_access_token(subject=username)
        resp = RedirectResponse("/admin/dashboard", status_code=303)
        resp.set_cookie("access_token", token, httponly=True, samesite="lax", secure=False, path="/")
        return resp
    return HTMLResponse("Unauthorized", status_code=401)
