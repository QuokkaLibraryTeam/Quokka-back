# admin/setup.py
from sqladmin import Admin
from admin.backend import DummyAuth  # or just authentication_backend=None if you prefer
from admin.views.user import UserAdmin
from admin.views.story import StoryAdmin
from admin.views.report import ReportAdmin
from admin.views.scene import SceneAdmin
from core.config import get_settings

settings = get_settings()

def setup_admin(app, engine):
    admin = Admin(
        app=app,
        engine=engine,
        authentication_backend=DummyAuth(secret_key=settings.SECRET_KEY),
        base_url="/admin/dashboard"   # ← 여기를 /admin/dashboard 로 바꿉니다
    )
    admin.add_view(StoryAdmin)
    admin.add_view(ReportAdmin)
    admin.add_view(UserAdmin)
    admin.add_view(SceneAdmin)